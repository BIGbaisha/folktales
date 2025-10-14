# 创建时间: 2025/10/14 12:36
# -*- coding: utf-8 -*-
"""
Markdown 文本分析 + 清理：
1) 检测：
   - 非标题行空格总数；
   - 非标题行中一位数字出现次数；
   - 统计这些数字所在的 H4 段落并打印；
2) 清理（可选）：
   - 删除正文中多余空格（除 markdown 结构符号后）；
   - 删除正文中出现的一位数字；
3) 通过 ONLY_DETECT 开关控制是否执行清理写出。
"""

import re
from pathlib import Path
from collections import defaultdict

# ===== 修改为你的文件路径 =====
INPUT_PATH = r"I:\中国民间传统故事\老黑解析版本\正式测试\6.3_Chinese Folk Tales_sichuan_cleaned.md"
OUTPUT_PATH = r"I:\中国民间传统故事\老黑解析版本\正式测试\6.4_Chinese Folk Tales_sichuan_cleaned.md"
# 是否只检测，不输出清理结果文件
ONLY_DETECT = True   # True=仅检测；False=检测并写出清理文件
# ============================

# 正则
RE_HEADING = re.compile(r"^#")
RE_H4 = re.compile(r"^(####)\s*(.*)$")
RE_SINGLE_DIGIT = re.compile(r"\b\d\b")
# Markdown 结构符号前缀（空格清理豁免区）
RE_MD_PREFIX = re.compile(r"^\s*(?:[-*+]|\d{1,3}[.)]|>+)\s+")

def clean_line(line: str) -> str:
    """
    清理正文行：
    1. 删除多余空格（除 markdown 符号后的空格）
    2. 删除一位数字（1–9）
    """
    m = RE_MD_PREFIX.match(line)
    prefix = ""
    rest = line
    if m:
        prefix = m.group(0)
        rest = line[len(prefix):]

    # 删除一位数字
    rest = RE_SINGLE_DIGIT.sub("", rest)

    # 删除多余空格
    rest = re.sub(r"[ \t]+", " ", rest).strip()

    return prefix + rest


def analyze_text(text: str):
    space_count = 0
    digit_count = 0
    line_count = 0

    current_h4 = "（无H4标题）"
    h4_digit_lines = defaultdict(list)
    cleaned_lines = []

    for lineno, line in enumerate(text.splitlines(), start=1):
        # 标题检测
        if RE_HEADING.match(line):
            m4 = RE_H4.match(line)
            if m4:
                current_h4 = m4.group(2).strip()
            cleaned_lines.append(line)
            continue

        # ---- 检测阶段 ----
        line_count += 1
        space_count += line.count(" ")
        digits = RE_SINGLE_DIGIT.findall(line)
        if digits:
            digit_count += len(digits)
            snippet = line.strip()
            if len(snippet) > 80:
                snippet = snippet[:80] + "..."
            h4_digit_lines[current_h4].append((lineno, snippet))

        # ---- 清理阶段 ----
        if ONLY_DETECT:
            cleaned_lines.append(line)
        else:
            cleaned_line = clean_line(line)
            cleaned_lines.append(cleaned_line)

    # 输出检测结果
    print("====== 检测结果 ======")
    print(f"非标题行总数：{line_count}")
    print(f"非标题行空格总数：{space_count}")
    print(f"非标题行一位数字(1–9)出现次数：{digit_count}")
    print("======================")

    if h4_digit_lines:
        print("\n====== 一位数字出现位置（按H4分组） ======")
        for h4_title, lines in h4_digit_lines.items():
            print(f"\n#### {h4_title}  —— 出现 {len(lines)} 次：")
            for ln, snippet in lines:
                print(f"  [行{ln}] {snippet}")
    else:
        print("\n未检测到正文中出现一位数字的行。")

    # 是否写出清理后的文本
    if not ONLY_DETECT:
        Path(OUTPUT_PATH).write_text("\n".join(cleaned_lines), encoding="utf-8")
        print("\n✅ 已输出清理后文件：", OUTPUT_PATH)
    else:
        print("\n🔍 当前为“仅检测”模式，不写出清理文件。")


def main():
    ip = Path(INPUT_PATH)
    if not ip.exists():
        raise FileNotFoundError(f"输入文件不存在：{ip}")
    text = ip.read_text(encoding="utf-8", errors="ignore")
    analyze_text(text)

if __name__ == "__main__":
    main()
