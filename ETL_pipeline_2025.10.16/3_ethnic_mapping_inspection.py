# 创建时间: 2025/10/15 14:20
# 版本: v2025.10
# -*- coding: utf-8 -*-
"""
3_ethnic_mapping_inspection_enhanced.py
----------------------------------------
功能：
- 检测中国民间故事 markdown 文件中的“族”结尾词，根据民族映射表检查映射情况
- 通过 MODE 选项，切换不同模式：
  * MODE = "inspect" 输出未映射项到 CSV
  * MODE = "summary" 打印简短行与以“族”结尾的文本行

输入路径：I:\\中国民间传统故事\\老黑解析版本\\正式测试\\
输出：CSV 文件或简要推出
"""

import re
import csv
from pathlib import Path
import sys

# ============================
# 可配置参数
# ============================
MODE = "inspect"  # 可选："inspect" 或 "summary"

INPUT_MD = r"I:\\中国民间传统故事\\老黑解析版本\\正式测试\\2.1_raw_sichuan.md"
MAPPING_TXT = r"I:\\中国民间传统故事\\老黑解析版本\\正式测试\\ethnic_mapping.txt"
OUTPUT_CSV = r"I:\\中国民间传统故事\\老黑解析版本\\正式测试\\3.1_ethnic_unmapped.csv"

# ============================
# 功能模块
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
    print(f"[INFO] 已加载映射项 {len(mapping)} 条")
    return mapping

def extract_ethnic_terms(text):
    return re.findall(r"([\u4e00-\u9fa5]{1,5}族)", text)

def inspect_mode():
    print("[MODE] inspect - 检测未映射民族")
    mapping = load_mapping(MAPPING_TXT)
    text = Path(INPUT_MD).read_text(encoding="utf-8")
    terms = extract_ethnic_terms(text)
    unique_terms = sorted(set(terms))
    unmapped = [t for t in unique_terms if t not in mapping]
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["未映射项"])
        for t in unmapped:
            writer.writerow([t])
    print(f"[DONE] 未映射 {len(unmapped)} 项 -> {OUTPUT_CSV}")

def summary_mode():
    print("[MODE] summary - 打印短行与族后结尾行")
    text = Path(INPUT_MD).read_text(encoding="utf-8")
    lines = text.splitlines()
    for line in lines:
        s = line.strip()
        if len(s) <= 10 and s.endswith("族"):
            print(s)
    print("[DONE] 摘要打印完成")

# ============================
# 主调用逻辑
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
