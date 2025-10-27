# -*- coding: utf-8 -*-
# Created on: 2025-10-27
# Version: v2025.12
"""
Final version – Corrected placeholder logic
-------------------------------------------
✅ Manual heading level (TARGET_LEVEL)
✅ Detects inline or separate ethnicity lines
✅ Handles formatting symbols (**, _, punctuation, etc.)
✅ Cleans to Chinese characters only
✅ Adds "> ——" ONLY when ethnicity is truly missing
✅ YAML-safe output (never breaks YAML)
"""

import re
import csv
from pathlib import Path

# ===== Configuration =====
INPUT_PATH  = r"I:\中国民间传统故事\分卷清洗\yunnan\6.6_Chinese Folk Tales_yunnan.md"
OUTPUT_PATH = r"I:\中国民间传统故事\分卷清洗\yunnan\6.7_Chinese Folk Tales_yunnan.md"
CSV_PATH    = r"I:\中国民间传统故事\分卷清洗\yunnan\6.7_detected_ethnicity.csv"

ONLY_DETECT = False     # True = detect only, False = replace & clean
TARGET_LEVEL = 3       # 👈 manually set heading level (e.g., 3 = ###)
# ==========================

# --- Regex Definitions ---
RE_NUM_TITLE = re.compile(
    rf"^[\s\u3000\u200b\u200c\u200d\uFEFF]*({'#'*TARGET_LEVEL})\s*\d{{1,4}}[\.、,，．：:\s]*.+$"
)

RE_INLINE_ETHNICITY = re.compile(
    rf"^[\s\u3000\u200b\u200c\u200d\uFEFF]*({'#'*TARGET_LEVEL})\s*\d{{1,4}}[\.、,，．：:\s]*"
    r"(.+?)[（(].*?([\u4e00-\u9fa5\s]+).*?[)）].*$"
)

RE_ETHNICITY = re.compile(
    r"""^[\s\*\_>—\-、,，．。:：;；·•~～]*           # leading punctuation
        [（(]\s*([\u4e00-\u9fa5\s]+?)\s*[)）]        # ethnicity content
        [\s\*\_>—\-、,，．。:：;；·•~～\.!?]*$        # trailing symbols
    """,
    re.VERBOSE
)

RE_EMPTY = re.compile(r"^[\s\u200b\u200c\u200d\uFEFF]*$")


def clean_ethnicity(raw_text: str) -> str:
    """Extract only Chinese characters, fallback to '——' if empty."""
    if not raw_text:
        return "——"
    text = re.sub(r"[^\u4e00-\u9fa5]", "", raw_text)
    return text if text else "——"


def detect_ethnicity_blocks(lines):
    """Detect ethnicity info below or inside story headings."""
    n = len(lines)
    i = 0
    blocks = []

    while i < n:
        line = lines[i].strip("\r\n\uFEFF\u200b\u200c\u200d ")
        inline_match = RE_INLINE_ETHNICITY.match(line)
        heading_match = RE_NUM_TITLE.match(line)

        # Case 1️⃣ Inline ethnicity in same line
        if inline_match:
            heading_text = inline_match.group(2).strip()
            ethnicity = clean_ethnicity(inline_match.group(3))
            blocks.append({
                "heading": heading_text,
                "level": f"H{TARGET_LEVEL}",
                "line_no": i + 1,
                "ethnicity": ethnicity,
            })
            i += 1
            continue

        # Case 2️⃣ Heading with ethnicity line below
        if heading_match:
            heading_text = line.strip()
            j = i + 1
            while j < n and RE_EMPTY.match(lines[j]):
                j += 1

            ethnicity = "——"
            if j < n:
                line_check = lines[j].strip("\r\n\uFEFF\u200b\u200c\u200d ")
                m = RE_ETHNICITY.search(line_check)
                if m:
                    ethnicity = clean_ethnicity(m.group(1))

            blocks.append({
                "heading": heading_text,
                "level": f"H{TARGET_LEVEL}",
                "line_no": j + 1 if j < n else "--",
                "ethnicity": ethnicity,
            })
            i = j
        i += 1

    return blocks


def export_csv(blocks, csv_path):
    """Export detection results to CSV."""
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["Heading", "Level", "LineNo", "Ethnicity"])
        for b in blocks:
            writer.writerow([b["heading"], b["level"], b["line_no"], b["ethnicity"]])
    print(f"\n🧾 Exported detection report: {csv_path}")


def replace_ethnicity_lines(lines):
    """Replace '(民族)' with '> 民族' (real) or skip if missing."""
    new_lines = []
    for line in lines:
        inline = RE_INLINE_ETHNICITY.match(line)
        if inline:
            heading_text = inline.group(2).rstrip()
            ethnicity = clean_ethnicity(inline.group(3))
            new_lines.append(f"{'#' * TARGET_LEVEL} {heading_text}\n")
            new_lines.append(f"> {ethnicity}\n")
            continue

        m = RE_ETHNICITY.search(line)
        if m:
            ethnicity = clean_ethnicity(m.group(1))
            new_lines.append(f"> {ethnicity}\n")
        else:
            new_lines.append(line)
    return new_lines


def main():
    ip = Path(INPUT_PATH)
    if not ip.exists():
        raise FileNotFoundError(f"Input file not found: {ip}")

    lines = ip.read_text(encoding="utf-8", errors="ignore").splitlines(True)
    blocks = detect_ethnicity_blocks(lines)

    print("====== Detection Results ======")
    print(f"Total lines: {len(lines)}")
    print(f"Detected H{TARGET_LEVEL} story headings: {len(blocks)}")
    for b in blocks[:10]:
        print(f"\n{b['level']} | {b['heading']}")
        print(f"Line: {b['line_no']}")
        print(f"Ethnicity: {b['ethnicity']}")
    print("===============================")

    export_csv(blocks, Path(CSV_PATH))

    if ONLY_DETECT:
        print("\n🔍 Detection mode only — no file modification.")
        return

    # === Replace and insert placeholders only where missing ===
    cleaned_lines = replace_ethnicity_lines(lines)

    # Build a mapping of which headings actually have real ethnicity
    real_ethnicity_headings = {
        b["heading"].strip(): b["ethnicity"]
        for b in blocks if b["ethnicity"] != "——"
    }

    final_output = []
    n = len(cleaned_lines)
    for i, line in enumerate(cleaned_lines):
        final_output.append(line)

        if RE_NUM_TITLE.match(line):
            heading_text = line.strip()
            # Determine whether this heading had a real ethnicity
            has_real_ethnicity = any(
                heading_text.endswith(h.strip()) for h in real_ethnicity_headings
            )

            if not has_real_ethnicity:
                # Look ahead to see if already has a quote line
                next_line = cleaned_lines[i + 1] if i + 1 < n else ""
                if not next_line.strip().startswith(">"):
                    final_output.append("> ——\n")

    Path(OUTPUT_PATH).write_text("".join(final_output), encoding="utf-8")
    print(f"\n✅ Cleaned and saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
