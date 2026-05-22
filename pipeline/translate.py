# -*- coding: utf-8 -*-
"""
Translates universal (intl=true) Taiwanese social media replies into casual English.

Modes:
  (default)         translate data/staging/classified-batch.json → translated-batch.json
  --backfill        translate intl=true replies in data/replies.json that lack text_en
                    (in place, with auto-backup to data/.backup/)
  --pilot [N]       pilot mode: translate N random universal replies from data/replies.json
                    (default N=10). Prints original + translation side-by-side. No write to
                    replies.json; saves a copy to data/.backup/pilot-translations-*.json.
  --review          interactive: accept / skip / regenerate / quit per reply
  --model ID        override model (default: claude-haiku-4-5-20251001)
  --batch N         batch size (default: 10)

Run examples:
  python3 pipeline/translate.py                       # translate the staging batch
  python3 pipeline/translate.py --pilot               # 10-reply pilot from live data
  python3 pipeline/translate.py --pilot 5 --review    # 5-reply pilot, interactive
  python3 pipeline/translate.py --backfill            # backfill live dataset
"""
import argparse
import json
import os
import random
import sys
from datetime import datetime
from pathlib import Path

ROOT     = Path(__file__).resolve().parent.parent
DATA     = ROOT / 'data'
STAGING  = DATA / 'staging'
BACKUP   = DATA / '.backup'

DEFAULT_MODEL = 'claude-haiku-4-5-20251001'
DEFAULT_BATCH = 10


# ── .env loader (no external dependency) ──────────────────────────────────────
def load_dotenv():
    env_path = ROOT / '.env'
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_dotenv()

try:
    from anthropic import Anthropic
except ImportError:
    sys.stderr.write("Missing dependency. Run: pip install anthropic\n")
    sys.exit(1)


# ── Translation prompt ────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are translating short Taiwanese social media replies (Traditional Chinese) into casual, natural English.

These are people sharing embarrassing personal moments on Threads, often self-deprecating, often funny. Translate them like you'd retell the story to a friend.

