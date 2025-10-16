# 创建时间: 2025/10/15 14:20
# 版本: v2025.10
# -*- coding: utf-8 -*-
"""
7.2_cleaning_log_merge.py
--------------------------------------------------
功能：
手动维护 LOG_PATHS，合并多个清洗与检测日志（如 6.2、6.6、6.8、7.1、7.4），
输出统一的 master_cleaning_log.csv。
改进点：
1. 自动读取每个 CSV 的列头；
2. 在输出文件中增加“来源文件”列；
3. 生成汇总输出信息（文件数量与条目总计）。
"""

import csv
from pathlib import Path

# 手动维护日志文件路径
LOG_PATHS = [
    r"I:\中国民间传统故事\老黑解析版本\正式测试\6.2_char_freq.csv",
    r"I:\中国民间传统故事\老黑解析版本\正式测试\6.6_structure_warnings.csv",
    r"I:\中国民间传统故事\老黑解析版本\正式测试\6.8_paragraph_length_stats.csv",
    r"I:\中国民间传统故事\老黑解析版本\正式测试\7.1_final_clean_report.csv",
    ,
]

OUTPUT_LOG = r"I:\中国民间传统故事\老黑解析版本\正式测试\7.2_master_cleaning_log.csv"


def merge_logs():
    total_rows = 0
    merged_files = 0
    header_written = False

    with open(OUTPUT_LOG, "w", newline="", encoding="utf-8-sig") as out:
        writer = csv.writer(out)

        for path in LOG_PATHS:
            p = Path(path)
            if not p.exists():
                print(f"⚠️ 未找到 {p.name}，跳过。")
                continue

            with open(p, "r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if not header:
                    print(f"⚠️ 文件 {p.name} 为空或无表头。")
                    continue

                if not header_written:
                    writer.writerow(["来源文件"] + header)
                    header_written = True

                for row in reader:
                    writer.writerow([p.name] + row)
                    total_rows += 1

            merged_files += 1

    print("\n[SUMMARY] 日志合并完成")
    print(f"  合并文件数: {merged_files}")
    print(f"  总记录数: {total_rows}")
    print(f"[DONE] 输出文件: {OUTPUT_LOG}\n")


if __name__ == "__main__":
    print("=== 7.2 Cleaning Log Merge (Manual Paths) ===")
    merge_logs()
