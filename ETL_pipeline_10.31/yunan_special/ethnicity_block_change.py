# -*- coding: utf-8 -*-
"""
功能：
1. 从 input 读取 md（不覆盖 input）
2. 将所有精确匹配  "> 哈尼族" 的行修改为 "> 民族: 哈尼族"
3. 只修改这一行，不动其它民族、不动其它 meta、不动正文
4. 将修改后的 markdown 输出到 output_path
5. 统计所有 H3 下的 ">" 行（修改与否）并输出 CSV

CSV 字段：
    h3_title, original_line, modified_line, line_number
"""

import re
import csv
from pathlib import Path

# ============ 你自己改路径：只读 input ==============
INPUT_PATH = Path(r"I:\中国民间传统故事\分卷清洗\yunnan\6.8_Chinese Folk Tales_yunnan.md")

# ============ 修改后输出到新文件（不会覆盖 input） =============
OUTPUT_PATH = Path(r"I:\中国民间传统故事\分卷清洗\yunnan\6.9_Chinese Folk Tales_yunnan.md")

# ============ CSV 输出路径 =============
CSV_PATH = Path(r"I:\中国民间传统故事\分卷清洗\yunnan\6.9_h3_gtag_changes.csv")

# 精确匹配 > 哈尼族 的行
MATCH_HANIZU = re.compile(r'^>\s*哈尼族\s*$', flags=re.MULTILINE)

# 判断是否已经是 “> 民族: xxx” 格式
MODIFIED_PATTERN = re.compile(r'^>\s*民族:\s*(.+)$')


def main():
    text = INPUT_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()

    new_lines = []
    results = []
    current_h3 = None

    for idx, line in enumerate(lines):

        # ---------------------------
        # 识别 H3 标题
        # ---------------------------
        m_h3 = re.match(r'^###\s+(.+)$', line)
        if m_h3:
            current_h3 = m_h3.group(1).strip()
            new_lines.append(line)
            continue

        stripped = line.strip()

        # ---------------------------
        # 统计任何 H3 下的 > 行
        # ---------------------------
        if stripped.startswith(">") and current_h3:

            original_line = stripped

            # 判断是否是目标替换行：> 哈尼族
            if MATCH_HANIZU.match(stripped):
                modified_line = "> 民族: 哈尼族"
                new_lines.append(modified_line)
            else:
                new_lines.append(line)
                modified_line = stripped if MODIFIED_PATTERN.match(stripped) else ""

            # 写入 CSV 记录
            results.append([
                current_h3,
                original_line,
                modified_line,
                idx + 1
            ])

            continue

        # 默认：原样写入
        new_lines.append(line)

    # ========== 写出新的 markdown，不覆盖 input ==========
    OUTPUT_PATH.write_text("\n".join(new_lines), encoding="utf-8")

    # ========== 输出 CSV ==========
    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["h3_title", "original_line", "modified_line", "line_number"])
        w.writerows(results)

    print("✔ 完成替换与统计")
    print("📄 修改后的 MD 输出 →", OUTPUT_PATH)
    print("📊 CSV 输出 →", CSV_PATH)
    print("📌 共发现", len(results), "条 H3 下的 '>' 行")


if __name__ == "__main__":
    main()
# 创建时间: 2025/11/14 15:09
