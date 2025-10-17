# -*- coding: utf-8 -*-
# 创建时间: 2025/10/18
"""
=============================================================
标题等级梳理脚本（两阶段 + 预清洗版）
Version: 5_titles_normalize_final.py
-------------------------------------------------------------
阶段功能对照表
-------------------------------------------------------------
| 阶段 | 功能说明 | 是否实现 |
|------|-----------|-----------|
| 阶段0 | 清除所有旧标题符号 # | ✅ 已添加 |
| 阶段1 | 重新识别标题等级 | ✅ |
| 阶段2 | 检测 H4 之间的中文数字行 → H5 | ✅ |
| 阶段3 | 输出 & CSV | ✅ |
-------------------------------------------------------------
核心逻辑：
0️⃣ 阶段0：清除原有 Markdown 标题符号（#）
1️⃣ 阶段1：识别初步标题等级（H1~H4）
2️⃣ 阶段2：在确认的 H4 之间检测中文数字行 → 标记为 H5
3️⃣ 阶段3：生成新 Markdown 与统计 CSV（含 H5_between_H4）
=============================================================
"""

import os
import re
import csv

# ==========================================================
# 路径配置
# ==========================================================
INPUT_PATH    = r"I:\中国民间传统故事\分卷清洗\yunnan\Chinese Folk Tales_yunnan.md"
OUTPUT_TARGET = r"I:\中国民间传统故事\分卷清洗\yunnan\5_Chinese Folk Tales_yunnan.md"
CSV_PATH      = r"I:\中国民间传统故事\分卷清洗\yunnan\5_yunnan_heading_stats.csv"

DEBUG_SHOW_PER_LEVEL = 3

# ==========================================================
# 公共标点与空白
# ==========================================================
PUNCT_WS = r"\s,\.，。:：;；!！\?？·・—\-_\~`'\"“”‘’\(\)（）\[\]【】<>《》、…⋯．·"

# ==========================================================
# 模糊匹配构建函数
# ==========================================================
def build_fuzzy_regex(text: str) -> re.Pattern:
    core = re.sub(f"[{PUNCT_WS}]", "", text)
    if not core:
        return re.compile(r"^(?!)$")
    sep = f"[{PUNCT_WS}]*"
    pattern = rf"^\s*[{PUNCT_WS}]*" + sep.join(map(re.escape, core)) + rf"[{PUNCT_WS}]*\s*$"
    return re.compile(pattern)

# ==========================================================
# 标题匹配规则表
# ==========================================================
H1_TITLES = ["前言", "后记"]
H2_TITLES = ["神话", "传说", "故事"]
H3_TITLES = [
    "神话","传说","故事","开天辟地神话","自然天象神话","动物植物神话",
    "图腾祖先神话","洪水人类再繁衍神话","文化起源神话","神和英雄神话","英雄神话",
    "人物传说","三国蜀汉人物传说","文人传说","现代革命家传说","史事传说",
    "地方传说","名山传说","风俗传说","动物故事","幻想故事",
    "鬼狐精怪故事","生活故事","机智人物故事","寓言故事","笑话"
]

H1_PATTERNS = [build_fuzzy_regex(t) for t in H1_TITLES]
H2_PATTERNS = [build_fuzzy_regex(t) for t in H2_TITLES]
H3_PATTERNS = [build_fuzzy_regex(t) for t in H3_TITLES]

# ==========================================================
# 特定结构标题正则
# ==========================================================
ROM_NUMS = "一二三四五六七八九十百千零〇○"

RE_H2_NUM = re.compile(
    rf"^\s*(?:[（(]\s*[{ROM_NUMS}]+\s*[)）]|[{ROM_NUMS}]+[、\.．])\s*$"
)

H4_MAX_NUMBER = 750
RE_H4_NUM_TITLE = re.compile(
    rf"^\s*(?P<num>\d{{1,5}})\s*[{PUNCT_WS}]*\s*(?P<title>.*[\u4e00-\u9fa5].*?)\s*$"
)

RE_H5_RELAXED = re.compile(rf"^\s*[{PUNCT_WS}]*附")
RE_H5_NUMERIC = re.compile(rf"^\s*[（(]?\s*[{ROM_NUMS}]+\s*[)）]?\s*$")
RE_ALL_HASHES = re.compile(r"^\s{0,3}#{1,6}\s*")

# ==========================================================
# 阶段0：清除所有标题井号（#）
# ==========================================================
def remove_all_hash_marks(lines):
    """去除所有行首的 # 与多余空格"""
    cleaned = []
    for line in lines:
        new_line = RE_ALL_HASHES.sub("", line).lstrip()
        cleaned.append(new_line)
    return cleaned

