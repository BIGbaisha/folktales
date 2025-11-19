# -*- coding: utf-8 -*-
# year/month/day
# ETL_pipeline_2025.11.xx_multi_ethnic_inject_and_promote.py

import re
import csv
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.template_script_header_manual import (
    load_text, save_text, log_stage, log_summary
)
from utils.text_normalizer import normalize_chinese_text

# ==========================================================
# 参数设置
# ==========================================================
TARGET_LEVEL = 4      # 故事标题等级，例如 #### → 4
PLACEHOLDER = "——"

INPUT_PATH  = Path(r"I:\中国民间传统故事\分卷清洗\sichuan\6.7_Chinese Folk Tales_sichuan.md")
OUTPUT_PATH = Path(r"I:\中国民间传统故事\分卷清洗\sichuan\6.8_Chinese Folk Tales_sichuan.md")
CSV_PATH    = Path(r"I:\中国民间传统故事\分卷清洗\sichuan\6.8_meta_extraction_summary.csv")

# ==========================================================
# 民族合法字典（已补全）
# ==========================================================
ETHNIC_DICT = {
    "汉族", "壮族", "满族", "回族", "苗族", "维吾尔族", "土家族", "彝族", "蒙古族",
    "藏族", "布依族", "侗族", "瑶族", "朝鲜族", "白族", "哈尼族", "哈萨克族",
    "黎族", "傣族", "畲族", "傈僳族", "仡佬族", "东乡族", "拉祜族", "水族",
    "佤族", "纳西族", "羌族", "土族", "仫佬族", "锡伯族", "柯尔克孜族",
    "景颇族", "撒拉族", "布朗族", "塔吉克族", "阿昌族", "普米族", "鄂温克族",
    "怒族", "京族", "基诺族", "德昂族", "保安族", "俄罗斯族", "裕固族",
    "乌孜别克族", "鄂伦春族", "门巴族", "赫哲族", "独龙族", "塔塔尔族"
}

# 正则
HEADING_PATTERN   = re.compile(r"^(#{1,6})\s+(.*)$")
H_TARGET_PATTERN  = re.compile(rf'^{"#" * TARGET_LEVEL}\s+(.+)$')
LOCATION_PATTERN  = re.compile(r"^>\s*地点[:：]")

# ==========================================================
# 工具函数：识别多民族 H1（除前言）
# ==========================================================
def detect_ethnic_h1(lines):
    ethnic_map = {}
    for idx, line in enumerate(lines):
        m = HEADING_PATTERN.match(line)
        if not m:
            continue
        level = len(m.group(1))
        title = m.group(2).strip()
        if level == 1 and title in ETHNIC_DICT and title != "前言":
            ethnic_map[idx] = title
    return ethnic_map

# ==========================================================
# 标题升一级（heading 数减少 1）
# ==========================================================
def promote_heading(line):
    m = HEADING_PATTERN.match(line)
    if not m:
        return line
    hashes, title = m.group(1), m.group(2)
    level = len(hashes)
    if level == 1:
        return line
    new_level = max(level - 1, 1)
    return f"{'#' * new_level} {title}"

# ==========================================================
# 主处理逻辑
# ==========================================================
def process(text):

    lines = text.splitlines()
    new_lines = []

    ethnic_h1_map = detect_ethnic_h1(lines)
    log_stage(f"识别到 {len(ethnic_h1_map)} 个民族 H1")

    current_ethnic = None
    report_rows = []

    i = 0

    while i < len(lines):
        line = lines[i]

        if i in ethnic_h1_map:
            current_ethnic = ethnic_h1_map[i]

        m = H_TARGET_PATTERN.match(line)
        if m:
            story_title = m.group(1).strip()
            story_line  = i + 1

            new_lines.append(line)
            i += 1

            inserted = False
            has_loc  = False
            block    = []

            while i < len(lines):
                l2 = lines[i]

                if HEADING_PATTERN.match(l2):
                    break

                if LOCATION_PATTERN.match(l2):
                    has_loc = True
                    block.append(l2)
                    block.append(f"> 民族: {current_ethnic if current_ethnic else PLACEHOLDER}")
                    inserted = True
                    i += 1

                    while i < len(lines) and not HEADING_PATTERN.match(lines[i]):
                        block.append(lines[i])
                        i += 1
                    break

                block.append(l2)
                i += 1

            if not inserted:
                new_lines.append("")
                new_lines.append(f"> 民族: {current_ethnic if current_ethnic else PLACEHOLDER}")

            new_lines.extend(block)

            report_rows.append([
                story_title,
                current_ethnic,
                story_line,
                "NO" if has_loc else "YES",
                "民族插入"
            ])
            continue

        new_lines.append(line)
        i += 1

    upgraded = [promote_heading(l) for l in new_lines]

    # ❗❗❗ 去掉“删除民族标题”逻辑 → 直接返回 upgraded
    return "\n".join(upgraded), report_rows

# ==========================================================
# 主入口
# ==========================================================
def main():

    text = load_text(INPUT_PATH)
    text = normalize_chinese_text(text)

    new_text, report = process(text)

    save_text(OUTPUT_PATH, new_text)
    log_stage(f"输出处理结果 → {OUTPUT_PATH}")

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["story_title", "ethnic", "line_number", "no_location", "reason"])
        w.writerows(report)

    log_stage(f"生成 CSV → {CSV_PATH}")

    # 正确调用 log_summary
    log_summary(
        str(INPUT_PATH),
        str(OUTPUT_PATH),
        {
            "total_rows": len(report)
        }
    )


if __name__ == "__main__":
    main()
