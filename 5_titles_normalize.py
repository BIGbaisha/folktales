#  创建时间: 2025/10/10 15:55
## -*- coding: utf-8 -*-

"""
标题等级梳理（单文件输入），按新规则：
1) H5放宽：行长<10，且行首（可有空格/标点）出现“附” => 赋值为H5
2) 清除无效#：若不在规则表中的行，但源行含有#，则去掉所有开头的#并当作普通文本输出
3) 无视原#重新判级：先剥离行首#再匹配规则，命中则按新级别写回

同时：
- H1 合并定义
- H2 （一）（二）… 使用非惰性 '+'
- H4 放宽并新增限制：行首 1~5 位数字 +（分隔符可缺失或任意标点/空白）+ 标题文本，
  且“标题字数 ≤ 15”才命中；否则视为未命中，继续后续规则
- 统计各级标题数量到 CSV
"""

import os
import re
import csv

# ========== 硬编码路径（单文件） ==========
INPUT_PATH    = r"I:\中国民间传统故事\老黑解析版本\正式测试\Chinese Folk Tales_sichuan.md"        # 只填一个文件
OUTPUT_TARGET = r"I:\中国民间传统故事\老黑解析版本\正式测试\5_Chinese Folk Tales_sichuan_normalized.md"    # 目录 或 具体 .md
CSV_PATH      = r"I:\中国民间传统故事\老黑解析版本\正式测试\sichuan_heading_stats.csv"       # CSV 统计输出
# 自检：每级打印多少条命中示例
DEBUG_SHOW_PER_LEVEL = 3

# ========== 放宽匹配允许的空白/标点 ==========
PUNCT_WS = r"\s,\.，。:：;；!！\?？·・—\-_\~`'\"“”‘’\(\)（）\[\]【】<>《》、…⋯．·"

def build_fuzzy_regex(text: str) -> re.Pattern:
    """
    宽松匹配：在每个字符之间、以及行首/行尾都允许出现任意空白/常见标点。
    这样像 '·开天辟地神话·'、'——人物传说——' 也能命中。
    """
    core = re.sub(f"[{PUNCT_WS}]", "", text)
    if not core:
        return re.compile(r"^(?!)$")  # 永不匹配
    sep = f"[{PUNCT_WS}]*"
    pattern = rf"^\s*[{PUNCT_WS}]*" + sep.join(map(re.escape, core)) + rf"[{PUNCT_WS}]*\s*$"
    return re.compile(pattern)

# ========== 规则区 ==========
H1_TITLES = [
    "前言", "后记",
    "汉族","壮族","满族","回族","苗族","维吾尔族","土家族","彝族","蒙古族","藏族","布依族","侗族","瑶族",
    "朝鲜族","白族","哈尼族","哈萨克族","傣族","黎族","傈僳族","仡佬族","拉祜族","东乡族","佤族","水族",
    "纳西族","羌族","土族","仫佬族","锡伯族","柯尔克孜族","达斡尔族","景颇族","撒拉族","布朗族","毛南族",
    "塔吉克族","普米族","阿昌族","怒族","鄂温克族","京族","基诺族","德昂族","乌孜别克族","俄罗斯族","裕固族",
    "保安族","塔塔尔族","独龙族","鄂伦春族","赫哲族","门巴族","珞巴族","高山族"
]
H2_TITLES = ["神话", "传说", "故事"]
H3_TITLES = [
    "开天辟地神话","自然天象神话","动物植物神话","动植物神话",
    "图腾祖先神话","洪水、人类再繁衍神话","文化起源神话","神和英雄神话",
    "人物传说","三国蜀汉人物传说","文人传说","现代革命家传说",
    "史事传说","地方传说","名山传说","丰都鬼城传说",
    "动植物传说","土特产传说","民间工艺传说","风俗传说",
    "动物故事","幻想故事","鬼狐精怪故事","生活故事","机智人物故事","寓言故事","笑话",
]

H1_PATTERNS = [build_fuzzy_regex(t) for t in H1_TITLES]
H2_PATTERNS = [build_fuzzy_regex(t) for t in H2_TITLES]
H3_PATTERNS = [build_fuzzy_regex(t) for t in H3_TITLES]

# H2：（一）（二）……（仅该序号一行）——非惰性 '+'
ROM_NUMS = "一二三四五六七八九十百千零〇○"
RE_H2_NUM = re.compile(rf"^\s*[（(]\s*[{ROM_NUMS}]+\s*[)）]\s*$")

# ===== H4：放宽并新增“标题 ≤ 15 字”限制 =====
# 先捕获：行首 1~5 位数字 +（可选分隔符：允许为空或任意标点/空白）+ 标题主体
# 使用命名组 'title' 以便统计标题字数
RE_H4_NUM_TITLE = re.compile(rf"^\s*\d{{1,5}}\s*(?:[{PUNCT_WS}]*)\s*(?P<title>.+?)\s*$")

# H5 放宽：行首（可有空格/标点）+ “附”，且整行长度 < 10
RE_H5_RELAXED = re.compile(rf"^\s*[{PUNCT_WS}]*附")

