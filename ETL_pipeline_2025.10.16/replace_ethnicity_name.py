# -*- coding: utf-8 -*-
# Created on: 2025-10-28
# Version: v2025.03
"""
Batch replace ethnicity names in Markdown text and print statistics.
-------------------------------------------------------------------
Overwrites the input file with replacements and prints statistics only.
"""

from pathlib import Path
import re

# ===== Configuration =====
INPUT_PATH  = r"I:\中国民间传统故事\分卷清洗\yunnan\6.6_Chinese Folk Tales_yunnan.md"
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
    if not ip.exists():
        raise FileNotFoundError(f"❌ Input file not found: {ip}")

    text = ip.read_text(encoding="utf-8", errors="ignore")
    replaced_text, stats = replace_ethnicities(text, REPLACE_MAP)
    ip.write_text(replaced_text, encoding="utf-8")

    # Print only summary
    if stats:
        total = sum(stats.values())
        for old, count in stats.items():
            print(f"{old} → {REPLACE_MAP[old]} ：{count} 处")
        print(f"总计替换：{total} 处")
    else:
        print("未检测到可替换的民族名称。")

if __name__ == "__main__":
    main()
