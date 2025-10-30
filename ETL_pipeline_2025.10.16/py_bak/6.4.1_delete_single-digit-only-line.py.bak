# -*- coding: utf-8 -*-
# 2025-10-27
"""
删除所有仅包含单个数字（1–9）的行，
即使该数字被 ** ** 或空格包围也会删除。
打印并导出这些行的所属标题、行号、原文到 CSV。
"""

import re
import csv
from pathlib import Path

# ===== 配置 =====
INPUT_PATH  = r"I:\中国民间传统故事\分卷清洗\yunnan\6.3_Chinese Folk Tales_yunnan.md"
OUTPUT_PATH = r"I:\中国民间传统故事\分卷清洗\yunnan\6.4_Chinese Folk Tales_yunnan.md"
CSV_PATH    = r"I:\中国民间传统故事\分卷清洗\yunnan\6.4.1_removed_single_digits.csv"
# =================

# 匹配标题（支持 # ~ ######）
RE_HEADING = re.compile(r"^(#{1,6})\s*(.*)$")

# 匹配整行只有一个数字（1–9），可被 **、空格、tab 包围
RE_SINGLE_DIGIT_LINE = re.compile(
    r"^\s*\**\s*([1-9])\s*\**\s*$"
)


def remove_single_digit_lines(text: str):
    """删除整行仅为单个数字（或 **数字**）的行，并打印和记录所属标题"""
    lines = text.splitlines()
    cleaned = []
    removed = []
    current_heading = "（无标题）"

    for lineno, line in enumerate(lines, 1):
        # 检测标题
        m = RE_HEADING.match(line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            current_heading = f"H{level} {title}" if title else f"H{level}"
            cleaned.append(line)
            continue

        # 检测是否为单数字行
        m_digit = RE_SINGLE_DIGIT_LINE.match(line)
        if m_digit:
            digit = m_digit.group(1)
            removed.append((current_heading, lineno, digit, line.strip()))
            continue

        cleaned.append(line)

    # 打印报告
    print("【检测报告】")
    if not removed:
        print("✅ 未发现独占一行的单个数字。")
    else:
        print(f"共删除 {len(removed)} 行：\n")
        for i, (heading, ln, digit, content) in enumerate(removed[:30], 1):
            print(f"{i:02d}. {heading} —— 行{ln}: {content}")
        if len(removed) > 30:
            print(f"……其余 {len(removed)-30} 行省略")

    return "\n".join(cleaned) + "\n", removed


def export_csv(removed, path: Path):
    """导出删除记录到 CSV"""
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["所属标题", "行号", "数字", "原始内容"])
        for heading, ln, digit, content in removed:
            writer.writerow([heading, ln, digit, content])
    print(f"\n🧾 已导出 CSV 报告：{path}")


def main():
    ip = Path(INPUT_PATH)
    if not ip.exists():
        raise FileNotFoundError(f"❌ 文件不存在: {INPUT_PATH}")

    text = ip.read_text(encoding="utf-8", errors="ignore")
    cleaned, removed = remove_single_digit_lines(text)

    Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)
    Path(OUTPUT_PATH).write_text(cleaned, encoding="utf-8")
    print(f"\n✅ 已输出清理后的文件：{OUTPUT_PATH}")

    if removed:
        export_csv(removed, Path(CSV_PATH))
    else:
        print("无数据需要导出。")


if __name__ == "__main__":
    main()
