# -*- coding: utf-8 -*-
# 2025-10-27
"""
检测并清除 “讲述者/口述者/整理者 等信息块”
------------------------------------------------
逻辑：
- 当行以设定的关键词（如“讲述者”、“口述者”、“整理者”）开头；
- 允许前面有空格或不可见字符；
- 从该行起，直到下一个标题（^#+）之前的所有行；
=> 视为信息块。

模式：
- ONLY_DETECT=True：仅检测并输出CSV；
- ONLY_DETECT=False：删除并输出清理后文件。
"""

import re
import csv
from pathlib import Path

# ===== 配置 =====
INPUT_PATH  = r"I:\中国民间传统故事\分卷清洗\yunnan\6.4_Chinese Folk Tales_yunnan.md"
OUTPUT_PATH = r"I:\中国民间传统故事\分卷清洗\yunnan\6.5_Chinese Folk Tales_yunnan.md"
CSV_PATH    = r"I:\中国民间传统故事\分卷清洗\yunnan\6.5_detected_narrator_blocks.csv"

ONLY_DETECT = False   # True=仅检测; False=删除
TARGET_KEYWORDS = ["讲述者", "翻译者","采录者", "整理者"]  # 可动态修改
# =================

# 正则
RE_HEADING = re.compile(r"^\s*#{1,6}\s+")  # 标题
RE_DYNAMIC = re.compile(
    r"^[\s\u3000\u200b\u200c\u200d\uFEFF]*"
    r"(?:" + "|".join(map(re.escape, TARGET_KEYWORDS)) + r")[:：]"
)
RE_EMPTY   = re.compile(r"^[\s\u200b\u200c\u200d\uFEFF]*$")

def detect_blocks(lines):
    """检测信息块"""
    n = len(lines)
    i = 0
    blocks = []
    current_heading = "（无标题）"

    while i < n:
        line = lines[i]
        # 更新标题
        if RE_HEADING.match(line):
            current_heading = line.strip()
            i += 1
            continue

        # 检测动态匹配的信息块开头
        if RE_DYNAMIC.match(line):
            start = i
            j = i + 1
            while j < n and not RE_HEADING.match(lines[j]):
                j += 1
            end = j
            block_text = "".join(lines[start:end])
            blocks.append({
                "heading": current_heading,
                "start_line": start + 1,
                "end_line": end,
                "line_count": end - start,
                "content_preview": re.sub(r"\s+", " ", block_text.strip())[:80]
            })
            i = end
            continue
        i += 1

    return blocks

def export_csv(blocks, csv_path):
    """输出检测结果 CSV"""
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["Heading", "StartLine", "EndLine", "LineCount", "ContentPreview"])
        for b in blocks:
            writer.writerow([b["heading"], b["start_line"], b["end_line"], b["line_count"], b["content_preview"]])
    print(f"\n🧾 已导出检测结果 CSV：{csv_path}")

def remove_blocks(lines, blocks):
    """从文本中删除指定区块"""
    to_remove = set()
    for b in blocks:
        for k in range(b["start_line"] - 1, b["end_line"]):
            to_remove.add(k)
    return [line for idx, line in enumerate(lines) if idx not in to_remove]

def main():
    ip = Path(INPUT_PATH)
    if not ip.exists():
        raise FileNotFoundError(f"输入文件不存在：{ip}")

    lines = ip.read_text(encoding="utf-8", errors="ignore").splitlines(True)
    blocks = detect_blocks(lines)

    print("====== 检测结果 ======")
    print(f"总行数：{len(lines)}")
    print(f"检测到信息块：{len(blocks)}")
    for b in blocks[:10]:
        print(f"\n标题：{b['heading']}")
        print(f"行号：{b['start_line']} - {b['end_line']}  ({b['line_count']} 行)")
        print(f"预览：{b['content_preview']}")
    print("======================")

    export_csv(blocks, Path(CSV_PATH))

    if ONLY_DETECT:
        print("\n🔍 当前为检测模式，仅输出结果与CSV，不修改文件。")
    else:
        cleaned_lines = remove_blocks(lines, blocks)
        Path(OUTPUT_PATH).write_text("".join(cleaned_lines), encoding="utf-8")
        print(f"\n✅ 已写出清理后文件：{OUTPUT_PATH}")

if __name__ == "__main__":
    main()
