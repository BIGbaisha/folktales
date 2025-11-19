# -*- coding: utf-8 -*-
# ETL_pipeline_2025.xx.xx_fix_first_meta_line.py
# ------------------------------------------------------------
# 目的：
#   将所有 H3 标题（### NNN. 标题）下面的第一条以 > 开头的行
#   从：
#       > 哈尼族
#   变成：
#       > 民族：哈尼族
# ------------------------------------------------------------

import re
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))
from utils.template_script_header_manual import (
    load_text, save_text, log_stage, log_summary
)

# ============================
# CONFIG
# ============================
INPUT_PATH  = Path(r"I:\中国民间传统故事\分卷清洗\yunnan\6.9_Chinese Folk Tales_yunnan.md")
OUTPUT_PATH = Path(r"I:\中国民间传统故事\分卷清洗\yunnan\6.10_Chinese Folk Tales_yunnan.md")

# H3：### 001. 标题
H3_RE = re.compile(r"^###\s+\d{1,3}\.\s*.*$")

# 以 > 开头的 meta 行
META_RE = re.compile(r"^>\s*(.*)$")


def process(text: str) -> str:
    lines = text.splitlines()

    out = []
    i = 0
    total = len(lines)

    while i < total:
        line = lines[i]

        # --- 匹配 H3 故事标题 ---
        if H3_RE.match(line):
            out.append(line)
            i += 1

            # 跳过 H3 后所有空行（关键修复）
            while i < total and lines[i].strip() == "":
                out.append(lines[i])  # ← 保留空行
                i += 1

            # 下一行必须是以 > 开头
            m = META_RE.match(lines[i])
            if m:
                original_val = m.group(1).strip()

                # 如果已经是 民族： 开头，不重复修改
                if original_val.startswith("民族"):
                    out.append(lines[i])  # 原样写回
                else:
                    # 修改为 > 民族：XXX
                    out.append(f"> 民族：{original_val}")

                i += 1
                continue

            # 否则不是 meta 行，不处理
            # 写回普通行
            out.append(lines[i])
            i += 1
            continue

        # --- 非 H3 行照抄 ---
        out.append(line)
        i += 1

    return "\n".join(out) + "\n"


def main():
    log_stage("读取文件")
    raw = load_text(INPUT_PATH)

    log_stage("处理标题下首个 meta 行")
    cleaned = process(raw)

    save_text(OUTPUT_PATH, cleaned)

    log_summary(str(INPUT_PATH), str(OUTPUT_PATH), {"task": "fix_first_meta_under_H3"})


if __name__ == "__main__":
    main()
