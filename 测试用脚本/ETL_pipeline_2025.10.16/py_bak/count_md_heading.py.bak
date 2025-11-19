# 创建时间: 2025/10/24 9:31
# -*- coding: utf-8 -*-
# 创建时间: 2025/10/24
"""
=============================================================
Markdown 标题统计脚本
Version: 2025.10.24/count_md_headings.py
=============================================================
功能说明：
-------------------------------------------------------------
统计指定 Markdown 文件中各级标题数量（H1~H6）。
输出结果保存为 CSV 文件。
"""

import os
import re
import csv

# ==========================================================
# 路径设置（修改成你的文件路径）
# ==========================================================
INPUT_PATH = r"I:\中国民间传统故事\分卷清洗\yunnan\5_Chinese Folk Tales_yunnan.md"
OUTPUT_CSV = r"I:\中国民间传统故事\分卷清洗\yunnan\heading_count_summary.csv"

# ==========================================================
# 正则匹配：行首 # 识别标题等级
# ==========================================================
RE_HEADING = re.compile(r"^\s{0,3}(#{1,6})\s*(.*)")

# ==========================================================
# 主函数
# ==========================================================
def count_headings(md_path):
    counts = {i: 0 for i in range(1, 7)}

    with open(md_path, "r", encoding="utf-8") as f:
        for line in f:
            match = RE_HEADING.match(line)
            if match:
                level = len(match.group(1))
                if 1 <= level <= 6:
                    counts[level] += 1

    total = sum(counts.values())
    return counts, total

# ==========================================================
# 输出 CSV
# ==========================================================
def export_csv(counts, total, out_csv, source_file):
    rows = [{
        "file": os.path.basename(source_file),
        "H1": counts[1],
        "H2": counts[2],
        "H3": counts[3],
        "H4": counts[4],
        "H5": counts[5],
        "H6": counts[6],
        "TOTAL": total
    }]

    os.makedirs(os.path.dirname(out_csv) or ".", exist_ok=True)
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["file", "H1", "H2", "H3", "H4", "H5", "H6", "TOTAL"]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ 标题统计完成：{os.path.basename(source_file)}")
    print(f"📄 H1={counts[1]}, H2={counts[2]}, H3={counts[3]}, H4={counts[4]}, H5={counts[5]}, H6={counts[6]}")
    print(f"📊 总计 {total} 个标题")
    print(f"💾 CSV 文件: {out_csv}")

# ==========================================================
# 主执行
# ==========================================================
def main():
    if not os.path.exists(INPUT_PATH):
        print(f"[ERROR] 文件不存在: {INPUT_PATH}")
        return

    counts, total = count_headings(INPUT_PATH)
    export_csv(counts, total, OUTPUT_CSV, INPUT_PATH)

if __name__ == "__main__":
    main()
