# -*- coding: utf-8 -*-
# 2025-10-27
"""
Markdown Cleaner v5
--------------------------------
Features:
1️⃣ Detects or removes all types of links (text, image, angle, bare URLs);
2️⃣ Ensures exactly one blank line before and after headings;
3️⃣ Ensures exactly one blank line between paragraphs.

Modes:
- REMOVE_LINKS = True → Detection only (prints found links);
- REMOVE_LINKS = False → Cleans and rewrites file.
"""

import re
from pathlib import Path

# ===== Configuration =====
INPUT_PATH  = r"I:\中国民间传统故事\分卷清洗\yuzhongqu\5.1_Chinese Folk Tales_yuzhongqu.md"
OUTPUT_PATH = r"I:\中国民间传统故事\分卷清洗\yuzhongqu\5.3_Chinese Folk Tales_yuzhongqu.md"

REMOVE_LINKS = False   # True = detect only; False = remove links
# =========================

# --- Regular Expressions ---
RE_HEADING = re.compile(r"^\s*#{1,6}\s+.*$")               # Markdown headings
RE_LINK_MD = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")        # [text](url)
RE_IMAGE_MD = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")      # ![alt](url)
RE_LINK_ANGLE = re.compile(r"<(https?://[^>]+)>")          # <http://xxx>
RE_LINK_BARE = re.compile(r"https?://[^\s)\]]+")           # Bare URL
RE_EMPTY = re.compile(r"^[\s\u200b\u200c\u200d\uFEFF]*$")  # Empty line detector


# === Core Functions ===

def detect_links(text: str):
    """Detect all link types including image links."""
    md_links = RE_LINK_MD.findall(text)
    image_links = RE_IMAGE_MD.findall(text)
    angle_links = RE_LINK_ANGLE.findall(text)
    bare_links = RE_LINK_BARE.findall(text)

    total = len(md_links) + len(image_links) + len(angle_links) + len(bare_links)
    print(f"\n🔍 Detected {total} links (including images):")

    if image_links:
        print(f"  • Image links: {len(image_links)} (first 3 shown):")
        for alt, url in image_links[:3]:
            print(f"    ![{alt}]({url})")

    if md_links:
        print(f"  • Markdown links: {len(md_links)}")
        for t, url in md_links[:5]:
            print(f"    [{t}]({url})")

    if angle_links:
        print(f"  • Angle-bracket links: {len(angle_links)} (first 3 shown):")
        for u in angle_links[:3]:
            print(f"    <{u}>")

    if bare_links:
        print(f"  • Bare URLs: {len(bare_links)} (first 3 shown):")
        for u in bare_links[:3]:
            print(f"    {u}")

    print("\n✅ Detection mode only — no file modifications performed.")


def remove_links_from_text(text: str) -> str:
    """Remove all link types including image links."""
    text = RE_IMAGE_MD.sub("", text)       # Remove image links
    text = RE_LINK_MD.sub(r"\1", text)     # Keep link text
    text = RE_LINK_ANGLE.sub("", text)     # Remove <https://...>
    text = RE_LINK_BARE.sub("", text)      # Remove bare URLs
    return text


def normalize_blank_lines(lines):
    """
    Normalize blank lines:
    - Ensure exactly one blank line before and after headings;
    - Ensure exactly one blank line between paragraphs.
    """
    output = []
    prev_blank = True  # treat start of file as blank

    for i, line in enumerate(lines):
        stripped = line.rstrip("\r\n")

        # Heading
        if RE_HEADING.match(stripped):
            if not prev_blank:
                output.append("\n")
            output.append(stripped + "\n")
            output.append("\n")
            prev_blank = True
            continue

        # Blank line
        if RE_EMPTY.match(stripped):
            if not prev_blank:
                output.append("\n")
                prev_blank = True
            continue

        # Normal text
        output.append(stripped + "\n")
        prev_blank = False

    # Ensure file ends with one newline
    if output and output[-1].strip():
        output.append("\n")

    return output


# === Main ===

def main():
    ip = Path(INPUT_PATH)
    if not ip.exists():
        raise FileNotFoundError(f"Input file not found: {ip}")

    text = ip.read_text(encoding="utf-8", errors="ignore")

    if REMOVE_LINKS:
        # Detection mode only
        detect_links(text)
        return

    # Cleaning mode
    print("🧹 Cleaning links and normalizing blank lines ...")
    text = remove_links_from_text(text)
    lines = text.splitlines(True)
    formatted_lines = normalize_blank_lines(lines)
    Path(OUTPUT_PATH).write_text("".join(formatted_lines), encoding="utf-8")

    print(f"\n✅ Cleaned and saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
