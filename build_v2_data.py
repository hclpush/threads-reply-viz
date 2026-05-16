# -*- coding: utf-8 -*-
"""
Builds data-v2/replies.json and data-v2/chart_data.json by:
1. Merging existing 683 replies with 472 new classified replies
2. Updating like counts for existing replies (likes only, NO category changes)
3. Applying existing category-overrides.json to ALL replies
4. Rebuilding chart_data.json

Run: python3 build_v2_data.py
"""
import json, os, shutil
from collections import defaultdict

BASE     = os.path.dirname(os.path.abspath(__file__))
DATA_V1  = os.path.join(BASE, 'data')
DATA_V2  = os.path.join(BASE, 'data-v2')

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
    os.makedirs(DATA_V2, exist_ok=True)

    # Load existing data (v1)
    v1           = load(os.path.join(DATA_V1, 'replies.json'))
    old_replies  = v1['replies']          # list of dicts
    source_post  = v1.get('sourcePost', '')
    print(f"Loaded {len(old_replies)} existing replies.")

    # Load scraped data (like count updates for old, new replies)
    raw_scraped  = load(os.path.join(DATA_V2, 'raw-scraped.json'))
    updated_likes = raw_scraped.get('updatedLikes', {})  # url -> {likes, likesNum}
    print(f"Like count updates for existing: {len(updated_likes)}")

    # Load new classified replies
    new_replies  = load(os.path.join(DATA_V2, 'classified-new-replies.json'))
    print(f"New replies to add: {len(new_replies)}")

    # Load overrides (v1 overrides still apply to all)
    overrides    = load(os.path.join(DATA_V1, 'category-overrides.json'))
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

    # ── Step 2: Merge old + new ───────────────────────────────────────────────
    # Deduplicate by URL (old replies take precedence for category/subcategory)
    merged_by_url = {}
    for r in old_replies:
        merged_by_url[r['url']] = r
    for r in new_replies:
        url = r['url']
        if url not in merged_by_url:
            merged_by_url[url] = r

    merged = list(merged_by_url.values())
    print(f"Merged total: {len(merged)} replies (was {len(old_replies)}, added {len(merged) - len(old_replies)})")

    # ── Step 3: Save replies.json v2 ─────────────────────────────────────────
    v2_replies_path = os.path.join(DATA_V2, 'replies.json')
    v2_replies = {
        "replies":    merged,
        "categories": list(CAT_COLORS.keys()),
        "total":      len(merged),
        "sourcePost": source_post,
    }
    save(v2_replies_path, v2_replies)

    # ── Step 4: Copy overrides, rebuild chart_data ────────────────────────────
    shutil.copy2(
        os.path.join(DATA_V1, 'category-overrides.json'),
        os.path.join(DATA_V2, 'category-overrides.json'),
    )
    shutil.copy2(
        os.path.join(DATA_V1, 'category-map.json'),
        os.path.join(DATA_V2, 'category-map.json'),
    )
    print("Copied overrides + category-map to data-v2/")

    # Apply overrides in-place when building chart_data
    # (overrides mutate r['category'] / r['subcategory'] for chart only)
    import copy
    merged_for_chart = copy.deepcopy(merged)
    chart_data = rebuild_chart_data(merged_for_chart, source_post, overrides)

    # Save chart_data.json
    chart_path = os.path.join(DATA_V2, 'chart_data.json')
    save(chart_path, chart_data)

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\nv2 Category breakdown (by likes):")
    cat_stats = chart_data['catStats']
    for cat in chart_data['catLabels']:
        s = cat_stats[cat]
        print(f"  {s['totalLikes']:8,}L  {s['count']:4}x  {cat}")
        for sub, ss in sorted(s['subcategories'].items(), key=lambda x: -x[1]['totalLikes']):
            print(f"    {ss['totalLikes']:8,}L  {ss['count']:4}x    ↳ {sub}")


if __name__ == '__main__':
    main()
