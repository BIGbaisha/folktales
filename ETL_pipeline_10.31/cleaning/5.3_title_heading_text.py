# -*- coding: utf-8 -*-
# year/month/day
# ETL_pipeline_10.31_clean_heading_text.py
# ------------------------------------------------------------
# 功能：
#   清洗所有级别标题（H1~H6）的标题内容，去除：
#   - 前后空格（全角/半角）
#   - 标题中夹杂的乱码（控制字符、不可见字符）
#   - 非法标点（全角点号、奇怪符号）
#   - 多余空格
#   - 标题编号前后的空格
#   标准化输出： "# 标题"、"### 001. 标题"
#   并输出 CSV 对照报告（原始标题 vs 清洗后）
# ------------------------------------------------------------

import re
import csv
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))
from utils.template_script_header_manual import (
    load_text, save_text, log_stage, log_summary
)
from utils.text_normalizer import normalize_chinese_text


# ============================
# CONFIG
# ============================
INPUT_PATH  = Path(r"I:\中国民间传统故事\分卷清洗\yunnan\6.8_Chinese Folk Tales_yunnan.md")
OUTPUT_PATH = Path(r"I:\中国民间传统故事\分卷清洗\yunnan\6.9_Chinese Folk Tales_yunnan.md")
CSV_PATH    = Path(r"I:\中国民间传统故事\分卷清洗\yunnan\5.3_heading_clean_report.csv")


# ============================
# 正则
# ============================

# 匹配 H1~H6
HEADING = re.compile(r"^(#{1,6})\s*(.*)$")

# 匹配故事编号标题：### 001. 标题
H3_PATTERN = re.compile(r"^(###)\s*(\d{1,3})\.\s*(.*)$")


# ============================
# 清洗函数
# ============================
def clean_title_text(s: str) -> str:
    """清洗标题内容"""

    # 全角 → 半角
    fw2hw = str.maketrans({
        '（': '(',
        '）': ')',
        '：': ':',
        '；': ';',
        '，': ',',
        '。': '.',
        '？': '?',
        '！': '!',
        '“': '"',
        '”': '"',
        '【': '[',
        '】': ']',
        '　': ' ',  # 全角空格
    })
    s = s.translate(fw2hw)

    # 去掉控制字符、不可见字符
    s = re.sub(r"[\u0000-\u001F\u007F\u0080-\u00A0]", "", s)

    # 去掉乱码符号
    s = re.sub(r"[·•●◆■★☆○◎※◇¤✦▣▓▒░►▼▌▍▶☉→←↑↓◉◐◑□]", "", s)

    # 去掉连续多个点号
    s = re.sub(r"\.{2,}", ".", s)

    # 统一空格
    s = re.sub(r"\s+", " ", s)

    return s.strip()


# ============================
# 主处理
# ============================
def process(text):
    lines = text.splitlines()
    new_lines = []
    csv_rows = []

    for idx, line in enumerate(lines):
        m = HEADING.match(line)

        # 非标题行
        if not m:
            new_lines.append(line)
            continue

        hashes, title = m.group(1), m.group(2)
        original_title = title

        # H3 with number
        mh3 = H3_PATTERN.match(line)
        if mh3:
            hashes = mh3.group(1)
            no = mh3.group(2).zfill(3)
            cleaned_title = clean_title_text(mh3.group(3))
            cleaned_line = f"{hashes} {no}. {cleaned_title}"

            # CSV 记录
            csv_rows.append([
                idx + 1,
                len(hashes),
                original_title,
                f"{no}. {cleaned_title}",
                "YES" if original_title != cleaned_title else "NO"
            ])

            new_lines.append(cleaned_line)
            continue

        # 普通标题
        cleaned_title = clean_title_text(title)
        cleaned_line = f"{hashes} {cleaned_title}"

        csv_rows.append([
            idx + 1,
            len(hashes),
            original_title,
            cleaned_title,
            "YES" if original_title != cleaned_title else "NO"
        ])

        new_lines.append(cleaned_line)

    return "\n".join(new_lines), csv_rows


# ============================
# MAIN
# ============================
def main():

    log_stage("读取 markdown")
    raw = load_text(INPUT_PATH)
    raw = normalize_chinese_text(raw)

    log_stage("清洗标题")
    out, csv_rows = process(raw)

    save_text(OUTPUT_PATH, out)
    log_stage(f"输出 → {OUTPUT_PATH}")

    # 写入 CSV
    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["line_no", "level", "original", "cleaned", "changed"])
        w.writerows(csv_rows)

    log_stage(f"CSV 报告 → {CSV_PATH}")

    log_summary(
        str(INPUT_PATH),
        str(OUTPUT_PATH),
        {"titles_cleaned": len(csv_rows)}
    )


if __name__ == "__main__":
    main()
# 创建时间: 2025/11/17 11:01
