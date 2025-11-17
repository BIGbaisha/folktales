# -*- coding: utf-8 -*-
# ETL_pipeline_2025.xx.xx_insert_ethnic_block.py
# ------------------------------------------------------------
# 目的：
#   对所有 H3（###）标题下的 “> 地点:XXX” 后
#   紧贴插入一行：
#       > 民族：汉族
#   （不留空行）
#   若已有民族行则不重复插入
# ------------------------------------------------------------

import re
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))
from utils.template_script_header_manual import load_text, save_text, log_stage, log_summary

# ============================
# CONFIG
# ============================
INPUT_PATH  = Path(r"I:\中国民间传统故事\分卷清洗\yuzhongqu\6.7_Chinese Folk Tales_yuzhongqu.md")
OUTPUT_PATH = Path(r"I:\中国民间传统故事\分卷清洗\yuzhongqu\6.8_Chinese Folk Tales_yuzhongqu.md")

# H3 标题
H3_RE = re.compile(r"^###\s+\d{1,3}\.\s*.*$")

# 匹配地点 meta 行
LOC_RE = re.compile(r"^>\s*地点[:：]\s*(.*)$")

# 匹配民族 meta 行
ETH_RE = re.compile(r"^>\s*民族[:：]")


def process(text: str) -> str:
    lines = text.splitlines()
    out = []
    i = 0
    total = len(lines)

    while i < total:
        line = lines[i]

        # ------------------------
        # 匹配 H3 标题
        # ------------------------
        if H3_RE.match(line):
            out.append(line)
            i += 1

            # 跳过标题后的空行（保留）
            while i < total and lines[i].strip() == "":
                out.append(lines[i])
                i += 1

            # 现在必须找“> 地点”行
            if i < total and LOC_RE.match(lines[i]):
                loc_line = lines[i]
                out.append(loc_line)
                i += 1

                # 如果下一行已经是民族行 → 不重复插入
                if i < total and ETH_RE.match(lines[i]):
                    out.append(lines[i])
                    i += 1
                    continue

                # 否则插入民族：汉族（不留空行）
                out.append("> 民族:汉族")
                continue

            # 非地点行 → 原样写回
            out.append(lines[i])
            i += 1
            continue

        # ------------------------
        # 非 H3 行直接写回
        # ------------------------
        out.append(line)
        i += 1

    return "\n".join(out) + "\n"


def main():
    log_stage("读取文件")
    raw = load_text(INPUT_PATH)

    log_stage("插入民族行")
    fixed = process(raw)

    save_text(OUTPUT_PATH, fixed)
    log_summary(INPUT_PATH, OUTPUT_PATH, {"task": "insert_ethnic_after_location"})


if __name__ == "__main__":
    main()
# 创建时间: 2025/11/17 11:32
