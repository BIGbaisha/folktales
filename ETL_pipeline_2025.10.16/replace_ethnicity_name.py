# -*- coding: utf-8 -*-
# Created on: 2025-10-30
# Version: v2025.02
"""
Batch replace ethnicity names in Markdown text and print statistics.
-------------------------------------------------------------------
Replaces incorrect/variant ethnicity names with standardized ones,
and prints how many replacements were made for each key.
"""

from pathlib import Path
import re

# ===== Configuration =====
INPUT_PATH  = r"I:\中国民间传统故事\分卷清洗\yunnan\6.7.1_Chinese Folk Tales_yunnan.md"
OUTPUT_PATH = r"I:\中国民间传统故事\分卷清洗\yunnan\6.7.3_Chinese Folk Tales_yunnan_replaced.md"
# ==========================

# Replacement dictionary
REPLACE_MAP = {
    "保保族": "傈僳族",
    "保康族": "傈僳族",
    "倮倮族": "傈僳族",
    "何昌族": "阿昌族",
    "普禾族": "普米族",
    "芯族": "怒族",
}

def replace_ethnicities(text: str, mapping: dict):
    """Replace all listed ethnicity names and count occurrences."""
    stats = {}
    for old, new in sorted(mapping.items(), key=lambda x: len(x[0]), reverse=True):
        pattern = re.compile(re.escape(old))
        matches = len(pattern.findall(text))
        if matches > 0:
            text = pattern.sub(new, text)
            stats[old] = matches
    return text, stats

def main():
    ip = Path(INPUT_PATH)
    op = Path(OUTPUT_PATH)
    if not ip.exists():
        raise FileNotFoundError(f"❌ Input file not found: {ip}")

    text = ip.read_text(encoding="utf-8", errors="ignore")
    replaced_text, stats = replace_ethnicities(text, REPLACE_MAP)
    op.write_text(replaced_text, encoding="utf-8")

    print("\n====== Replacement Summary ======")
    if stats:
        total = sum(stats.values())
        for old, count in stats.items():
            print(f"{old} → {REPLACE_MAP[old]} ：{count} 处")
        print("---------------------------------")
        print(f"✅ 总计替换：{total} 处")
    else:
        print("未检测到可替换的民族名称。")
    print("=================================")
    print(f"\n✅ 已写出替换后文件：{op}")

if __name__ == "__main__":
    main()
