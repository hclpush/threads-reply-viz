# -*- coding: utf-8 -*-
import json, base64, os, unicodedata, argparse

BASE = os.path.dirname(os.path.abspath(__file__))

parser = argparse.ArgumentParser()
parser.add_argument('--data-dir', default='data', help='data directory (default: data)')
args = parser.parse_args()

DATA_DIR = os.path.join(BASE, args.data_dir)

# Load + sanitize data
with open(os.path.join(DATA_DIR, 'chart_data.json'), encoding='utf-8') as f:
    cd = json.load(f)

def clean(s):
    if not isinstance(s, str): return s
    return ''.join(c for c in s
                   if unicodedata.category(c) not in ('Cf','Cs','Co') or c == '\n')

for r in cd['replies']:
    r['t'] = clean(r.get('t', ''))

data_b64 = base64.b64encode(
    json.dumps(cd, ensure_ascii=False).encode('utf-8')
).decode('ascii')

total = cd.get('total', len(cd.get('replies', [])))

# i18n — all values will be escaped to \uXXXX by ensure_ascii=True
i18n = {
    "zh": {
        "title": "社死大調查",
        "subtitle": "回覆分析 · @betabreakhsin",
        "search_placeholder": "搜尋回覆內容或作者...",
        "toggle_likes": "按喜歡數", "toggle_count": "按回覆數",
        "all_categories": "所有類別",
        "col_likes": "喜歡", "col_author": "作者",
        "col_category": "類別", "col_text": "內容", "col_link": "連結",
        "source": f"資料來源：Threads @betabreakhsin · {total} 則留言樣本",
        "no_results": "沒有符合的結果",
        "sidebar_title": "類別",
        "cat_labels": {
            "口誤": "口誤",
            "被工作/兵役制約": "被工作/兵役制約",
            "認錯人": "認錯人",
            "當眾出糗": "當眾出糗",
            "其他": "其他",
            "回覆原 PO": "回覆原 PO",
            "以為在跟自己說話": "以為在跟自己說話",
            "走錯空間": "走錯空間",
            "以為沒人亂講話": "以為沒人亂講話",
            "叫錯": "叫錯",
        },
        "sub_labels": {
            "點餐/購物": "點餐/購物",
            "職場口誤": "職場口誤",
            "語言混亂": "語言混亂",
            "腦袋當機": "腦袋當機",
            "乳頭/奶頭": "乳頭/奶頭",
            "一起說歡迎光臨": "一起說歡迎光臨",
            "當完兵喊「有！」": "當完兵喊「有！」",
            "有肢體接觸": "有肢體接觸",
            "沒有肢體接觸": "沒有肢體接觸",
            "工作中": "工作中",
            "童言無忌": "童言無忌",
            "學狗叫": "學狗叫",
            "語言不通": "語言不通",
            "你好可愛": "你好可愛",
            "好好笑": "好好笑",
            "好好笑長出腹肌": "好好笑長出腹肌",
            "留 X 看": "留 X 看",
            "以為店員在跟自己說話": "以為店員在跟自己說話",
            "領錯獎/誤以為得獎": "領錯獎/誤以為得獎",
            "叫老師媽媽": "叫老師媽媽",
        }
    },
    "en": {
        "title": "Cringe Moments Survey",
        "subtitle": "Reply Analysis · @betabreakhsin",
        "search_placeholder": "Search replies or authors...",
        "toggle_likes": "By Likes", "toggle_count": "By Count",
        "all_categories": "All Categories",
        "col_likes": "Likes", "col_author": "Author",
        "col_category": "Category", "col_text": "Content", "col_link": "Link",
        "source": f"Source: Threads @betabreakhsin · {total} reply sample",
        "no_results": "No results found",
        "sidebar_title": "Category",
        "cat_labels": {
            "口誤": "Slip of the Tongue",
            "被工作/兵役制約": "Conditioned by Work/Military",
            "認錯人": "Mistook Someone",
            "當眾出糗": "Public Embarrassment",
            "其他": "Others",
            "回覆原 PO": "Reply to OP",
            "以為在跟自己說話": "Thought Someone Talked to Me",
            "走錯空間": "Walked into Wrong Place",
            "以為沒人亂講話": "Talked Freely, Got Caught",
            "叫錯": "Called Wrong Name",
        },
        "sub_labels": {
            "點餐/購物": "Ordering / Shopping",
            "職場口誤": "Workplace slip",
            "語言混亂": "Language mix-up",
            "腦袋當機": "Brain glitch",
            "乳頭/奶頭": "Nipple homophone",
            "一起說歡迎光臨": "Said Welcome out of habit",
            "當完兵喊「有！」": "Shouted Present post-military",
            "有肢體接觸": "With Physical Contact",
            "沒有肢體接觸": "Without Physical Contact",
            "工作中": "While Working",
            "童言無忌": "Kid said the quiet part loud",
            "學狗叫": "Barked Like a Dog",
            "語言不通": "Language Barrier",
            "你好可愛": "OP is so cute",
            "好好笑": "So funny",
            "好好笑長出腹肌": "Laughed until abs hurt",
            "留 X 看": "Saved to watch",
            "以為店員在跟自己說話": "Thought clerk was talking to me",
            "領錯獎/誤以為得獎": "Claimed Wrong Prize",
            "叫老師媽媽": "Called Teacher Mom",
        }
    }
}
i18n_js = json.dumps(i18n, ensure_ascii=True)

# Read HTML template
with open(os.path.join(BASE, 'index_template.html'), encoding='utf-8') as f:
    html = f.read()

html = html.replace('__DATA_B64__', data_b64)
html = html.replace('__I18N__', i18n_js)

out = os.path.join(BASE, 'index.html')
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)

sc = html.count('</script>')
print(f"Written {len(html):,} chars | </script> count: {sc} (expect 2)")
print(f"data_b64: {len(data_b64):,} chars")
print(f"Total replies in dashboard: {total}")
print(f"Data source: {args.data_dir}/")
