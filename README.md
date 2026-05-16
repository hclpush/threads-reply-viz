# 社死大調查 · Cringe Moments Survey

An interactive analysis of replies to a viral Threads post asking people to share their most embarrassing public moments.

**Source post:** [@betabreakhsin](https://www.threads.com/@betabreakhsin/post/DXzS3YEEY8t) — "大家人生中社死現場第一名是什麼？"

## Features

- **Stacked bar chart** — categories sorted by total likes or reply count, with graded subcategory breakdown
- **Toggle** between likes view and reply count view
- **Sidebar filters** — categories ranked by count; click any category or subcategory to filter the table
- **Search** — filter by reply text or author handle
- **EN / 中 toggle** — full bilingual UI
- **Direct links** — every reply row links to the original Threads reply and Google Translate

## How to use

Open `index.html` in any modern browser — no server needed, fully self-contained.

## Categories

| Category | EN | Subcategories |
|---|---|---|
| 口誤 | Slip of the Tongue | 點餐/購物 · 職場口誤 · 腦袋當機 · 語言混亂 · 乳頭/奶頭 |
| 被工作/兵役制約 | Conditioned by Work/Military | 一起說歡迎光臨 · 當完兵喊「有！」|
| 認錯人 | Mistook Someone | 有肢體接觸 · 沒有肢體接觸 |
| 當眾出糗 | Public Embarrassment | 工作中 · 童言無忌 · 學狗叫 · 語言不通 |
| 以為在跟自己說話 | Thought Someone Talked to Me | 以為店員在跟自己說話 · 領錯獎/誤以為得獎 |
| 以為沒人亂講話 | Talked Freely, Got Caught | — |
| 走錯空間 | Walked into Wrong Place | — |
| 叫錯 | Called Wrong Name | 叫老師媽媽 |
| 回覆原 PO | Reply to OP | 好好笑 · 好好笑長出腹肌 · 留 X 看 · 你好可愛 |
| 其他 | Others | — |

## Data snapshots

| Version | Replies | Scraped | Notes |
|---|---|---|---|
| v1 | 683 | 2026-05-03 | Top-engagement replies only; likes reflect that moment |
| v2 | 1,155 | 2026-05-15 | Added 472 new replies; refreshed like counts for 250 existing replies |

## File structure

```
data/                         # v1 — original snapshot (do not modify)
  replies.json                  # 683 replies, full fields
  chart_data.json               # compact format for dashboard
  category-map.json             # taxonomy reference
  category-overrides.json       # URL → {category, subcategory} manual overrides

data-v2/                      # v2 — current dataset
  replies.json                  # 1,155 replies (v1 + new), merged
  chart_data.json               # compact format for dashboard
  category-map.json             # taxonomy reference (copy of v1)
  category-overrides.json       # overrides (copy of v1; extend here for new replies)

scripts/
  scrape_new_replies.js         # Playwright scraper — intercepts GraphQL to extract replies + likes
  package.json                  # playwright dependency

generate_overrides.py           # hardcoded OVERRIDES dict → data/category-overrides.json
apply_overrides.py              # applies overrides to replies.json, rebuilds chart_data.json
classify_new_replies.py         # keyword classifier for newly scraped replies
build_v2_data.py                # merges v1 + new replies, updates likes, rebuilds data-v2/
build.py                        # bakes chart_data.json + i18n into index.html
```

## Updating with new replies (v3+)

```bash
# 1. Scrape — requires Playwright Chromium and active Threads login in browser profile
node scripts/scrape_new_replies.js
# → writes data-v2/raw-scraped.json

# 2. Classify new replies
python3 classify_new_replies.py
# → writes data-v2/classified-new-replies.json
# → prints 其他 samples for manual review

# 3. (Optional) add URL-based overrides for misclassified items
#    Edit generate_overrides.py → add to OVERRIDES dict
#    python3 generate_overrides.py  (writes data/category-overrides.json)

# 4. Merge + rebuild chart data
python3 build_v2_data.py
# → writes data-v2/replies.json, data-v2/chart_data.json

# 5. Rebuild dashboard
python3 build.py --data-dir data-v2
# → overwrites index.html
```

## Reclassifying replies (manual overrides)

1. **Edit `generate_overrides.py`** — add entries to `OVERRIDES` dict:
   `"https://www.threads.com/@user/post/ID": ("category", "subcategory|None")`
2. `python3 generate_overrides.py` → overwrites `data/category-overrides.json`
3. `python3 build_v2_data.py` → picks up the updated overrides and rebuilds `data-v2/`
4. `python3 build.py --data-dir data-v2` → regenerates `index.html`

To add a new category or subcategory, also update `build.py` — add zh/en labels to `cat_labels` and `sub_labels` in the `i18n` dict, and add a color to `CAT_COLORS` in `apply_overrides.py`.

## Scraper notes

- Uses Playwright with a persistent Chrome profile (`mcp-chrome-235b035`) to reuse an active Threads login session
- Intercepts `api/graphql` responses to extract structured reply data (author, text, likes, timestamp, URL) — more reliable than DOM parsing
- Scrolls up to 120 times at 1.8s intervals; stops after 6 consecutive scrolls with no new replies
- Chromium binary path is hardcoded to the local installation — update `CHROMIUM_EXEC` in `scripts/scrape_new_replies.js` if it changes

---

Built with [Claude Code](https://claude.ai/code) · Chart.js 4.4
