# -*- coding: utf-8 -*-
# 创建时间: 2025/10/24
"""
=============================================================
标题等级梳理脚本（逐行识别版 + 修正版加粗逻辑）
Version: ETL_pipeline_2025.10.24/5_titles_normalize_v11.py
=============================================================

功能概述：
-------------------------------------------------------------
1. 按行识别 H1~H4；
2. 若行首带单个 # 但不在 H1 规则中（前言、后记、神话、传说、故事），
   且未被识别为 H1~H4 标题 → 去掉 # 并加粗 **...**；
3. 输出规范化 Markdown、统计表与加粗明细表（始终生成两份 CSV）。
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
CSV_EMPH_PATH = r"I:\中国民间传统故事\分卷清洗\yunnan\5_yunnan_emphasized_h1.csv"

DEBUG_SHOW_PER_LEVEL = 3

# ==========================================================
# 公共符号
# ==========================================================
PUNCT_WS = r"\s,\.，。:：;；!！\?？·・—\-_\~`'\"“”‘’\(\)（）\[\]【】<>《》、…⋯．·"
ROM_NUMS = "一二三四五六七八九十百千零〇○"
RE_ALL_HASHES = re.compile(r"^\s{0,3}#{1,6}\s*")

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
# 标题匹配规则
# ==========================================================
H1_TITLES = ["前言", "后记", "神话", "传说", "故事"]
H2_TITLES = [
    "开天辟地神话","自然天象神话","动物植物神话","动植物神话","图腾祖先神话","祖先神话","天体自然神话",
    "洪水人类再繁衍神话","文化起源神话","神和英雄神话","英雄神话",
    "人物传说","三国蜀汉人物传说","文人传说","现代革命家传说",
    "史事传说","地方传说","名山传说","风俗传说","动植物传说","动物植物传说","丰都鬼城传说",
    "土特产传说","民间工艺传说",
    "动物故事","幻想故事","鬼狐精怪故事","生活故事",
    "机智人物故事","寓言故事","笑话","寓言"
]

H1_PATTERNS = [build_fuzzy_regex(t) for t in H1_TITLES]
H2_PATTERNS = [build_fuzzy_regex(t) for t in H2_TITLES]
RE_H3_NUM_TITLE = re.compile(rf"^\s*(?P<num>\d{{1,5}})\s*[{PUNCT_WS}]*\s*(?P<title>.*[\u4e00-\u9fa5].*?)\s*$")
RE_H4_APPENDIX = re.compile(rf"^\s*[{PUNCT_WS}]*(附记|附[:：])")

# ==========================================================
# 清理函数
# ==========================================================
def clean_lines(lines):
    return [line.rstrip("\n") + "\n" for line in lines]

# ==========================================================
# 标题识别函数
# ==========================================================
def detect_headings(lines):
    results = []
    for line in lines:
        text = line.rstrip("\n")
        stripped = text.strip()
        if not stripped:
            results.append({"level": None, "title": None, "text": line})
            continue

        core = RE_ALL_HASHES.sub("", stripped)
        lvl, title = None, None

        # H1
        for p in H1_PATTERNS:
            if p.match(core):
                lvl, title = 1, core
                break

        # H2
        if not lvl:
            for p in H2_PATTERNS:
                if p.match(core):
                    lvl, title = 2, core
                    break

        # H3
        if not lvl:
            m = RE_H3_NUM_TITLE.match(core)
            if m:
                num = int(m.group("num"))
                title_part = m.group("title")
                if num <= 750 and len(title_part) <= 15:
                    lvl, title = 3, core

        # H4 附类
        if not lvl and RE_H4_APPENDIX.match(core):
            lvl, title = 4, core

        results.append({"level": lvl, "title": title, "text": line})
    return results

# ==========================================================
# 修正版：带单个#且不匹配H1规则 → 加粗
# ==========================================================
def emphasize_unmatched_h1(results):
    emphasized = []
    for item in results:
        line = item["text"].rstrip("\n")

        # 原始行为单个#
        if re.match(r"^\s*#(?!#)", line):
            core = re.sub(r"^\s*#\s*", "", line).strip()
            matched_h1 = any(p.match(core) for p in H1_PATTERNS)
            # 若行未被识别为任何标题或不是合法H1
            if (not item["level"]) or (item["level"] == 1 and not matched_h1):
                item["text"] = f"**{core}**\n"
                item["level"] = None
                emphasized.append(core)

    return results, emphasized

# ==========================================================
# 输出与统计
# ==========================================================
def export_results(results, emphasized):
    counts = {1:0, 2:0, 3:0, 4:0}
    samples = {1:[], 2:[], 3:[], 4:[]}
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
    with open(OUTPUT_TARGET, "w", encoding="utf-8") as f:
        f.writelines(out_lines)

    # 输出两个 CSV（始终生成）
    rows = [{
        "file": os.path.basename(INPUT_PATH),
        "H1": counts[1],
        "H2": counts[2],
        "H3": counts[3],
        "H4": counts[4],
        "Emphasized_H1": len(emphasized),
        "TOTAL": sum(counts.values())
    }]
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["file","H1","H2","H3","H4","Emphasized_H1","TOTAL"])
        writer.writeheader()
        writer.writerows(rows)

    # 第二个CSV即使为空也生成
    with open(CSV_EMPH_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Emphasized_H1_Text"])
        for t in emphasized:
            writer.writerow([t])

    summary = "，".join([f"H{lvl}={counts[lvl]}（例：{'；'.join(samples[lvl])}）" for lvl in range(1,5) if counts[lvl]])
    print(f"✅ 标题识别完成 | {summary} | 加粗H1={len(emphasized)}")
    print(f"📄 统计文件: {CSV_PATH}")
    print(f"📑 加粗H1明细: {CSV_EMPH_PATH}")
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

    print("🚀 阶段1：逐行识别 H1~H4 …")
    results = detect_headings(clean_lines(lines))

    print("✨ 阶段2：处理带#但不在H1规则的行 → 加粗 …")
    results, emphasized = emphasize_unmatched_h1(results)

    print("💾 阶段3：输出 Markdown 与 CSV …")
    export_results(results, emphasized)

if __name__ == "__main__":
    main()
