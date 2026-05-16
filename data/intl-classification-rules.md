# `intl` Classification Rules

Rules for deciding whether a reply's humor is "internationally understandable" (`intl: true`) or requires Chinese language/culture knowledge to land (`intl: false`).

**Core test:** Translate the story into English for a non-Chinese friend. Is it still funny? If yes → `intl: true`. If the punchline dies in translation → `intl: false`.

---

## Hard rules — always `intl: false`

Sexual-organ homophones, even if the original word was innocent:

- 龜頭 (glans) — e.g. 接頭/龜頭, 歸頭/龜頭, 歸仁→歸頭
- 奶頭 / 乳頭 (nipple) — e.g. 奶油/奶頭, 芋頭/奶頭, 乳糖/乳頭
- 陰毛 (pubic hair) — e.g. 陰霾/陰毛
- 雞雞 / LP / 性器 — Taiwanese sexual slang
- Other body-part homophone slips

These are always false regardless of how universal the surrounding situation looks. The punchline is the homophone itself.

---

## Not universal (`intl: false`)

### Language-dependent
- **諧音梗 (homophones)** — Mandarin or Taiwanese sound-alike pairs (戚風/威風, 葉問/業務, 海綿蛋糕/海綿體)
- **Chinese mispronunciation** — wrong tone, wrong character (聶/ㄕㄜˋ, ㄔ/ㄑㄧˋ)
- **Truncated Chinese phrases** — when humor relies on the truncated form sounding like something else (你沒有用到/你沒有用, 不好意思/你好意思, 外帶/外用)
- **Chinese idiom misuse** — 以訛傳訛, 卍解, 信口開河 used wrong
- **Taiwanese-language jokes** — 速共, 當吔里賀, LP的P
- **Code-mixing puns** — only works if reader knows the Chinese reading (鱟/whoo)

### Culturally specific
- **TW-specific brand confusion as punchline** — 50嵐, 統一發票/統一編號, 104, 健達情趣蛋, 葉問/業務. Note: brand presence alone is fine; only mark false if the brand IS the joke.
- **Cigarettes / TW slang** — 七星, 長壽 when used as cigarette names
- **Chinese pop culture references** as punchline — Show Lo lyrics, Jay Chou half-song, Chinese movie names (笑傲飛鷹)
- **Chinese name puns** — 姓大→大小姐, 侑襄/柚香, 溫蒂漫步/溫室雜草, 關心妍/關菊英
- **Chinese-specific holidays/concepts** — 端午節 vs 中秋節 mix-up
- **Chinese-specific food names that ARE the joke** — 冬瓜澑澑, 八寶冰, 觀落陰

### Meta replies (always false)
- 回覆原 PO category — comments on the OP, not original stories

---

## Universal (`intl: true`)

### Physical comedy / body
- Tripping, slipping, falling on stairs
- Walking into clean glass doors
- Couldn't brake on ice/bike → hugged stranger
- Bus/train sudden brake → fell onto stranger's lap
- Skirt stuck in tights / fly undone / open backpack
- Foot mask peeling visible during emergency

### Mistaken identity (visual)
- Hugged/slapped/yelled at wrong person from behind
- Followed wrong car, opened door
- Got into wrong dorm room / KTV box / hot pot shop
- Talked to mannequin thinking it's a friend

### Social slips (situational, not linguistic)
- Wrong group chat with embarrassing message
- Browsing job site / personal stuff visible on shared screen
- Oversharing in elevator / public ("my bladder is big")
- Calling teacher "mom" (truly universal Freudian slip)
- Reflexive workplace behavior in wrong setting ("welcome!" on a bus from a retail worker)

### Cross-cultural language goofs (universally understandable)
- Saying "I love you" instead of "thank you" in foreign language
- Saying "go to hell" instead of "where to"
- Bowing and saying "how much" as goodbye
- Mistaking 金玉 (Japanese: testicles) for Snitch
- These work because the *direction* of the mistake is universal even if details aren't

### Reflexive behaviors
- Bark on cue, "yes sir" military reflex
- Retail conditioning ("welcome" at wrong store)
- Picking up wrong customer / wrong order from old job

### Universal awkwardness
- Asking if someone is pregnant when they're not
- Mistaking partner for stranger and calling them a "nerd"
- Asking customer "do you have money?" instead of "how will you pay?"
- Asking server "can you hand-feed me?"
- Kids saying embarrassing things in public

### Brand/store mix-ups (situation is universal)
- Ordering at wrong restaurant (KFC menu at McDonald's)
- Smelling all the perfumes at the wrong brand counter
- Bringing expired flyer to checkout

### Eggplant innuendo & similar
- "Do you want to eat my eggplant?" — universal because eggplant is a globally recognized innuendo

---

## Edge cases

| Scenario | Decision | Why |
|---|---|---|
| Famous person referenced (Show Lo, Jay Chou, Ip Man) | Depends on whether their *name* is the pun | Just being in the story = universal. Name-as-homophone = not universal |
| Foreign language slip BY the Chinese speaker | Usually universal | Hearing the difference between two foreign words doesn't require Chinese knowledge |
| Chinese-language slip in a foreign country | Not universal | If the punchline is the Chinese sound mismatch |
| Brand mentioned in passing (Starbucks, IKEA) | Universal | The setting is global |
| Mistaken-identity story with Chinese name | Universal | Name doesn't matter; situation does |
| Incomplete text (cut off mid-story) | Default `true` unless visible Chinese-pun keywords | Benefit of the doubt |
| Reply-to-OP (回覆原 PO category) | Always `false` | Meta reactions, not stories |

---

## Decision algorithm

```
1. If text contains 龜頭/奶頭/乳頭/陰毛/雞雞/LP as punchline → false
2. If category == "回覆原 PO" → false
3. If text contains slip indicators (說成/變成/講成/脫口而出) AND the substituted word is a Chinese homophone of the intended word → false
4. If the punchline is a Chinese name, idiom, brand, or pop reference → false
5. Else: translate the story to English mentally. Still funny? → true. Otherwise → false
```

---

## When updating new data

When new replies are scraped (e.g. v2's 472 new replies), apply this same ruleset. Hard rules are deterministic; the rest requires reading each text.

For batch processing: a Python script can pre-flag hard-rule hits and reply-to-OP entries. Everything else needs manual review.

**Related files:**
- `data/replies.json` — current dataset with `intl` field
- `data/replies-v3.json` — delta file with re-classified `intl` values + reasons (this rule pass)
- `data/category-overrides.json` — category corrections
