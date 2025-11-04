# ============================================================
# 文件名称: text_consistency_check.py
# 版本日期: 2025-10-17
# ============================================================
# 【功能说明】
# ------------------------------------------------------------
# 本脚本用于在“中国民间传统故事”文本清洗流水线中，
# 对比相邻两个 Markdown 文件（如 6.2 → 6.3）之间的结构
# 差异，检测章节标题（以 # 开头行）的新增与缺失情况，
# 并输出一致性检测报告。
#
# 【使用场景】
# ------------------------------------------------------------
# 本脚本可独立运行，也可被 run_pipeline.py 自动调用。
# 若通过命令行参数传入 input_old / input_new / region，
# 则以指定文件对比；否则自动检测 BASE_DIR 下最新两份文件。
#
# 【核心功能】
# ------------------------------------------------------------
# 1️⃣ 自动提取 Markdown 文本中的标题行（#、##、### 等）；
# 2️⃣ 比较前后版本标题集合的差异；
# 3️⃣ 输出 CSV 报告，记录“缺失/新增”标题；
# 4️⃣ 自动生成报告文件名，含地区名与时间戳；
# 5️⃣ 支持命令行参数调用模式（适配 run_pipeline.py）；
# 6️⃣ 无法找到输入文件时自动提示。
#
# 【路径规则】
# ------------------------------------------------------------
# BASE_DIR = I:\中国民间传统故事\分卷清洗\<REGION>\
# Markdown 文件命名格式：
#   6.x_Chinese Folk Tales_<REGION>.md
# 报告文件命名格式：
#   consistency_report_<REGION>_<版本名>_<时间戳>.csv
#
# 【示例】
# ------------------------------------------------------------
# 独立运行：
#   > python text_consistency_check.py
#
# 自动运行（由 run_pipeline 调用）：
#   > python text_consistency_check.py \
#         --input_old "...\6.2_Chinese Folk Tales_yuzhongqu.md" \
#         --input_new "...\6.3_Chinese Folk Tales_yuzhongqu.md" \
#         --region "yunnan"
#
# ============================================================

import argparse
from pathlib import Path
from datetime import datetime
import csv
import re
import sys


# === 命令行参数解析 ===
parser = argparse.ArgumentParser(description="检测 Markdown 文件结构一致性（章节标题差异）")
parser.add_argument("--input_old", type=str, help="上一版本文件路径")
parser.add_argument("--input_new", type=str, help="当前版本文件路径")
parser.add_argument("--region", type=str, default="yunnan", help="地区名（默认 yunnan）")
args = parser.parse_args()

# === 基础路径设置 ===
REGION = args.region
BASE_DIR = Path(r"I:\中国民间传统故事\分卷清洗") / REGION

# 若未传入参数，则自动检测最新两个文件
if args.input_old and args.input_new:
    INPUT_OLD = Path(args.input_old)
    INPUT_NEW = Path(args.input_new)
else:
    files = sorted(BASE_DIR.glob("6.*_Chinese Folk Tales_*.md"))
    if len(files) < 2:
        print("❌ 未找到至少两份可比较的 Markdown 文件。")
        sys.exit(1)
    INPUT_OLD, INPUT_NEW = files[-2], files[-1]

# 输出路径
CSV_PATH = BASE_DIR / f"consistency_report_{REGION}_{INPUT_NEW.stem}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"

print(f"\n📂 工作目录: {BASE_DIR}")
print(f"🔹 上一版本: {INPUT_OLD.name}")
print(f"🔹 当前版本: {INPUT_NEW.name}")
print(f"🧾 报告输出: {CSV_PATH}\n")


# === 提取标题函数 ===
def extract_titles(text):
    """提取 Markdown 文本中的标题行"""
    return re.findall(r"^(#{1,5})\s+(.+)$", text, re.M)


# === 比较逻辑 ===
def compare_titles(old_titles, new_titles):
    """比较前后版本标题集合"""
    old_set = {t[1].strip() for t in old_titles}
    new_set = {t[1].strip() for t in new_titles}
    missing = sorted(old_set - new_set)
    added = sorted(new_set - old_set)
    return missing, added


# === 主执行函数 ===
def main():
    try:
        old_text = INPUT_OLD.read_text(encoding="utf-8")
        new_text = INPUT_NEW.read_text(encoding="utf-8")
    except Exception as e:
        print(f"❌ 读取文件失败：{e}")
        sys.exit(1)

    old_titles = extract_titles(old_text)
    new_titles = extract_titles(new_text)

    missing, added = compare_titles(old_titles, new_titles)

    with open(CSV_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["类型", "标题"])
        for m in missing:
            writer.writerow(["缺失", m])
        for a in added:
            writer.writerow(["新增", a])

    print(f"✅ 一致性检测完成：{CSV_PATH}")
    print(f"📊 缺失标题 {len(missing)}，新增标题 {len(added)}\n")


if __name__ == "__main__":
    main()
