# -*- coding: utf-8 -*-
# Created: 2025/11/5
"""
=============================================================
标题等级梳理脚本（逐行识别版 + 修正版加粗逻辑）
Version: 5_titles_normalize_v12.py
=============================================================
"""

import os
import re
import csv
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))  # 添加父目录

from utils.template_script_header_manual import (
    load_text, save_text, log_stage, log_summary
)
from utils.text_normalizer import normalize_chinese_text
from collections import Counter
from typing import List, Tuple, Dict

# ============================================================
# 路径与参数配置
# ============================================================
INPUT_PATH = Path(r"I:\中国民间传统故事\分卷清洗\sichuan\5.1_Chinese Folk Tales_sichuan.md")
CSV_REPORT_PATH = Path(r"I:\中国民间传统故事\分卷清洗\sichuan\5.2_number_check_H4.csv")
EXPECTED_MAX = 1029
TARGET_HEADING_LEVEL = 4  # ✅ 手动指定标题等级 (如 3 表示 ###, 4 表示 ####)

# ============================================================
# 正则与工具
# ============================================================
PUNCT_WS = r"\s,\.，。:：;；!！\?？·・—\-_\~`'\"“”‘’\(\)（）\[\]【】<>《》、…⋯．·"
_FW2HW_MAP = {ord(f): ord('0') + i for i, f in enumerate('０１２３４５６７８９')}

def to_halfwidth_digits(s: str) -> str:
    return s.translate(_FW2HW_MAP)

def normalize_num_token(s: str) -> str:
    s = to_halfwidth_digits(s)
    return re.sub(r"[^0-9]", "", s)

# 动态标题识别正则
RE_H_PREFIX    = re.compile(rf"^\s*{'#' * TARGET_HEADING_LEVEL}\s*(?P<num>[0-9０-９]+)\s*[{PUNCT_WS}]*")
RE_LOOSE_PREFIX = re.compile(rf"^\s*(?P<num>[0-9０-９]+)\s*[{PUNCT_WS}]+", re.UNICODE)
RE_SUSPECT_START = re.compile(
    rf"^\s*(?P<tok>[0-9０-９OolLIISSBb]{{1,8}})\s*[{PUNCT_WS}]+", re.UNICODE
)

# ============================================================
# 主逻辑函数（严格照搬原逻辑）
# ============================================================
def extract_number(line: str):
    m = RE_H_PREFIX.match(line)
    if not m:
        m = RE_LOOSE_PREFIX.match(line)
        if not m:
            return -1, ""
    raw_num = m.group("num")
    norm = normalize_num_token(raw_num)
    if not norm:
        return -1, raw_num
    try:
        val = int(norm)
        if val > 100000:
            return -1, raw_num
        return val, raw_num
    except ValueError:
        return -1, raw_num

def scan_file(path: Path):
    rows, positions = [], []
    text = load_text(path)
    for idx, line in enumerate(text.splitlines(), start=1):
        s = line.rstrip("\n")
        n, tok = extract_number(s)
        rows.append((idx, s, n, tok))
        if n > 0:
            positions.append((n, idx))
    positions.sort(key=lambda x: (x[0], x[1]))
    return rows, positions

def _print_header(title: str):
    bar = "—" * max(8, len(title))
    print(f"\n{title}\n{bar}")

def _chunk_print(nums: List[int], chunk_size: int = 30):
    for i in range(0, len(nums), chunk_size):
        print("  " + ", ".join(map(str, nums[i:i+chunk_size])))

def main():
    log_stage("开始检测指定 H 等级的标题连续性")
    rows, positions = scan_file(INPUT_PATH)
    nums = [n for (_, _, n, _) in rows if n > 0]
    got = set(nums)
    expect = set(range(1, EXPECTED_MAX + 1))
    missing = sorted(expect - got)
    dup = sorted([n for n, c in Counter(nums).items() if n > 0 and c > 1])

    _print_header("总体统计")
    print(f"文件: {INPUT_PATH}")
    print(f"检测标题等级: H{TARGET_HEADING_LEVEL}")
    print(f"编号期望范围: 1..{EXPECTED_MAX}")
    print(f"成功识别编号总数: {len(nums)}（唯一 {len(set(nums))}）")
    print(f"缺失编号数: {len(missing)}")
    print(f"重复编号种类数: {len(dup)}")

    _print_header("缺失编号清单")
    if missing:
        _chunk_print(missing)
    else:
        print("  ✅ 无缺失编号")

    _print_header("缺失编号定位（前后锚点）")
    if missing:
        pos_sorted = sorted(positions, key=lambda x: x[0])
        for m in missing:
            left = max([p for p in pos_sorted if p[0] < m], default=None, key=lambda x: x[0])
            right = min([p for p in pos_sorted if p[0] > m], default=None, key=lambda x: x[0])
            prev_str = f"{left[0]} @ line {left[1]}" if left else "—"
            next_str = f"{right[0]} @ line {right[1]}" if right else "—"
            print(f"  缺失 {m}:  prev={prev_str}  |  next={next_str}")
        print("  提示：在 prev 与 next 之间查漏；注意 O/0、I/l/1、S/5、B/8 混淆。")
    else:
        print("  （无缺失，略）")

    _print_header("重复编号详情（行号与原文）")
    if dup:
        for n in dup:
            print(f"\n  ▸ 编号 {n}：")
            count = 0
            for ln, text, val, _tok in rows:
                if val == n:
                    print(f"    - line {ln}: {text}")
                    count += 1
                    if count >= 10:
                        print("    ...（更多已省略）")
                        break
    else:
        print("  ✅ 无重复编号")

    _print_header("可疑编号行（字母/数字混淆的起始 token）")
    suspects = []
    for ln, text, val, _tok in rows:
        if val > 0:
            continue
        m = RE_SUSPECT_START.match(text)
        if not m:
            continue
        tok = m.group("tok")
        hw = to_halfwidth_digits(tok)
        if re.search(r"[A-Za-z]", hw) and re.search(r"[0-9]", hw):
            suspects.append((ln, tok, text))
    if suspects:
        shown = 0
        for ln, tok, text in suspects:
            print(f"  - line {ln}: [{tok}]  {text}")
            shown += 1
            if shown >= 30:
                print("  ...（更多已省略）")
                break
        print("  提示：这些行可能是漏识的标题编号（如 ８３O→830、l76→176、９６４l→964）。")
    else:
        print("  （未检测到明显可疑 token）")

    # 生成 CSV 报告
    if missing:
        with open(CSV_REPORT_PATH, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['Missing_Number', 'Prev_Anchor', 'Next_Anchor'])
            pos_sorted = sorted(positions, key=lambda x: x[0])
            for m in missing:
                left = max([p for p in pos_sorted if p[0] < m], default=None, key=lambda x: x[0])
                right = min([p for p in pos_sorted if p[0] > m], default=None, key=lambda x: x[0])
                prev_str = f"{left[0]} @ line {left[1]}" if left else "—"
                next_str = f"{right[0]} @ line {right[1]}" if right else "—"
                writer.writerow([m, prev_str, next_str])
        log_summary(f"缺号报告已保存至 {CSV_REPORT_PATH}", INPUT_PATH, CSV_REPORT_PATH)
    else:
        log_summary("未发现缺号，未生成 CSV。", INPUT_PATH, CSV_REPORT_PATH)

if __name__ == '__main__':
    main()
