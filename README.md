# 社死大調查 · Cringe Moments Survey

An interactive analysis of replies to a viral Threads post asking people to share their most embarrassing public moments.

**Source post:** [@betabreakhsin](https://www.threads.com/@betabreakhsin/post/DXzS3YEEY8t) — "大家人生中社死現場第一名是什麼？"

## Features

- **Stacked bar chart** — categories ranked by total likes, with subcategory breakdown stacked by likes within each bar
- **Sidebar filters** — categories and subcategories ranked by likes; click any row to filter the reply table
- **Search** — filter by reply text or author handle (`@handle` works)
- **EN / 中 toggle** — full bilingual UI. EN mode shows only the 455 universal replies in pre-translated English; 中 mode shows all 1,155 in original Chinese
- **3-screen welcome modal** — auto-shown on first visit (pre-selects EN or 中 based on browser language). Floating `?` button reopens it anytime
- **Direct links** — every reply row links to the original Threads reply

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

| Snapshot | Replies | Scraped | Notes |
|---|---|---|---|
| original | 683 | 2026-05-03 | Top-engagement replies only; preserved in `archive/v1-2026-05-03/` |
| current | 1,155 | 2026-05-15 | Live dataset in `data/`; added 472 new replies, refreshed like counts for 250 existing |

**Bilingual:** 455 replies are classified as `intl=true` (universal, translation lands cleanly in English) and have a `text_en` field. The remaining 700 lean on Taiwan-specific puns, slang, or cultural context and stay in original Chinese only. In EN mode the dashboard shows only the 455 translatable ones; in 中 mode it shows all 1,155.

## File structure

```
data/                            # live, current dataset
  replies.json                     # 1,155 replies, full fields (incl. text_en where intl=true)
  chart_data.json                  # compact format for dashboard
  category-map.json                # taxonomy reference
  category-overrides.json          # URL → {category, subcategory} manual overrides
  staging/                         # in-flight batches (gitignored)
    raw-scraped.json                 # latest scrape output, unclassified
    classified-batch.json            # latest batch after classification, pre-merge
    translated-batch.json            # latest batch after translation, pre-merge
  .backup/                         # snapshots before destructive writes (gitignored)
    manual-translations.json         # working file for batch translations done in Claude Code

pipeline/                        # ordered pipeline scripts
  scrape.js                        # 1. Playwright scraper → staging/raw-scraped.json
  classify.py                      # 2. keyword classifier → staging/classified-batch.json
  overrides.py                     # (optional) regenerate data/category-overrides.json
  translate.py                     # 3. (optional) translate intl=true replies via Claude API
  merge.py                         # 4. merge batch into data/, rebuild chart_data.json
  build.py                         # 5. bake chart_data.json + i18n → index.html
  package.json                     # Playwright dependency for scrape.js

archive/                         # frozen historical snapshots
  v1-2026-05-03/                   # original 683-reply snapshot + v1→v2 migration tooling

index.html                       # built artifact (committed; CI rebuilds on push)
index_template.html              # source template for build.py
```

## Updating with new replies

```bash
# 1. Scrape — requires Playwright Chromium and active Threads login in browser profile
node pipeline/scrape.js
# → writes data/staging/raw-scraped.json

# 2. Classify the batch
python3 pipeline/classify.py
# → writes data/staging/classified-batch.json
# → prints 其他 samples for manual review

# 3. (Optional) add URL-based overrides for misclassified items
#    Edit pipeline/overrides.py → add to OVERRIDES dict
#    python3 pipeline/overrides.py  (writes data/category-overrides.json)

# 4. (Optional) translate intl=true replies via Claude API (needs ANTHROPIC_API_KEY in .env)
python3 pipeline/translate.py
# → writes data/staging/translated-batch.json
# Alternative: do translations manually in a Claude Code session — append to
# data/.backup/manual-translations.json, then merge.py picks them up next run.

# 5. Merge batch into live dataset (auto-snapshots data/replies.json → data/.backup/ first)
python3 pipeline/merge.py
# → writes data/replies.json (incl. text_en), data/chart_data.json

# 6. Rebuild dashboard
python3 pipeline/build.py
# → overwrites index.html
```

CI runs step 6 automatically on every push to `main`.

## Translation notes

- Only replies with `intl=true` get translated. Taiwan-specific puns / slang / cultural context (`intl=false`) stay in original Chinese only.
- If a translation reads awkwardly (the joke depends on Chinese phonology, e.g. 接頭/龜頭, 戚風/威風), reclassify the row to `intl=false` rather than try to translate the unrenderable pun.
- The dashboard's language toggle drives both text language AND row filtering: EN mode shows only translated rows, 中 mode shows all.

## Reclassifying replies (manual overrides)

1. **Edit `pipeline/overrides.py`** — add entries to `OVERRIDES` dict:
   `"https://www.threads.com/@user/post/ID": ("category", "subcategory|None")`
2. `python3 pipeline/overrides.py` → overwrites `data/category-overrides.json`
3. `python3 pipeline/merge.py` → picks up the updated overrides and rebuilds `data/chart_data.json`
4. `python3 pipeline/build.py` → regenerates `index.html`

To add a new category or subcategory, also update `pipeline/build.py` — add zh/en labels to `cat_labels` and `sub_labels` in the `i18n` dict, and add a color to `CAT_COLORS` in `pipeline/merge.py`.

## Scraper notes

- Uses Playwright with a persistent Chrome profile (`mcp-chrome-235b035`) to reuse an active Threads login session
- Intercepts `api/graphql` responses to extract structured reply data (author, text, likes, timestamp, URL) — more reliable than DOM parsing
- Scrolls up to 120 times at 1.8s intervals; stops after 6 consecutive scrolls with no new replies
- Chromium binary path is hardcoded to the local installation — update `CHROMIUM_EXEC` in `pipeline/scrape.js` if it changes

---

Built with [Claude Code](https://claude.ai/code) · Chart.js 4.4