# 去掉行首已有的 Markdown 井号（全部去掉）
RE_ALL_LEADING_HASHES = re.compile(r"^\s{0,3}#{1,6}\s*")

def strip_all_leading_hashes(text: str) -> str:
    s = text
    while True:
        new = RE_ALL_LEADING_HASHES.sub("", s, count=1)
        if new == s:
            return s.strip()
        s = new

def visible_text(line: str) -> str:
    return line.strip()

def count_title_chars(s: str) -> int:
    """统计标题字数：去掉空白与常见标点后计数。"""
    return len(re.sub(f"[{PUNCT_WS}]", "", s))

def match_level(line: str):
    """
    返回 (level, title_text, had_hash) 或 (None, None, had_hash)
    级别：H1=1, H2=2, H3=3, H4=4, H5=5
    逻辑：
      - 记录原行是否带有#
      - 用“剥离#后的内容”参与规则匹配
      - H5优先判断放宽规则（附 开头 + 行长<10）
      - H4：数字+标题 且 标题字数 ≤ 15 才命中
    """
    raw = line.rstrip("\n")
    had_hash = bool(re.match(r"^\s*#", raw))

    # 用于匹配的内容：剥离行首所有#
    content = strip_all_leading_hashes(raw)
    if not content.strip():
        return None, None, had_hash

    # H5 放宽：以“附”开头（允许前导空白/标点），行总长度<10（包含空格标点）
    if len(raw) < 10 and RE_H5_RELAXED.match(content):
        return 5, visible_text(content), had_hash

    # （一）（二）……
    if RE_H2_NUM.match(content):
        return 2, visible_text(content), had_hash

    # H4：数字 + 标题（标题字数 ≤ 15 才命中）
    m_h4 = RE_H4_NUM_TITLE.match(content)
    if m_h4:
        title_part = m_h4.group("title")
        if count_title_chars(title_part) <= 15:
            return 4, visible_text(content), had_hash
        # 否则视为未命中 H4，继续下面规则

    # H1 固定标题/民族名
    for p in H1_PATTERNS:
        if p.match(content):
            return 1, visible_text(content), had_hash

    # H2 固定标题
    for p in H2_PATTERNS:
        if p.match(content):
            return 2, visible_text(content), had_hash

    # H3 列表
    for p in H3_PATTERNS:
        if p.match(content):
            return 3, visible_text(content), had_hash

    return None, None, had_hash

def normalize_text(lines):
    """对一组文本行进行标题规范化，返回（新文本、计数dict、示例dict）"""
    counts = {1:0, 2:0, 3:0, 4:0, 5:0}
    samples = {1:[], 2:[], 3:[], 4:[], 5:[]}
    out_lines = []

    for line in lines:
        lvl, title, had_hash = match_level(line)
        raw = line.rstrip("\n")
        if lvl:
            out_lines.append("#" * lvl + " " + title + "\n")
            counts[lvl] += 1
            if len(samples[lvl]) < DEBUG_SHOW_PER_LEVEL:
                samples[lvl].append(title)
        else:
            # 不在规则表命中，但原行含# => 取消#（做普通文本）
            if had_hash:
                plain = strip_all_leading_hashes(raw)
                out_lines.append(plain + "\n")
            else:
                out_lines.append(line)

    return "".join(out_lines), counts, samples

def main():
    if not os.path.isfile(INPUT_PATH):
        print(f"未找到输入文件：{INPUT_PATH}")
        return

    base = os.path.basename(INPUT_PATH)

    # 判断 OUTPUT_TARGET 是目录还是 .md 文件
    if OUTPUT_TARGET.lower().endswith(".md"):
        out_path = OUTPUT_TARGET
    else:
        os.makedirs(OUTPUT_TARGET, exist_ok=True)
        out_path = os.path.join(OUTPUT_TARGET, base)  # 用输入同名写出

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_text, counts, samples = normalize_text(lines)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        f.write(new_text)

    # 自检输出
    hit_parts = []
    for lvl in (1,2,3,4,5):
        n = counts[lvl]
        if n:
            eg = "；".join(samples[lvl])
            hit_parts.append(f"H{lvl}={n}" + (f"（例：{eg}）" if eg else ""))
    hits = "，".join(hit_parts) if hit_parts else "无命中"
    print(f"✅ {base} => {os.path.basename(out_path)} | {hits}")

    # 写CSV（当前文件+总计）
    rows = [{
        "file": base,
        "H1": counts[1],
        "H2": counts[2],
        "H3": counts[3],
        "H4": counts[4],
        "H5": counts[5],
        "TOTAL": sum(counts.values())
    },{
        "file": "TOTAL",
        "H1": counts[1],
        "H2": counts[2],
        "H3": counts[3],
        "H4": counts[4],
        "H5": counts[5],
        "TOTAL": sum(counts.values())
    }]
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["file","H1","H2","H3","H4","H5","TOTAL"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"📄 统计CSV已生成：{CSV_PATH}")
    print(f"📝 输出文件：{out_path}")

if __name__ == "__main__":
    main()