Rules:
- Preserve the casual, conversational tone. Contractions, mild informality, slight self-deprecation are good.
- Preserve emojis (🫢😭🫨), emphatic punctuation (!!!, ww, lol), and line breaks (paragraphs as written).
- Do NOT add explanations, brackets, or footnotes — just translate the moment as-is.
- For names/places/brands, keep them readable: 統一 → Uni-President, 7-11 → 7-11, 阿嬤 → grandma (or aunty in context).
- If a joke leans on Chinese wordplay or a Chinese-specific pun, translate the meaning literally — do not invent an English pun. If the literal translation kills the joke, that's fine — the data flag may need to change.
- For English words already mixed into the Chinese text (e.g. "Visa卡", "lol"), keep them as English.
- Output ONLY a JSON array of translation strings, in the same order as input. No prose around the JSON."""


# ── API client ────────────────────────────────────────────────────────────────
def make_client():
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        sys.stderr.write("ANTHROPIC_API_KEY not set. Add to .env (gitignored) or export in shell.\n")
        sys.exit(1)
    return Anthropic(api_key=api_key)


def translate_batch(client, model, texts):
    """Send one batch of texts to Claude. Returns list of translations in same order."""
    user_content = "Translate these replies. Output a JSON array of strings, same order:\n\n"
    for i, t in enumerate(texts, 1):
        user_content += f"---REPLY {i}---\n{t}\n\n"

    resp = client.messages.create(
        model=model,
        max_tokens=4096,
        system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": "["},
        ],
    )

    body = "[" + resp.content[0].text
    last_bracket = body.rfind(']')
    if last_bracket == -1:
        raise RuntimeError(f"No closing ] in response:\n{body[:500]}")
    body = body[:last_bracket + 1]

    try:
        translations = json.loads(body)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"JSON parse failed: {e}\nGot:\n{body[:500]}")

    if len(translations) != len(texts):
        raise RuntimeError(f"Expected {len(texts)} translations, got {len(translations)}")

    return translations


# ── Review prompt ─────────────────────────────────────────────────────────────
def review_translation(orig, trans):
    print(f"\n{'─'*60}")
    print(f"ORIGINAL:\n{orig}")
    print(f"\nTRANSLATION:\n{trans}")
    while True:
        ans = input("\n[a]ccept / [s]kip / [r]egenerate / [q]uit  > ").strip().lower()
        if ans in ('a', 'accept', ''): return 'accept'
        if ans in ('s', 'skip'):       return 'skip'
        if ans in ('r', 'regen'):      return 'regenerate'
        if ans in ('q', 'quit'):       return 'quit'


def translate_replies(client, model, replies, batch_size, review_mode=False):
    """Adds text_en to each reply. Returns (translated, skipped, quit_early)."""
    pending = [r for r in replies if not r.get('text_en')]
    if not pending:
        print("All replies already have text_en. Nothing to translate.")
        return 0, 0, False

    print(f"Translating {len(pending)} replies in batches of {batch_size}...")
    translated, skipped, quit_early = 0, 0, False

    for i in range(0, len(pending), batch_size):
        chunk = pending[i:i+batch_size]
        texts = [r['text'] for r in chunk]
        print(f"  Batch {i//batch_size + 1}: {len(chunk)} replies... ", end='', flush=True)
        try:
            translations = translate_batch(client, model, texts)
        except Exception as e:
            print(f"FAILED ({e})")
            skipped += len(chunk)
            continue
        print("done.")

        for r, t in zip(chunk, translations):
            if review_mode:
                while True:
                    action = review_translation(r['text'], t)
                    if action == 'accept':
                        r['text_en'] = t
                        translated += 1
                        break
                    if action == 'skip':
                        skipped += 1
                        break
                    if action == 'regenerate':
                        try:
                            t = translate_batch(client, model, [r['text']])[0]
                        except Exception as e:
                            print(f"Regen failed: {e}")
                            skipped += 1
                            break
                    if action == 'quit':
                        return translated, skipped, True
            else:
                r['text_en'] = t
                translated += 1

    return translated, skipped, quit_early


# ── Commands ──────────────────────────────────────────────────────────────────
def cmd_default(args, client):
    """Translate the latest classified batch."""
    in_path  = STAGING / 'classified-batch.json'
    out_path = STAGING / 'translated-batch.json'

    if not in_path.exists():
        print(f"No classified batch at {in_path}. Run pipeline/classify.py first.")
        return

    with open(in_path, encoding='utf-8') as f:
        batch = json.load(f)

    universal = [r for r in batch if r.get('intl') is True]
    print(f"Loaded {len(batch)} from classified batch. {len(universal)} are intl=true (will translate).")

    translate_replies(client, args.model, universal, args.batch, review_mode=args.review)

    # Merge text_en back into the full batch (intl=false stays untouched)
    by_url = {r['url']: r for r in universal}
    for r in batch:
        if r['url'] in by_url and by_url[r['url']].get('text_en'):
            r['text_en'] = by_url[r['url']]['text_en']

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(batch, f, ensure_ascii=False, indent=2)
    print(f"Wrote → {out_path}")


def cmd_backfill(args, client):
    """Translate intl=true rows in data/replies.json that lack text_en, in place with backup."""
    replies_path = DATA / 'replies.json'
    with open(replies_path, encoding='utf-8') as f:
        data = json.load(f)

    BACKUP.mkdir(exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    backup_path = BACKUP / f'replies.{stamp}.pre-translate.json'
    backup_path.write_bytes(replies_path.read_bytes())
    print(f"Backup → {backup_path}")

    intl_true = [r for r in data['replies'] if r.get('intl') is True]
    pending   = [r for r in intl_true if not r.get('text_en')]
    print(f"intl=true: {len(intl_true)} | already translated: {len(intl_true) - len(pending)} | pending: {len(pending)}")
    if not pending:
        print("Nothing to translate.")
        return

    translated, skipped, quit_early = translate_replies(client, args.model, pending, args.batch, review_mode=args.review)

    with open(replies_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\nTranslated: {translated} | Skipped: {skipped}")
    if quit_early:
        print("(Quit early — partial save written.)")
    print(f"Updated → {replies_path}")


def cmd_pilot(args, client):
    """Translate N random universal replies from data/replies.json, print results. No save to replies.json."""
    n = args.pilot if isinstance(args.pilot, int) else 10
    replies_path = DATA / 'replies.json'
    with open(replies_path, encoding='utf-8') as f:
        data = json.load(f)

    intl_true = [r for r in data['replies'] if r.get('intl') is True and not r.get('text_en')]
    if not intl_true:
        print("No intl=true replies need translation.")
        return

    random.seed(42)  # reproducible sample
    sample = random.sample(intl_true, min(n, len(intl_true)))
    print(f"Pilot: {len(sample)} replies | model={args.model}")

    # Translate on copies (don't mutate original data structure)
    copies = [dict(r) for r in sample]
    translate_replies(client, args.model, copies, args.batch, review_mode=args.review)

    print(f"\n{'='*60}\nPILOT RESULTS\n{'='*60}")
    for i, r in enumerate(copies, 1):
        cat = f"[{r.get('category', '?')} / {r.get('subcategory') or '-'}]"
        print(f"\n--- {i}. {cat} ---")
        print(f"原文:\n{r['text']}")
        print(f"\nEN:\n{r.get('text_en', '(no translation)')}")

    BACKUP.mkdir(exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    out_path = BACKUP / f'pilot-translations-{stamp}.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(copies, f, ensure_ascii=False, indent=2)
    print(f"\nSaved → {out_path}")


# ── CLI ───────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument('--backfill', action='store_true',
                    help='translate intl=true rows in data/replies.json in place')
    ap.add_argument('--pilot', nargs='?', const=10, type=int, metavar='N',
                    help='pilot N random universal replies (default N=10), no save to replies.json')
    ap.add_argument('--review', action='store_true',
                    help='interactive accept/skip per translation')
    ap.add_argument('--model', default=DEFAULT_MODEL,
                    help=f'model id (default: {DEFAULT_MODEL})')
    ap.add_argument('--batch', type=int, default=DEFAULT_BATCH,
                    help=f'batch size (default: {DEFAULT_BATCH})')
    args = ap.parse_args()

    client = make_client()

    if args.pilot is not None:
        cmd_pilot(args, client)
    elif args.backfill:
        cmd_backfill(args, client)
    else:
        cmd_default(args, client)


if __name__ == '__main__':
    main()
