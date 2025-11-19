# 创建时间: 2025/10/17 14:40
# 版本: v2025.10-auto
# -*- coding: utf-8 -*-
"""
7.2_cleaning_log_merge.py（自动版）
--------------------------------------------------
功能：
自动遍历 BASE_DIR，收集并合并所有清洗与检测日志（CSV 格式），
输出统一的 master_cleaning_log.csv。

改进点：
1️⃣ 无需手动维护 LOG_PATHS；
2️⃣ 自动遍历 BASE_DIR 下所有 .csv 文件；
3️⃣ 仅选择文件名中包含 “6.”、“7.” 的日志；
4️⃣ 自动读取每个 CSV 的列头；
5️⃣ 输出文件中增加“来源文件”列；
6️⃣ 输出合并汇总信息（文件数量与条目总计）。
"""

import csv
from pathlib import Path
from datetime import datetime

# === 基础配置 ===
REGION = "yuzhongqu"  # 可被 update paths 自动替换
BASE_DIR = Path(r"I:\中国民间传统故事\分卷清洗") / REGION
OUTPUT_LOG = BASE_DIR / f"7.2_master_cleaning_log_{REGION}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"


def collect_csv_files(base_dir: Path):
    """遍历目录，收集符合条件的 CSV 文件"""
    csv_files = []
    for path in base_dir.glob("*.csv"):
        if any(tag in path.name for tag in ["6.", "7."]):
            csv_files.append(path)
    return sorted(csv_files)


def merge_logs():
    """合并所有 CSV 文件"""
    total_rows = 0
    merged_files = 0
    header_written = False

    csv_files = collect_csv_files(BASE_DIR)
    if not csv_files:
        print("⚠️ 未找到符合条件的 CSV 日志文件。")
        return

    with open(OUTPUT_LOG, "w", newline="", encoding="utf-8-sig") as out:
        writer = csv.writer(out)

        for p in csv_files:
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
            print(f"✅ 已合并: {p.name}")

    print("\n[SUMMARY] 日志合并完成")
    print(f"  合并文件数: {merged_files}")
    print(f"  总记录数: {total_rows}")
    print(f"[DONE] 输出文件: {OUTPUT_LOG}\n")


if __name__ == "__main__":
    print("=== 7.2 Cleaning Log Merge (Auto-Detect CSV) ===")
    merge_logs()
