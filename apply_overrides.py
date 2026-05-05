# -*- coding: utf-8 -*-
"""
1. Applies category-overrides.json to replies.json
2. Renames legacy categories/subcats to v2 names
3. Rebuilds chart_data.json from scratch
"""
import json, os
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))

# ── Category color map (preserved where possible) ────────────────────────────
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

# ── Legacy renames applied to all replies (not just 其他) ─────────────────────
CAT_RENAME = {
    "點餐/購物口誤": "口誤",
    "走錯店/進錯車": "走錯空間",
}
SUB_RENAME = {
    "奶頭": "乳頭/奶頭",
}
# Legacy 點餐/購物口誤 with no subcat → assign 點餐/購物
PROMOTE_SUB = {
    "口誤": "點餐/購物",   # only applied when subcat is None and old cat was 點餐/購物口誤
}


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved → {path}")


def apply_and_rebuild():
    replies_path    = os.path.join(BASE, "data/replies.json")
    overrides_path  = os.path.join(BASE, "data/category-overrides.json")
    chart_path      = os.path.join(BASE, "data/chart_data.json")

    replies_data = load(replies_path)
    overrides    = load(overrides_path)
    chart_data   = load(chart_path)

    replies = replies_data["replies"]
    changed = 0

    for r in replies:
        url = r["url"]
        old_cat = r["category"]
        old_sub = r.get("subcategory")

        # 1. Apply override for 其他 items
        if url in overrides:
            r["category"]    = overrides[url]["category"]
            r["subcategory"] = overrides[url]["subcategory"]
            changed += 1
            continue

        # 2. Rename legacy categories
        if old_cat in CAT_RENAME:
            new_cat = CAT_RENAME[old_cat]
            r["category"] = new_cat
            # Promote null subcat to 點餐/購物 for former 點餐/購物口誤 items
            if old_cat == "點餐/購物口誤" and old_sub is None:
                r["subcategory"] = "點餐/購物"
            elif old_sub in SUB_RENAME:
                r["subcategory"] = SUB_RENAME[old_sub]
            changed += 1

    print(f"Updated {changed} replies")
    save(replies_path, replies_data)

    # ── Rebuild chart_data ────────────────────────────────────────────────────
    # Compute stats from updated replies
    cat_likes   = defaultdict(int)
    cat_count   = defaultdict(int)
    sub_likes   = defaultdict(lambda: defaultdict(int))
    sub_count   = defaultdict(lambda: defaultdict(int))

    for r in replies:
        cat = r["category"]
        sub = r.get("subcategory")
        lk  = r.get("likesNum", 0) or 0
        cat_likes[cat] += lk
        cat_count[cat] += 1
        if sub:
            sub_likes[cat][sub] += lk
            sub_count[cat][sub] += 1

    # Order categories by total likes desc
    cat_order = sorted(cat_likes.keys(), key=lambda c: -cat_likes[c])
    cat_labels = cat_order
    cat_colors = [CAT_COLORS.get(c, "#999999") for c in cat_order]

    # catStats
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

    # datasets — main + one per subcat
    idx = {c: i for i, c in enumerate(cat_order)}
    n   = len(cat_order)
    alpha_colors = [c + "99" for c in cat_colors]

    datasets = [{
        "label":  "__main__",
        "data":   [cat_likes[c] for c in cat_order],
        "colors": cat_colors,
    }]
    # Collect all subcats
    all_subs = []
    for cat in cat_order:
        for sub in sub_likes[cat]:
            all_subs.append((sub, cat, sub_likes[cat][sub]))
    # Sort by likes desc
    all_subs.sort(key=lambda x: -x[2])
    for sub, cat, lk in all_subs:
        row = [0] * n
        row[idx[cat]] = lk
        datasets.append({
            "label":  sub,
            "data":   row,
            "colors": alpha_colors,
        })

    # Rebuild compact replies list (keep same key scheme)
    compact_replies = []
    for r in replies:
        compact_replies.append({
            "a":  r["author"],
            "t":  r["text"],
            "l":  r.get("likesNum", 0),
            "ls": r.get("likes", "0"),
            "u":  r["url"],
            "c":  r["category"],
            "s":  r.get("subcategory"),
        })

    chart_data["catLabels"]  = cat_labels
    chart_data["catColors"]  = cat_colors
    chart_data["catStats"]   = cat_stats
    chart_data["datasets"]   = datasets
    chart_data["replies"]    = compact_replies
    chart_data["total"]      = len(replies)

    save(chart_path, chart_data)

    # Summary
    print(f"\nNew category breakdown (by likes):")
    for cat in cat_order:
        print(f"  {cat_likes[cat]:7,}L  {cat_count[cat]:4}x  {cat}")
        for sub, lk in sorted(sub_likes[cat].items(), key=lambda x: -x[1]):
            print(f"    {lk:7,}L  {sub_count[cat][sub]:4}x    ↳ {sub}")


if __name__ == "__main__":
    apply_and_rebuild()