# ==========================================================
# 阶段1：初步识别标题等级
# ==========================================================
def detect_initial_levels(lines):
    results = []
    for line in lines:
        raw = line.rstrip("\n")
        content = raw.strip()
        if not content:
            results.append({"level": None, "title": None, "text": line})
            continue

        lvl, title = None, None
        # H2：章节编号
        if RE_H2_NUM.match(content):
            lvl, title = 2, content
        # H4：数字 + 汉字
        else:
            m = RE_H4_NUM_TITLE.match(content)
            if m:
                num = int(m.group("num"))
                title_part = m.group("title")
                if num <= H4_MAX_NUMBER and len(title_part) <= 15:
                    lvl, title = 4, content

        # 固定标题匹配 H1~H3
        if not lvl:
            for p in H1_PATTERNS:
                if p.match(content):
                    lvl, title = 1, content
                    break
        if not lvl:
            for p in H2_PATTERNS:
                if p.match(content):
                    lvl, title = 2, content
                    break
        if not lvl:
            for p in H3_PATTERNS:
                if p.match(content):
                    lvl, title = 3, content
                    break

        results.append({"level": lvl, "title": title, "text": line})
    return results

# ==========================================================
# 阶段2：识别 H4 之间的中文数字小节为 H5
# ==========================================================
def refine_H5_between_H4(results):
    between_H4_count = 0
    for i in range(1, len(results) - 1):
        cur = results[i]
        prev_lvl = results[i - 1]["level"]
        next_lvl = results[i + 1]["level"]
        content = cur["text"].strip()

        # 附录类
        if len(content) < 10 and RE_H5_RELAXED.match(content):
            cur["level"] = 5
            cur["title"] = content
            continue

        # 夹在两个 H4 之间的中文数字行
        if RE_H5_NUMERIC.match(content) and prev_lvl == 4 and next_lvl == 4:
            cur["level"] = 5
            cur["title"] = content
            between_H4_count += 1
    return between_H4_count

# ==========================================================
# 阶段3：输出结果与统计
# ==========================================================
def export_results(results, between_H4_count):
    counts = {1:0, 2:0, 3:0, 4:0, 5:0}
    samples = {1:[], 2:[], 3:[], 4:[], 5:[]}
    out_lines = []

    for item in results:
        lvl, title, line = item["level"], item["title"], item["text"].rstrip("\n")
        if lvl:
            out_lines.append("#" * lvl + " " + title + "\n")
            counts[lvl] += 1
            if len(samples[lvl]) < DEBUG_SHOW_PER_LEVEL:
                samples[lvl].append(title)
        else:
            out_lines.append(line + "\n")

    os.makedirs(os.path.dirname(OUTPUT_TARGET) or ".", exist_ok=True)
    with open(OUTPUT_TARGET, "w", encoding="utf-8", newline="") as f:
        f.writelines(out_lines)

    rows = [{
        "file": os.path.basename(INPUT_PATH),
        "H1": counts[1],
        "H2": counts[2],
        "H3": counts[3],
        "H4": counts[4],
        "H5": counts[5],
        "H5_between_H4": between_H4_count,
        "TOTAL": sum(counts.values())
    }]

    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["file","H1","H2","H3","H4","H5","H5_between_H4","TOTAL"])
        writer.writeheader()
        writer.writerows(rows)

    summary = "，".join(
        [f"H{lvl}={counts[lvl]}（例：{'；'.join(samples[lvl])}）" for lvl in range(1,6) if counts[lvl]]
    )
    print(f"✅ 标题分析完成 | {summary} | H5_between_H4={between_H4_count}")
    print(f"📄 CSV: {CSV_PATH}")
    print(f"📝 输出文件: {OUTPUT_TARGET}")

# ==========================================================
# 主流程
# ==========================================================
def main():
    if not os.path.exists(INPUT_PATH):
        print(f"[ERROR] 文件不存在: {INPUT_PATH}")
        return

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    print("🧹 阶段0：清除原有 Markdown 标题符号…")
    lines = remove_all_hash_marks(lines)

    print("🚀 阶段1：检测初始标题等级…")
    results = detect_initial_levels(lines)

    print("🔍 阶段2：检测 H4 之间的中文数字小节…")
    between_H4_count = refine_H5_between_H4(results)

    print("💾 阶段3：生成输出文件与统计…")
    export_results(results, between_H4_count)

if __name__ == "__main__":
    main()
