# -*- coding: utf-8 -*-
# Created on: 2025/10/27
"""
检测并清除“信息块”（讲述者/采录者/整理者/...）
---------------------------------------
逻辑：
- 当行以任意设定关键字开头（允许前有空格或不可见字符）；
- 从该行起，直到下一个标题（^#+）之前的所有行；
=> 视为“信息块”并删除。

模式：
- ONLY_DETECT=True：仅检测并输出CSV；
- ONLY_DETECT=False：删除并输出清理后文件。
"""

import re
import csv
from pathlib import Path

# ===== 可自定义配置 =====
INPUT_PATH  = r"I:\中国民间传统故事\分卷清洗\yunnan\6.4_Chinese Folk Tales_yunnan.md"
OUTPUT_PATH = r"I:\中国民间传统故事\分卷清洗\yunnan\6.5_Chinese Folk Tales_yunnan.md"
CSV_PATH    = r"I:\中国民间传统故事\分卷清洗\yunnan\6.5_detected_blocks.csv"

ONLY_DETECT = False  # True = 仅检测; False = 执行删除

# ✅ 自定义触发关键字，可自由扩展
TRIGGER_KEYWORDS = [
    "讲述者", "口述者", "采录者", "翻译者", "译述者", "整理者", "记录者",
    "叙述者", "叙事者", "传述者", "提供者", "采访者"
]
# ==========================

# 标题检测：任意级别 #
RE_HEADING = re.compile(r"^\s*#{1,6}\s+")

# 讲述者等触发词检测（动态拼接）
RE_TRIGGER = re.compile(
    r"^[\s\u3000\u200b\u200c\u200d\uFEFF]*(" +
    "|".join(map(re.escape, TRIGGER_KEYWORDS)) +
    r")[:：]"
)


def detect_blocks(lines):
    """检测以触发关键字开头的区块（到下一个标题为止）"""
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

        # 触发关键字匹配
        if RE_TRIGGER.match(line):
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
            writer.writerow([
                b["heading"], b["start_line"], b["end_line"], b["line_count"], b["content_preview"]
            ])
    print(f"\n🧾 已导出检测结果 CSV：{csv_path}")


def remove_blocks(lines, blocks):
    """删除检测到的区块"""
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
