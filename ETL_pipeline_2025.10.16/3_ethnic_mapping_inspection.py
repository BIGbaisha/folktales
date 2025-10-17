# 2025-10-17 10:00:00
# \ETL_pipeline_2025.10.16\3_ethnic_mapping_inspection.py

# -*- coding: utf-8 -*-
"""
民族映射检测（命中与未命中分开输出）
------------------------------------
功能：
1. 检测 markdown 文件中以“族”结尾的民族名；
2. 与映射表对比；
3. 输出两个 CSV：
   - 一个包含命中映射表的民族；
   - 一个包含未命中的民族。
"""

import re
import csv
from pathlib import Path
import sys

# ============================
# 配置参数
# ============================
MODE = "inspect"  # 可选："inspect" 或 "summary"
INPUT_MD = r"I:\中国民间传统故事\分卷清洗\yunnan\Chinese Folk Tales_yunnan.md"
MAPPING_TXT = r"D:\pythonprojects\folktales\data\ethnic_mapping.txt"

OUTPUT_HIT_CSV = r"I:\中国民间传统故事\分卷清洗\yunnan\3.1_ethnic_hit.csv"
OUTPUT_UNMAPPED_CSV = r"I:\中国民间传统故事\分卷清洗\yunnan\3.1_ethnic_unmapped.csv"

# ============================
# 函数定义
# ============================

def load_mapping(path):
    mapping = set()
    if not Path(path).exists():
        print(f"[WARN] 未找到映射表: {path}")
        return mapping
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                mapping.add(line)
    print(f"[INFO] 已加载映射表，共 {len(mapping)} 项")
    return mapping

def extract_ethnic_terms(text):
    # 匹配长度 1~5 的汉字 + “族”
    return re.findall(r"([\u4e00-\u9fa5]{1,5}族)", text)

def inspect_mode():
    print("[MODE] inspect - 输出命中与未命中映射表的民族")
    mapping = load_mapping(MAPPING_TXT)
    text = Path(INPUT_MD).read_text(encoding="utf-8")
    terms = extract_ethnic_terms(text)
    unique_terms = sorted(set(terms))

    hits = [t for t in unique_terms if t in mapping]
    unmapped = [t for t in unique_terms if t not in mapping]

    # ====== 写入命中表 ======
    with open(OUTPUT_HIT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["命中映射项"])
        for t in hits:
            writer.writerow([t])

    # ====== 写入未命中表 ======
    with open(OUTPUT_UNMAPPED_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["未映射项"])
        for t in unmapped:
            writer.writerow([t])

    # ====== 打印统计 ======
    print("\n=== 检测结果汇总 ===")
    print(f"总计民族词：{len(unique_terms)}")
    print(f"✅ 命中映射：{len(hits)} → {OUTPUT_HIT_CSV}")
    print(f"⚠️ 未命中：{len(unmapped)} → {OUTPUT_UNMAPPED_CSV}")
    print("🎉 检测完成")

def summary_mode():
    print("[MODE] summary - 打印短行与“族”结尾行")
    text = Path(INPUT_MD).read_text(encoding="utf-8")
    for line in text.splitlines():
        s = line.strip()
        if len(s) <= 10 and s.endswith("族"):
            print(s)
    print("[DONE] 摘要打印完成")

# ============================
# 主逻辑
# ============================

def main():
    global MODE
    if len(sys.argv) > 1:
        MODE = sys.argv[1].lower()
    if MODE == "inspect":
        inspect_mode()
    elif MODE == "summary":
        summary_mode()
    else:
        print(f"[ERROR] 未知模式: {MODE}")

if __name__ == "__main__":
    main()
