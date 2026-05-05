# 社死大調查 · Cringe Moments Survey

An interactive analysis of 683 replies to a viral Threads post asking people to share their most embarrassing public moments.

**Source post:** [@betabreakhsin](https://www.threads.com/@betabreakhsin/post/DXzS3YEEY8t) — "大家人生中社死現場第一名是什麼？"

## Features

- **Stacked bar chart** — categories ranked by total likes, with subcategory breakdown
- **Toggle** between likes view and reply count view
- **Sidebar filters** — click any category or subcategory to filter the table
- **Search** — filter by reply text or author handle
- **EN / 中 toggle** — full bilingual UI
- **Direct links** — every reply row has a 🔗 link to the original Threads reply + 🌐 Google Translate

## How to use

Just open `index.html` in any modern browser — no server needed, fully self-contained.

## Categories (v2)

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

**v2 changes from v1:**
- `點餐/購物口誤` expanded to `口誤` — now covers all verbal slips (workplace, language mix-up, brain glitch, sexual homophone)
- `走錯店/進錯車` renamed to `走錯空間`
- 426 replies reclassified from `其他` — down to 47 truly uncategorizable fragments

## Data

Scraped 683 replies from ~1,900 total (top-engagement portion). Data snapshot from 2026-05-03. Likes counts reflect that moment in time.

## Files

```
data/
  replies.json           # source of truth — all 683 replies with full fields
  chart_data.json        # compact format consumed by build.py → index.html
  category-map.json      # v1 taxonomy (kept for reference)
  category-overrides.json # URL → {category, subcategory} for the 426 reclassified items

generate_overrides.py    # all manual classifications hardcoded — edit here to reclassify
apply_overrides.py       # applies overrides + renames to replies.json, rebuilds chart_data.json
build.py                 # bakes chart_data.json + i18n into index.html
```

## Future remapping

To reclassify replies or adjust categories:

1. **Edit `generate_overrides.py`** — add/change entries in the `OVERRIDES` dict (key = Threads URL, value = `(category, subcategory|None)`)
2. **Run** `python3 generate_overrides.py` → overwrites `data/category-overrides.json`
3. **Restore** `data/replies.json` to its original state first if re-running from scratch (overrides are applied on top of the original `其他` classifications; running `apply_overrides.py` twice will double-apply)
4. **Run** `python3 apply_overrides.py` → updates `replies.json` + rebuilds `chart_data.json`
5. **Run** `python3 build.py` → regenerates `index.html`

To add a new category or subcategory, also update:
- `build.py` — add zh/en labels to both `cat_labels` and `sub_labels` in the `i18n` dict

---

Built with [Claude Code](https://claude.ai/code) · Chart.js 4.4
