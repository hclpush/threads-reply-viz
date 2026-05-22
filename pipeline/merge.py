# -*- coding: utf-8 -*-
"""
Merges the latest classified batch into the live dataset:
1. Snapshots current data/replies.json to data/.backup/ before any write
2. Updates like counts for existing replies from staging/raw-scraped.json (likes only)
3. Appends new classified replies from staging/classified-batch.json
4. Applies data/category-overrides.json to ALL replies
5. Rebuilds data/chart_data.json

Run: python3 pipeline/merge.py
"""
import json, os
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT    = Path(__file__).resolve().parent.parent
DATA    = ROOT / 'data'
STAGING = DATA / 'staging'
BACKUP  = DATA / '.backup'

# ── Category color map ────────────────────────────────────────────────────────
CAT_COLORS = {
    "口誤":             "#ff6b6b",
    "當眾出糗":         "#e84393",
    "回覆原 PO":        "#a29bfe",
    "其他":             "#666666",
    "以為沒人亂講話":   "#6ab04c",
    "認錯人":           "#ff9f43",
    "被工作/兵役制約":  "#4bcffa",
    "以為在跟自己說話": "#c44569",
    "走錯空間":         "#34e7e4",
    "叫錯":             "#ffd32a",
}

def load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def save(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved → {path}")


def rebuild_chart_data(replies, source_post, overrides):
    cat_likes  = defaultdict(int)
    cat_count  = defaultdict(int)
    sub_likes  = defaultdict(lambda: defaultdict(int))
    sub_count  = defaultdict(lambda: defaultdict(int))

    for r in replies:
        # Apply overrides
        url = r.get('url', '')
        if url in overrides:
            r['category']    = overrides[url]['category']
            r['subcategory'] = overrides[url].get('subcategory')

        cat = r['category']
        sub = r.get('subcategory')
        lk  = r.get('likesNum', 0) or 0
        cat_likes[cat] += lk
        cat_count[cat] += 1
        if sub:
            sub_likes[cat][sub] += lk
            sub_count[cat][sub] += 1

    cat_order  = sorted(cat_likes.keys(), key=lambda c: -cat_likes[c])
    cat_colors = [CAT_COLORS.get(c, "#999999") for c in cat_order]
    alpha_colors = [c + "99" for c in cat_colors]

    cat_stats = {}
    for cat in cat_order:
        subs = {}
        for sub, lk in sub_likes[cat].items():
            subs[sub] = {"count": sub_count[cat][sub], "totalLikes": lk}
        cat_stats[cat] = {
            "count": cat_count[cat],
            "totalLikes": cat_likes[cat],
            "subcategories": subs,
        }

    idx = {c: i for i, c in enumerate(cat_order)}
    n   = len(cat_order)
    datasets = [{"label": "__main__", "data": [cat_likes[c] for c in cat_order], "colors": cat_colors}]

    all_subs = []
    for cat in cat_order:
        for sub in sub_likes[cat]:
            all_subs.append((sub, cat, sub_likes[cat][sub]))
    all_subs.sort(key=lambda x: -x[2])
    for sub, cat, lk in all_subs:
        row = [0] * n
        row[idx[cat]] = lk
        datasets.append({"label": sub, "data": row, "colors": alpha_colors})

    compact = []
    for r in replies:
        row = {
            "a":  r["author"],
            "t":  r["text"],
            "l":  r.get("likesNum", 0),
            "ls": r.get("likes", "0"),
            "u":  r["url"],
            "c":  r["category"],
            "s":  r.get("subcategory"),
        }
        if "intl" in r:
            row["i"] = bool(r["intl"])
        if r.get("text_en"):
            row["te"] = r["text_en"]
        compact.append(row)

    return {
        "sourcePost":  source_post,
        "total":       len(replies),
        "catLabels":   cat_order,
        "catColors":   cat_colors,
        "catStats":    cat_stats,
        "datasets":    datasets,
        "replies":     compact,
    }


def main():
    replies_path  = DATA / 'replies.json'
    chart_path    = DATA / 'chart_data.json'

    # Snapshot current dataset before any write — merge.py reads and writes the same file
    if replies_path.exists():
        BACKUP.mkdir(exist_ok=True)
        stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        backup_path = BACKUP / f'replies.{stamp}.json'
        backup_path.write_bytes(replies_path.read_bytes())
        print(f"Backed up current dataset → {backup_path}")

    # Load current live dataset
    current      = load(replies_path)
    old_replies  = current['replies']
    source_post  = current.get('sourcePost', '')
    print(f"Loaded {len(old_replies)} existing replies.")

    # Load latest scrape (like-count updates for existing rows)
    raw_scraped  = load(STAGING / 'raw-scraped.json')
    updated_likes = raw_scraped.get('updatedLikes', {})
    print(f"Like count updates for existing: {len(updated_likes)}")

    # Load latest classified batch
    new_replies  = load(STAGING / 'classified-batch.json')
    print(f"New replies to add: {len(new_replies)}")

    # Load overrides
    overrides    = load(DATA / 'category-overrides.json')
    print(f"Overrides loaded: {len(overrides)} entries")

    # ── Step 1: Update like counts in existing replies (categories unchanged) ──
    likes_updated = 0
    for r in old_replies:
        url = r.get('url', '')
        if url in updated_likes:
            upd = updated_likes[url]
            r['likes']    = upd['likes']
            r['likesNum'] = upd['likesNum']
            likes_updated += 1
    print(f"Updated likes for {likes_updated} existing replies.")

    # ── Step 2: Merge old + new (dedup by URL; existing rows win) ─────────────
    merged_by_url = {}
    for r in old_replies:
        merged_by_url[r['url']] = r
    for r in new_replies:
        url = r['url']
        if url not in merged_by_url:
            merged_by_url[url] = r

    merged = list(merged_by_url.values())
    print(f"Merged total: {len(merged)} replies (was {len(old_replies)}, added {len(merged) - len(old_replies)})")

    # ── Step 3: Write merged dataset back to data/replies.json ────────────────
    save(replies_path, {
        "replies":    merged,
        "categories": list(CAT_COLORS.keys()),
        "total":      len(merged),
        "sourcePost": source_post,
    })

    # ── Step 4: Rebuild chart_data with overrides applied ─────────────────────
    import copy
    merged_for_chart = copy.deepcopy(merged)
    chart_data = rebuild_chart_data(merged_for_chart, source_post, overrides)
    save(chart_path, chart_data)

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\nCategory breakdown (by likes):")
    cat_stats = chart_data['catStats']
    for cat in chart_data['catLabels']:
        s = cat_stats[cat]
        print(f"  {s['totalLikes']:8,}L  {s['count']:4}x  {cat}")
        for sub, ss in sorted(s['subcategories'].items(), key=lambda x: -x[1]['totalLikes']):
            print(f"    {ss['totalLikes']:8,}L  {ss['count']:4}x    ↳ {sub}")


if __name__ == '__main__':
    main()
