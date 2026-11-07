#!/usr/bin/env python3
# AI 味评分器 · 硬指标自动扫描（通用版）
# 输出 JSON：硬指标分（封顶70）与各项命中明细。
# 用法：python3 score.py "<文本>"   或   echo "<文本>" | python3 score.py
import sys, re, json

# 通用塑料黑话 / 高频空词（命中 +3，可按账号增删）
BUZZWORD_REDLINE = ["赋能", "重塑", "杠杆", "底层", "维度"]

# humanizer 一级/二级禁用词（核心子集）
HARD_BANNED = [
    "仿佛", "犹如", "宛若", "如同", "一丝", "一抹", "些许", "几分", "隐约",
    "深吸一口气", "缓缓", "不禁", "微微", "轻轻", "淡淡",
    "眼中闪过", "嘴角勾起", "眉头微皱", "眉眼低垂", "瞳孔微缩",
    "心中一动", "心头一震", "心下了然", "心中暗道", "心底泛起", "不由得",
    "不容置疑", "不容置喙", "不易察觉", "显而易见", "毫无疑问", "不可否认",
    "坚定", "闪烁着光芒", "狡黠", "深邃", "凛冽", "冰冷",
    "自然而然", "情不自禁", "不由自主",
]

# 高频堆叠副词
STACK_ADV = ["极其", "极度", "极易", "极为", "猛地", "死死", "狠狠", "稳稳",
             "偏偏", "生生", "硬生生", "活生生", "瞬间", "下一秒", "那一秒",
             "立刻", "此刻", "此时", "紧接着", "骤然", "当场"]

# 连接词套话（只列明确套话；"首先/其次/最后/同时/随着"等常见词易误伤，
# 其"三段式"结构问题交由模型在 L2 评估，不在硬指标按单字计数）
CONNECT = ["此外", "值得注意的是", "需要指出的是", "不难发现", "综上所述",
           "总而言之", "一方面", "另一方面", "毋庸置疑",
           "不可否认", "在...的背景下", "从某种意义上说", "在当今", "至关重要",
           "深入探讨", "进一步来说", "换言之", "由此可见", "值得一提的是", "事实上",
           "不得不说", "坦率地说", "客观来讲", "众所周知"]

# 科普起手式
SCIENCE_OPENER = ["先说答案", "先给你一个结论", "掰开了揉碎了", "拆解", "你品一下",
                  "看明白了吗", "看到没有", "让我们来看看", "接下来让我们"]

# 自问自答老师腔
TEACHER_QA = ["这叫什么", "说明什么", "怎么办到的", "看明白了吗", "看到没有"]

# 你以为A实际上B
YOU_THINK = ["你以为"]

# 陈词滥调比喻
CLICHE_META = ["如沐春风", "梨花带雨", "命运的齿轮", "精准的手术刀", "如潮水般",
               "像一把刀", "稳稳地接住你"]


def _count(words, text):
    detail = {}
    for w in words:
        n = text.count(w)
        if n:
            detail[w] = n
    return detail, sum(detail.values())


def scan(text):
    hits = {}
    score = 0

    d, c = _count(BUZZWORD_REDLINE, text)
    hits["buzzword_redline"] = {"detail": d, "count": c, "weight": 3}
    score += c * 3

    d, c = _count(HARD_BANNED, text)
    hits["hard_banned"] = {"detail": d, "count": c, "weight": 2}
    score += c * 2

    # 标点违规
    punct = {}
    for ch, name in [("：", "全角冒号"), (":", "半角冒号"), ("——", "破折号"),
                     ("“", "左双引号"), ("”", "右双引号"), ('"', "半角双引号")]:
        n = text.count(ch)
        if n:
            punct[name] = n
    pcount = sum(punct.values())
    hits["punct_violation"] = {"detail": punct, "count": pcount, "weight": 3}
    score += pcount * 3

    # "不是A而是B"候选（不计入硬分，交由模型判毒）
    nb = len(re.findall(r"不是.{0,12}?(而是|是)", text))
    hits["not_but_candidate"] = {"count": nb, "weight": 5,
                                 "note": "候选，模型判毒后才 +5/处；好用法不计"}

    d, c = _count(STACK_ADV, text)
    hits["stack_adv"] = {"detail": d, "count": c, "weight": 1}
    score += c * 1

    d, c = _count(CONNECT, text)
    hits["connect_cliche"] = {"detail": d, "count": c, "weight": 1}
    score += c * 1

    d, c = _count(SCIENCE_OPENER, text)
    hits["science_opener"] = {"detail": d, "count": c, "weight": 3}
    score += c * 3

    d, c = _count(TEACHER_QA, text)
    hits["teacher_qa"] = {"detail": d, "count": c, "weight": 2}
    score += c * 2

    yt = text.count("你以为")
    hits["you_think"] = {"count": yt, "weight": 3}
    score += yt * 3

    d, c = _count(CLICHE_META, text)
    hits["cliche_metaphor"] = {"detail": d, "count": c, "weight": 3}
    score += c * 3

    score = min(score, 70)
    return score, hits


if __name__ == "__main__":
    text = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    score, hits = scan(text)
    out = {"hard_score_cap70": score, "hits": hits}
    print(json.dumps(out, ensure_ascii=False, indent=2))
