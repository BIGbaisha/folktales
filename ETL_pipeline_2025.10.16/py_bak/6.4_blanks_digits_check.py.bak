# -*- coding: utf-8 -*-
# 2025-10-27
"""
检测正文中混杂中文出现的一位数字，并输出 CSV
------------------------------------------------
功能：
1️⃣ 检测正文中与中文混杂出现的单个数字（1–9）；
2️⃣ 不匹配 NO3、b5、a1、7.4、(1)、1.、1、3月 等；
3️⃣ 命中后记录所属最近标题（任意级别 #～######）；
4️⃣ 打印上下文；
5️⃣ 导出 CSV 文件；
6️⃣ 可选择清理模式或检测模式。
"""

import re
import csv
from pathlib import Path
from collections import defaultdict

# ===== 配置 =====
INPUT_PATH = r"I:\中国民间传统故事\分卷清洗\yunnan\6.4_Chinese Folk Tales_yunnan.md"
OUTPUT_PATH = r"I:\中国民间传统故事\分卷清洗\yunnan\6.4_Chinese Folk Tales_yunnan.md"
CSV_PATH = r"I:\中国民间传统故事\分卷清洗\yunnan\6.4_detected_single_digits.csv"

ONLY_DETECT = True   # True=仅检测并输出CSV；False=清理后写出新文件
# =================

# ========= 标题检测 =========
RE_HEADING = re.compile(r"^(#{1,6})\s*(.*)$")

# ========= 数字匹配规则 =========
# 排除小数、日期、序号（1.、1、(1)、（1）等）
RE_SINGLE_DIGIT = re.compile(
    r"""
    (?<![0-9A-Za-z])     # not preceded by letters or digits
    (?<!\d\.)            # not part of decimal (like 7.4)
    (?<![（(])           # not preceded by opening parenthesis （(
    ([1-9])              # single digit 1–9
    (?![)）])            # not followed by closing parenthesis ）)
    (?!\.\d)             # not part of decimal (like .4)
    (?![0-9A-Za-z])      # not followed by letters or digits
    (?![年月日])          # not followed by 年/月/日
    (?![、\.．])          # not followed by enumeration punctuation 、.．
    """,
    re.VERBOSE,
)

# Markdown结构符号豁免
RE_MD_PREFIX = re.compile(r"^\s*(?:[-*+]|\d{1,3}[.)]|>+)\s+")


def clean_line(line: str) -> str:
    """删除正文中一位数字及多余空格"""
    m = RE_MD_PREFIX.match(line)
    prefix = ""
    rest = line
    if m:
        prefix = m.group(0)
        rest = line[len(prefix):]

    rest = RE_SINGLE_DIGIT.sub("", rest)
    rest = re.sub(r"[ \t]+", " ", rest).strip()
    return prefix + rest


def analyze_text(text: str):
    """检测 + 清理 + 生成结果列表"""
    current_heading = "（无标题）"
    heading_digit_lines = defaultdict(list)
    cleaned_lines = []

    for lineno, line in enumerate(text.splitlines(), start=1):
        # ===== 标题识别 =====
        m = RE_HEADING.match(line)
        if m:
            level, title = len(m.group(1)), m.group(2).strip()
            current_heading = f"H{level} {title}"
            cleaned_lines.append(line)
            continue

        # ===== 检测数字 =====
        for m in RE_SINGLE_DIGIT.finditer(line):
            pos = m.start()
            start = max(0, pos - 5)
            end = min(len(line), pos + 6)
            context = line[start:end].replace("\n", "")
            heading_digit_lines[current_heading].append(
                (lineno, m.group(1), context, line.strip())
            )

        # ===== 清理逻辑 =====
        if ONLY_DETECT:
            cleaned_lines.append(line)
        else:
            cleaned_lines.append(clean_line(line))

    return cleaned_lines, heading_digit_lines


def export_csv(heading_digit_lines, path: Path):
    """输出检测结果到 CSV"""
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["所属标题", "行号", "命中数字", "上下文", "原始行"])
        for heading, items in heading_digit_lines.items():
            for ln, digit, context, snippet in items:
                writer.writerow([heading, ln, digit, context, snippet])
    print(f"\n🧾 已导出检测结果 CSV：{path}")


def print_summary(heading_digit_lines):
    """打印检测结果摘要"""
    total_hits = sum(len(v) for v in heading_digit_lines.values())
    print("====== 检测结果 ======")
    print(f"共检测到一位数字出现 {total_hits} 次\n")

    for heading, items in list(heading_digit_lines.items())[:10]:
        print(f"\n{heading} —— 出现 {len(items)} 次：")
        for ln, digit, context, snippet in items[:3]:
            print(f"  [行{ln}] {snippet}")
            print(f"           ↑ 数字: {digit} | 上下文: {context}")
        if len(items) > 3:
            print(f"  ……其余 {len(items)-3} 条省略")

    if len(heading_digit_lines) > 10:
        print(f"\n……其余 {len(heading_digit_lines)-10} 个标题省略")


def main():
    ip = Path(INPUT_PATH)
    if not ip.exists():
        raise FileNotFoundError(f"输入文件不存在：{ip}")

    text = ip.read_text(encoding="utf-8", errors="ignore")
    cleaned_lines, heading_digit_lines = analyze_text(text)

    print_summary(heading_digit_lines)
    export_csv(heading_digit_lines, Path(CSV_PATH))

    if ONLY_DETECT:
        print("\n🔍 当前为检测模式，仅打印并输出CSV，不修改原文件。")
    else:
        Path(OUTPUT_PATH).write_text("\n".join(cleaned_lines), encoding="utf-8")
        print(f"\n✅ 已清理后写出文件：{OUTPUT_PATH}")


if __name__ == "__main__":
    main()
