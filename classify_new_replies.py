# -*- coding: utf-8 -*-
"""
Classifies new replies in data-v2/raw-scraped.json → data-v2/classified-new-replies.json
Run: python3 classify_new_replies.py
"""
import json, os, re
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))


def has(text, *keywords):
    return any(kw in text for kw in keywords)


def classify(text):
    t = text.strip()
    short = len(t) < 60

    # ── 回覆原 PO ─────────────────────────────────────────────────────────────
    # Definitive reaction markers (no personal story)
    reaction_strong = [
        '哈哈哈', '笑死', '笑爛', '笑到', '噴了', '噴出來笑', '去世了', '我死掉',
        '嗚嗚嗚', '救命啊', '不行了', '我要死', '我死了', '崩潰了', '笑翻',
        '快笑死', '笑出聲', '好好笑', '超好笑', '太好笑了', '笑到哭', '哈哈哈哈',
        '可以笑', '真的笑了', '笑爆', '笑我',
    ]
    for kw in reaction_strong:
        if kw in t and len(t) < 80:
            return ('回覆原 PO', None)

    # Pattern: "留X看" or "留著看"
    if re.search(r'留[^\n]{0,5}看', t) and short:
        return ('回覆原 PO', '留 X 看')

    # Short reactions — text < 50 chars with reaction words
    if short:
        if has(t, '哈哈', '笑', '可愛', '推', '崩潰', '嗚嗚', '噴', '救命',
               '這篇', '原PO', '按讚', '去世', '怎麼', '笑完', '看完', '樓下',
               '不行', '社死', '看著看著', '謝謝你分享', '升級成', '有畫面', '社死包廂',
               '正向', '頒給你', '同款', '浪漫', '連環', '真實案例', '代言',
               '異曲同工', '幫你繫', '有情趣', '得主', '為什麼是', '加一等',
               '超尷尬', '已離開現場', '先告辭', '不好意思了', '想離職',
               '清楚', '貼心', '直率', '好心', '現世報', '沒問題', '古董',
               '太多了', '沒事了', '紅毯', '你懂', '覺得很正向', '這叫做', '貴舍',
               '探討', '驚恐', '宅男', '原因是', '值得了', '犧牲'):
            return ('回覆原 PO', None)

    # Reaction to someone else's story (referencing a previous post)
    if has(t, '這跟最近那個', '跟你一樣', '我也一樣', '同款社死', '我也有過', '我也是',
           '雷同', '讓我想起') and short:
        return ('回覆原 PO', None)

    # Referencing another reply within the thread
    if has(t, '樓上', '您好，這邊', '升級成社死', '恭喜獲得') and short:
        return ('回覆原 PO', None)

    # ── 被工作/兵役制約 ───────────────────────────────────────────────────────
    if has(t, '當兵', '服役', '兵役', '退伍', '成功嶺', '軍中', '阿兵哥',
           '喊有！', '喊「有！', '當完兵', '替代役') :
        if has(t, '喊有', '立正', '稍息', '有！'):
            return ('被工作/兵役制約', '當完兵喊「有！」')
        return ('被工作/兵役制約', None)

    # Reflexive greeting/habit
    if has(t, '歡迎光臨', '謝謝光臨', '謝謝惠顧', '謝謝您的蒞臨'):
        if has(t, '職業病', '習慣', '下意識', '條件反射', '不自覺', '打工', '上班',
               '一起喊', '跟著喊', '自動喊出', '喊出來', '喊了出來'):
            return ('被工作/兵役制約', '一起說歡迎光臨')
        # Reflexively said welcome somewhere inappropriate
        if has(t, '咖啡廳', '餐廳', '朋友家', '百貨', '結果喊', '不小心喊',
               '喊了', '喊出', '脫口喊'):
            return ('被工作/兵役制約', '一起說歡迎光臨')

    if has(t, '職業病', '下意識', '條件反射'):
        if has(t, '喊', '說', '叫', '講', '回答'):
            return ('被工作/兵役制約', None)

    # ── 口誤 > 乳頭/奶頭 ─────────────────────────────────────────────────────
    if has(t, '乳頭', '奶頭'):
        return ('口誤', '乳頭/奶頭')

    # ── Slip detection (broad) ─────────────────────────────────────────────────
    slip_kw = [
        '說錯', '講錯', '說成', '講成', '說出口', '口誤', '說溜嘴', '不小心說', '不小心講',
        '說出來', '講出來', '脫口而出', '一時', '搞混', '才反應', '才意識到',
        '說完才', '沒睡好', '剛睡醒', '腦袋空白', '腦當機', '說自己名字',
        '喊成', '喊錯', '叫成', '說了', '講了', '喊了', '說出', '問錯',
        '介紹成', '介紹錯', '報錯', '自報', '打錯', '說太快', '自信滿滿',
    ]
    is_slip = has(t, *slip_kw)

    # ── 口誤 > 語言混亂 ───────────────────────────────────────────────────────
    lang_kw = ['英文', '日文', '台語', '粵語', '韓文', '法文', '德文', '語言',
               '說成英', '說成日', '說成台', '切換', '母語', '外語', '海外',
               '在國外', '外國', 'department', 'store', '講英文', '說英文']
    if has(t, *lang_kw) and (is_slip or has(t, '結果說', '脫口說', '說了')):
        return ('口誤', '語言混亂')

    # ── 口誤 > 職場口誤 ───────────────────────────────────────────────────────
    medical_kw = ['護理', '護士', '護師', '醫生', '醫師', '醫院', '病人', '病房',
                  '診所', '加護', '手術', '急診', '護理站', '實習', '住院', '院長',
                  '解釋病情', '病況', '感染', '治療', '患者', '術後', '麻醉']
    # Medical context slips (including wrong relationship address)
    if has(t, *medical_kw):
        # Called patient's family member wrong title (e.g. wife→mother)
        if has(t, '您母親', '你母親', '她是我老婆', '是我先生', '是我老公'):
            return ('口誤', '職場口誤')
        if is_slip or has(t, '說', '喊', '問', '叫', '非常抱歉', '很抱歉'):
            return ('口誤', '職場口誤')
        return ('當眾出糗', '工作中')

    # General workplace slips
    work_context = has(t, '主管', '老闆', '客戶', '同事', '面試', '上司', '開會',
                       '打工', '工讀', '上班', '公司', '值班', '輪班', '工作', '職場',
                       '店員', '服務員', '收銀員', '收銀台', '客人', '訂位', '接待',
                       '介紹商品', '跟客人', '接電話', '回答客', '帶位', '結帳',
                       '連鎖', '711', '7-11', '全家', '超商', '麥當勞', 'mister donut',
                       '補習班', '教室', '老師', '學生', '家長')
    # Stage/performance slip
    stage_context = has(t, '台上', '舞台', '表演', '主持', '演唱', '婚宴', '比賽',
                        '頒獎', '播報', '主播', '直播', '開幕', '致詞')
    if (work_context or stage_context) and (is_slip or has(t, '不小心', '結果', '喊錯', '說錯地點',
                                                             '非常抱歉', '被聽到', '發現',
                                                             '脫口', '說出', '喊了')):
        # Stage slip — said wrong city/info
        if stage_context and has(t, '桃園', '台北', '台中', '高雄', '大家好', '朋友們'):
            return ('口誤', '職場口誤')
        if work_context:
            # Check if it's ordering context (customer making a slip at a shop)
            if has(t, '結帳', '點餐', '買', '訂位', '外送', '超商', '夜市', '買單'):
                # Is the speaker a worker or a customer?
                if has(t, '我在', '我工作', '打工', '工讀', '上班', '工作', '客人',
                       '帶位', '收銀', '介紹商品'):
                    return ('口誤', '職場口誤')
                return ('口誤', '點餐/購物')
            return ('口誤', '職場口誤')
        return ('口誤', '職場口誤')

    # ── 口誤 > 點餐/購物 ─────────────────────────────────────────────────────
    ordering_ctx = has(t, '點餐', '超商', '便利商店', '飲料', '珍奶', '珍珠奶茶',
                        '夜市', '便當', '結帳', '買單', '外帶', '外送', '訂位',
                        '買早餐', '買午餐', '買飲料', '買東西', '購物', '買票',
                        '早餐店', '麵包店', '滷肉飯', '餐廳', '咖啡', '奶油', '美乃滋',
                        '鮮奶油', '結帳機', '自助', '刷卡', '付錢')
    if ordering_ctx and (is_slip or has(t, '不小心', '結果說', '結果講',
                                        '說成', '喊成', '叫成')):
        return ('口誤', '點餐/購物')

    # ── 口誤 > 腦袋當機 ───────────────────────────────────────────────────────
    brain_kw = ['腦袋空白', '沒睡好', '腦當機', '剛睡醒', '還沒睡醒',
                '才意識', '才反應', '自報名字', '說了自己', '說出自己',
                '沒反應過來', '腦子不轉', '腦袋當機', '太累', '睡眠不足',
                '說出自己名字', '周佳蓉', '自己的名字', '報了自己']
    if has(t, *brain_kw) or (is_slip and has(t, '自己名字', '名字', '報了', '說了自己')):
        return ('口誤', '腦袋當機')

    # Generic slip that doesn't fit above
    if is_slip and len(t) > 40:
        # Unknown context
        return ('口誤', None)

    # ── 認錯人 ────────────────────────────────────────────────────────────────
    mistaken_kw = ['認錯人', '誤認', '以為是', '以為他是', '以為妳是', '把他當',
                   '把她當', '把你當', '叫錯人', '認成', '弄錯人', '以為是同學',
                   '以為是朋友', '以為是室友', '以為是妹妹', '以為是老婆',
                   '完全不認識', '才發現不認識', '發現認錯', '發現弄錯']
    physical_kw = ['拍肩', '打', '抱', '推', '摸', '靠', '碰', '跳', '拉',
                   '搭肩', '抓住', '拍了', '打了', '踢', '踩', '坐上', '坐進',
                   '掐', '扯', '捏']
    mistaken = has(t, *mistaken_kw)

    # Also: boarded wrong car / got into wrong person's space and addressed them
    wrong_person_vehicle = has(t, '上車', '坐上去', '繫安全帶', '坐進去') and has(t, '陌生人', '不認識', '白色', '不是')
    if wrong_person_vehicle:
        return ('認錯人', '有肢體接觸')

    if mistaken:
        for pk in physical_kw:
            if pk in t:
                return ('認錯人', '有肢體接觸')
        return ('認錯人', '沒有肢體接觸')

    # Physical accidental contact with unknown person (grabbed/bumped stranger)
    accidental_contact = (
        has(t, '抓住', '拍了', '打了', '打到', '碰到', '撞到', '靠在', '摸到',
            '抓到', '握到') and
        has(t, '陌生人', '不認識', '轉過來', '回過頭', '完全不認識',
            '才發現', '才看到', '才注意', '路人', '旁邊的人', '女生', '男生',
            '一個人', '乘客')
    )
    if accidental_contact:
        return ('認錯人', '有肢體接觸')

    # ── 叫錯 ──────────────────────────────────────────────────────────────────
    # Called teacher mom
    if has(t, '老師') and has(t, '媽', '媽媽', 'mom', '哇媽') and (
        has(t, '叫成', '叫了', '叫出口', '叫錯', '喊成', '喊了', '叫了出來') or
        (has(t, '老師') and has(t, '媽') and len(t) < 100)
    ):
        return ('叫錯', '叫老師媽媽')

    # General called wrong name/title
    wrong_title_kw = ['叫錯', '叫成', '喊成', '喊成了', '喊錯']
    wrong_title_target = ['阿公', '阿嬤', '爺爺', '奶奶', '阿姨', '叔叔', '伯伯',
                          '爸爸', '媽媽', '男友', '女友', '老婆', '老公', '前任',
                          '老師', '同學', '阿姨']
    if has(t, *wrong_title_kw) and has(t, *wrong_title_target):
        return ('叫錯', None)

    # Called person wrong title without explicit "叫錯" word
    if has(t, '阿公您好', '阿嬤您好') and has(t, '爸', '媽', '哥', '姊', '叔', '伯'):
        return ('叫錯', None)
    # Called friend's sister "阿姨"
    if has(t, '阿姨') and has(t, '朋友') and has(t, '其實是', '是他姊', '是他妹', '跟我同'):
        return ('叫錯', None)

    # ── 走錯空間 ──────────────────────────────────────────────────────────────
    wrong_place_kw = ['走錯', '進錯', '推錯門', '開錯', '鑽進', '走進了', '衝進',
                      '走進去', '闖入', '闖進', '錯廁所', '進到錯', '坐錯位',
                      '坐到', '走到別人', '進了別人', '鑽入', '推開錯',
                      '走進別人', '坐了別人', '走錯廁所', '男廁', '女廁',
                      '鑽進去', '跑進去', '衝到', '走反']
    if has(t, *wrong_place_kw):
        return ('走錯空間', None)

    # Sat in interviewer's chair / wrong seat
    if has(t, '面試') and has(t, '坐下', '坐進', '坐了', '坐到', '坐在', '坐了過去'):
        return ('走錯空間', None)

    # Wrong lane in sports (bowling into neighbor's lane)
    if has(t, '保齡球', '球道') and has(t, '別人的', '隔壁', '丟到', '打到'):
        return ('走錯空間', None)

    # ── 以為在跟自己說話 ─────────────────────────────────────────────────────
    thought_me_kw = ['以為在跟我說話', '以為叫我', '誤以為叫我', '以為是叫我',
                     '以為是跟我', '以為在問我', '以為那是跟我', '以為是對我']
    for kw in thought_me_kw:
        if kw in t:
            if has(t, '店員', '服務員', '收銀員', '工作人員', '路人', '廣播'):
                return ('以為在跟自己說話', '以為店員在跟自己說話')
            return ('以為在跟自己說話', None)
    if has(t, '以為') and has(t, '叫我', '在叫我', '跟我說', '問我', '喊我'):
        if has(t, '店員', '服務員', '路人', '陌生人', '廣播', '廣告',
               '電話', '路邊', '隔壁'):
            return ('以為在跟自己說話', '以為店員在跟自己說話')
        return ('以為在跟自己說話', None)

    # ── 以為沒人亂講話 ────────────────────────────────────────────────────────
    no_one_kw = ['以為沒人', '偷說', '不知道有人', '沒想到有人', '被聽到', '被聽見',
                 '開擴音', '開免持', '外放', '耳機沒', '耳機忘', '忘了插耳機',
                 '沒戴耳機', '發現耳機', '耳機沒連', '耳機沒插',
                 '以為只有我', '以為只有我們', '以為沒有人聽得懂',
                 '以為聽不懂']
    if has(t, *no_one_kw):
        return ('以為沒人亂講話', None)

    # Chinese speakers abroad thinking no one understands
    if has(t, '以為沒人懂', '沒人聽得懂', '聽不懂中文', '聽懂中文') and has(t, '結果', '沒想到'):
        return ('以為沒人亂講話', None)
    if has(t, '說中文', '講中文', '中文分享', '中文聊', '台語聊') and has(t, '聽懂', '聽到', '回答', '搭話', '反應', '原來是', '台灣人', '懂中文', '台語'):
        return ('以為沒人亂講話', None)
    # Earphone / speaker situations
    if has(t, '全店', '整間', '整個', '全場') and has(t, '聽到', '聽見', '陪我', '一起') and has(t, '耳機', '音樂', '歌', '聲音'):
        return ('以為沒人亂講話', None)
    # Screamed in public thinking no one could hear
    if has(t, '減壓房', '隔音') and has(t, '大喊', '大叫', '喊了', '叫了', '外面', '聽得'):
        return ('以為沒人亂講話', None)

    # ── 當眾出糗 ─────────────────────────────────────────────────────────────
    kids_kw = ['小孩', '兒子', '女兒', '小朋友', '孩子', '小孩子', '寶寶', '小孩說',
               '小朋友說']
    kids_emb = ['說出', '問了', '大聲說', '大喊', '問道', '突然說', '指著', '講了',
                '說給', '告訴']
    if has(t, *kids_kw) and has(t, *kids_emb):
        return ('當眾出糗', '童言無忌')

    # Work / stage embarrassment
    work_emb = has(t, '工作', '打工', '上班', '工讀', '職場', '公司', '值班',
                   '主持', '婚宴', '演唱', '台上', '舞台', '主播', '直播',
                   '表演', '演出', '出差', '客戶面前', '老闆面前')
    pub_emb = has(t, '尷尬', '丟臉', '出糗', '全場', '大家都', '所有人',
                  '公開', '當眾', '大聲', '廣播', '全班', '全校', '忍住不笑',
                  '笑場', '忍不住笑', '沒忍住', '笑出來', '笑場', '社死現場',
                  '眾目睽睽', '搞笑', '超丟臉')

    if work_emb and pub_emb:
        return ('當眾出糗', '工作中')
    if work_emb and has(t, '出糗', '丟臉', '尷尬', '社死'):
        return ('當眾出糗', '工作中')

    # Generic public embarrassment with clear story
    if pub_emb and len(t) > 60:
        return ('當眾出糗', None)

    # Airport/public space name called out loudly
    if has(t, '大叫', '大喊', '喊了') and has(t, '安檢', '機場', '大廳', '捷運', '月台', '車站', '超市', '賣場', '百貨') and len(t) > 60:
        return ('當眾出糗', None)

    # 社死 in any context counts as 當眾出糗 if it's a personal story with length
    if has(t, '社死', '超級社死', '最社死', '社死現場') and len(t) > 80 and not has(t, '這篇', '分享', '留', '看著', '看完', '讀完'):
        return ('當眾出糗', None)

    # Embarrassing public situations
    pub_story = ['尷尬', '丟臉', '出糗', '當場', '超尷尬', '超丟臉', '場面很',
                 '全場沉默', '全場都', '在場所有', '轉身發現', '才發現是', '現場所有']
    if has(t, *pub_story) and len(t) > 80:
        return ('當眾出糗', None)

    # Romantic/social rejection or public mistake not covered above
    if has(t, '告白', '拒絕', '被拒絕') and has(t, '當眾', '全班', '全校', '大家',
                                                   '眾多', '在場', '很多人'):
        return ('當眾出糗', None)

    # Confession / bold move in public (even short stories)
    if has(t, '告白') and has(t, '拒絕', '然後', '班上', '學校', '公開', '很多人', '幾百人'):
        return ('當眾出糗', None)
    if has(t, '告白') and len(t) > 40:
        return ('當眾出糗', None)

    # Ordering without explicit slip word — said obviously wrong item
    if ordering_ctx and has(t, '結果說', '結果講', '結果喊', '說了', '說出',
                             '自信滿滿', '不小心', '才發現', '才意識', '才反應'):
        return ('口誤', '點餐/購物')

    # Stage slip — said wrong location/audience
    if stage_context and has(t, '桃園', '台北', '台中', '高雄', '台南', '花蓮',
                              '嘉義', '新竹', '基隆', '大家好', '朋友們',
                              '喊了', '喊出', '大喊', '喊道'):
        return ('口誤', '職場口誤')

    # Workplace conditioning — toddler care habits in adult setting
    if has(t, '托嬰', '幼稚園', '幼兒園', '保育', '小朋友') and has(t, 'No~', 'No No', '搖手指', '食指', '動作', '習慣'):
        return ('被工作/兵役制約', None)

    # Public situations with clear embarrassment
    if has(t, '全場', '全場都', '所有人', '大家都', '旁邊都') and has(t, '看我', '看著我', '看過來', '靜下來', '安靜了', '沉默'):
        return ('當眾出糗', None)

    # "妳要飯的嗎" type public call-outs (shouted in crowd)
    if has(t, '大喊', '大叫', '廣播', '喊道') and has(t, '人群', '排隊', '超市', '機場', '捷運', '月台', '廣場', '百貨', '全場') and len(t) > 60:
        return ('當眾出糗', None)

    # Language mix-up by someone else (observer shares classmate's story)
    if has(t, '語言', '外語', 'department store', '講成', '說成') and len(t) > 60:
        return ('口誤', '語言混亂')

    # English word mix-up abroad (car service/room service type)
    if has(t, '英文', '英語') and has(t, 'service', 'room', 'car', 'hello', '說', '練習') and has(t, '澳洲', '美國', '英國', '加拿大', '國外', '海外', '外國'):
        return ('口誤', '語言混亂')

    # Talked negatively about someone in their presence (overheard)
    if has(t, '空氣突然安靜', '一片安靜', '靜下來了', '瞬間安靜', '安靜了') and len(t) > 60:
        return ('以為沒人亂講話', None)

    # Physical slip into stranger (train/bus)
    if has(t, '跌入', '撞進', '跌進', '倒進', '撞上', '碰到') and has(t, '懷裡', '身上', '旁邊', '陌生', '乘客', '旁座', '男生', '女生') and len(t) > 50:
        return ('認錯人', '有肢體接觸')

    # Multiple incidents described (take first meaningful one or 當眾出糗)
    if t.count('1.') >= 1 and t.count('2.') >= 1 and len(t) > 80:
        return ('當眾出糗', None)

    # Work habit used in wrong context (childcare/medical habit)
    if has(t, '職業病', '工作慣了', '習慣了', '工作的時候') and has(t, '在家', '在朋友', '在外面', '在學校', '對陌生人', '對大人'):
        return ('被工作/兵役制約', None)

    # Personal item falls / drops in embarrassing public situation
    if has(t, '掉出來', '掉下來', '飛出去', '脫落', '掉落', '掉了') and has(t, '男生', '女生', '帥', '同學', '路人', '陌生人') and len(t) > 60:
        return ('當眾出糗', None)

    # Talking about someone in their presence (overheard)
    if has(t, '偷偷', '小聲', '私下', '背後') and has(t, '客人', '店員', '路人', '本人', '當事人', '對方', '他') and has(t, '聽到', '聽見', '聽懂', '剛好') and len(t) > 50:
        return ('以為沒人亂講話', None)

    # Sent wrong message / accidentally exposed
    if has(t, '傳錯', '傳到', '傳給') and has(t, '店員', '客戶', '主管', '老闆', '陌生人', '他的', '她的') and len(t) > 50:
        return ('以為沒人亂講話', None)

    # Body sounds in public transport or quiet space
    if has(t, '打呵欠', '打嗝', '放屁', '屁聲', '打噴嚏', '巨響', '大聲') and has(t, '捷運', '公車', '火車', '電車', '電梯', '安靜', '大家') and len(t) > 50:
        return ('當眾出糗', None)

    # Workplace product name said wrong (without explicit slip word)
    if work_context and has(t, '客人', '客戶', '不對', '才不是', '其實是', '應該是') and has(t, '說', '喊', '介紹') and len(t) > 50:
        return ('口誤', '職場口誤')

    # Called parent "grandfather/grandmother" in professional context (幼兒園/補習班)
    if has(t, '幼兒園', '托嬰', '補習班', '安親班') and has(t, '阿公', '阿嬤', '爺爺', '奶奶') and has(t, '爸', '媽', '是他', '其實是'):
        return ('叫錯', None)

    # Stopped at or approached a car thinking it was unoccupied
    if has(t, '停車格', '車格', '停車位', '路邊') and has(t, '車窗', '裡面', '有人', '人在') and len(t) > 40:
        return ('走錯空間', None)

    # Fall / stumble into stranger in transit
    if has(t, '跌', '滑', '撞', '摔') and has(t, '捷運', '公車', '火車', '電車', '月台', '車廂') and has(t, '懷裡', '身上', '旁座', '陌生', '男乘客', '女乘客') and len(t) > 50:
        return ('認錯人', '有肢體接觸')

    # 社死 with personal story (not a reaction)
    if has(t, '社死') and len(t) > 80 and not has(t, '這篇', '分享', '看這篇', '看完', '讀完', '跟你一樣', '我也是'):
        return ('當眾出糗', None)

    return ('其他', None)


def main():
    in_path  = os.path.join(BASE, 'data-v2', 'raw-scraped.json')
    out_path = os.path.join(BASE, 'data-v2', 'classified-new-replies.json')

    with open(in_path, encoding='utf-8') as f:
        raw = json.load(f)

    new_replies = raw['newReplies']
    classified = []
    cat_counter = Counter()

    for r in new_replies:
        cat, sub = classify(r['text'])
        r['category']    = cat
        r['subcategory'] = sub
        classified.append(r)
        cat_counter[cat] += 1

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(classified, f, ensure_ascii=False, indent=2)

    print(f"Classified {len(classified)} new replies → {out_path}")
    print("\nCategory breakdown:")
    for cat, n in cat_counter.most_common():
        print(f"  {n:4d}  {cat}")

    # Show 其他 samples for manual review
    others = sorted([r for r in classified if r['category'] == '其他'], key=lambda r: -r['likesNum'])
    print(f"\n其他 samples (top {min(30, len(others))} by likes):")
    for r in others[:30]:
        print(f"  {r['likes']:>6} | {r['text'][:100].replace(chr(10),' ')}")


if __name__ == '__main__':
    main()
