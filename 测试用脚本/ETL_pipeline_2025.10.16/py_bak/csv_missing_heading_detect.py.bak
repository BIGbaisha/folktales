# -*- coding: utf-8 -*-
# Created on: 2025-10-27
# Version: v2025.10
"""
Detect missing story numbers from heading list in ethnicity CSV
---------------------------------------------------------------
Reads the `Heading` column from an exported ethnicity detection CSV
and reports missing or duplicated story numbers.
"""

import csv
import re
from pathlib import Path

# ===== Configuration =====
CSV_PATH = r"I:\中国民间传统故事\分卷清洗\yunnan\6.7_detected_ethnicity.csv"
OUTPUT_MISSING_PATH = r"I:\中国民间传统故事\分卷清洗\yunnan\6.7_missing_numbers.csv"
# ==========================

RE_NUMBER = re.compile(r"\b(\d{1,4})[\.、,，．：:]")

def read_headings(csv_path):
    """Read headings and extract numbers."""
    numbers = []
    headings = []
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            heading = row.get("Heading", "")
            m = RE_NUMBER.search(heading)
            if m:
                num = int(m.group(1))
                numbers.append(num)
                headings.append(heading)
    return numbers, headings


def detect_missing_numbers(numbers):
    """Return missing and duplicate story numbers."""
    if not numbers:
        return [], []
    numbers_sorted = sorted(numbers)
    min_n, max_n = numbers_sorted[0], numbers_sorted[-1]

    full_range = set(range(min_n, max_n + 1))
    missing = sorted(list(full_range - set(numbers)))
    duplicates = [n for n in set(numbers) if numbers.count(n) > 1]
    return missing, duplicates


def export_results(missing, duplicates, output_path):
    """Export missing and duplicate info to CSV."""
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["Type", "Number"])
        for m in missing:
            writer.writerow(["Missing", m])
        for d in duplicates:
            writer.writerow(["Duplicate", d])
    print(f"\n🧾 Exported report: {output_path}")


def main():
    numbers, headings = read_headings(Path(CSV_PATH))
    print(f"✅ Found {len(numbers)} headings with numbers.")

    missing, duplicates = detect_missing_numbers(numbers)

    print("\n====== Story Number Report ======")
    if missing:
        print(f"⚠️ Missing numbers ({len(missing)}): {', '.join(map(str, missing))}")
    else:
        print("✅ No missing numbers detected.")

    if duplicates:
        print(f"⚠️ Duplicates: {', '.join(map(str, duplicates))}")
    else:
        print("✅ No duplicates detected.")
    print("=================================")

    export_results(missing, duplicates, Path(OUTPUT_MISSING_PATH))


if __name__ == "__main__":
    main()
# 创建时间: 2025/10/27 15:54
