# -*- coding: utf-8 -*-
# Created on: 2025-10-30
# Version: v2025.02
"""
Validate ethnicity lines in cleaned Markdown files.
----------------------------------------------------
✅ Only checks lines that start with '>'
✅ Ignores bold text like **(一)** or **(二)**
✅ Matches against a valid ethnicity dictionary
✅ Outputs mismatched items (with H3 heading) to CSV
"""

import re
import csv
from pathlib import Path

# ===== Configuration =====
INPUT_PATH  = r"I:\中国民间传统故事\分卷清洗\yuzhongqu\6.7_Chinese Folk Tales_yuzhongqu.md"
OUTPUT_PATH = r"I:\中国民间传统故事\分卷清洗\yuzhongqu\6.7.2.1_invalid_ethnicity_report.csv"

VALID_ETHNICITIES = {
    "汉族","壮族","回族","满族","维吾尔族","苗族","彝族","土家族","藏族","蒙古族",
    "布依族","侗族","瑶族","朝鲜族","白族","哈尼族","哈萨克族","黎族","傣族","畲族",
    "傈僳族","仡佬族","东乡族","高山族","拉祜族","水族","佤族","纳西族","羌族","土族",
    "仫佬族","锡伯族","柯尔克孜族","达斡尔族","景颇族","毛南族","撒拉族","布朗族","塔吉克族",
    "阿昌族","普米族","鄂温克族","怒族","京族","基诺族","德昂族","保安族","俄罗斯族","裕固族",
    "乌孜别克族","门巴族","鄂伦春族","独龙族","塔塔尔族","赫哲族","珞巴族"
}
# ==========================

RE_HEADING = re.compile(r"^(#{1,6})\s*\d{1,4}[\.\、,，．：:\s]*.+$")
RE_ETHNICITY_LINE = re.compile(r"^\s*>\s*([\u4e00-\u9fa5——\s]+)$")

def clean_ethnicity(raw: str) -> str:
    """Keep only Chinese characters (and '——')."""
    return re.sub(r"[^\u4e00-\u9fa5——]", "", raw or "").strip()

def check_ethnicity(file_path: Path):
    """Check all '> 民族' lines against dictionary."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    invalid = []
    current_heading = "（无标题）"

    for i, raw in enumerate(lines, start=1):
        line = raw.strip()

        # Track heading
        if RE_HEADING.match(line):
            current_heading = line
            continue

        # ✅ Only consider lines starting with ">"
        if not line.startswith(">"):
            continue

        m = RE_ETHNICITY_LINE.match(line)
        if not m:
            continue  # skip decorative quote lines, malformed lines, etc.

        ethnicity = clean_ethnicity(m.group(1))

        # Skip placeholders or empty
        if not ethnicity or ethnicity == "——":
            continue

        if ethnicity not in VALID_ETHNICITIES:
            invalid.append({
                "heading": current_heading,
                "line_no": i,
                "ethnicity": ethnicity,
                "status": "❌ Not in dict"
            })

    return invalid

def export_csv(invalid_list, output_path):
    """Write invalid entries to CSV."""
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["Heading", "LineNo", "Ethnicity", "Status"])
        for item in invalid_list:
            writer.writerow([item["heading"], item["line_no"], item["ethnicity"], item["status"]])
    print(f"\n🧾 Exported invalid ethnicity report: {output_path}")

def main():
    invalid_entries = check_ethnicity(Path(INPUT_PATH))

    print("====== Ethnicity Validation ======")
    if not invalid_entries:
        print("✅ All ethnicity entries match the dictionary.")
    else:
        print(f"⚠️ Found {len(invalid_entries)} invalid entries:")
        for item in invalid_entries:
            print(f"{item['line_no']:>5} | {item['heading']} | {item['ethnicity']}")
    print("=================================")

    if invalid_entries:
        export_csv(invalid_entries, Path(OUTPUT_PATH))

if __name__ == "__main__":
    main()
