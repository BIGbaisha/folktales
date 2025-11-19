# 创建时间: 2025/10/11 10:01
# -*- coding: utf-8 -*-
"""
仅打印版本：检查 Markdown 中 H4（故事编号）是否连续（1..EXPECTED_MAX）
支持：
- 全角/半角数字
- 前导零可有可无
- 数字后的分隔符宽松（空格/点/顿号/破折号等）
功能（全部打印到控制台，不生成CSV）：
- 总体统计（识别总数、唯一数）
- 缺失编号清单 + 每个缺失编号的前/后锚点（已识别的相邻编号及其行号）
- 重复编号详情（每个重复编号出现的所有行号 + 原文）
- 可疑编号行（起始 token 有 O/0、I/l/1、S/5、B/8 混淆迹象）
"""

import re
import os
from collections import Counter
from typing import List, Tuple, Dict

# ========== 硬编码路径与参数 ==========
INPUT_PATH   = r"I:\中国民间传统故事\分卷清洗\sichuan\5.1_Chinese Folk Tales_sichuan.md"
EXPECTED_MAX = 1029

# 为避免超长终端刷屏，可设置每段分块打印数量（None 表示全部）
CHUNK_SIZE_MISSING = 30     # 缺失编号分块大小
MAX_DUP_EXAMPLES   = None   # 每个重复编号展示的出现次数（None=全部）
MAX_SUSPECT_ROWS   = None   # 可疑编号最多展示多少行（None=全部）

# ========== 正则与工具 ==========
PUNCT_WS = r"\s,\.，。:：;；!！\?？·・—\-_\~`'\"“”‘’\(\)（）\[\]【】<>《》、…⋯．·"

# 全角数字 → 半角
_FW2HW_MAP = {ord(f): ord('0') + i for i, f in enumerate('０１２３４５６７８９')}
def to_halfwidth_digits(s: str) -> str:
    return s.translate(_FW2HW_MAP)

def normalize_num_token(s: str) -> str:
    """转半角并去掉非数字字符"""
    s = to_halfwidth_digits(s)
    return re.sub(r"[^0-9]", "", s)

# 识别 H4 或“看起来像编号起头”的行
RE_H4_PREFIX    = re.compile(rf"^\s*####\s*(?P<num>[0-9０-９]+)\s*[{PUNCT_WS}]*")
RE_LOOSE_PREFIX = re.compile(rf"^\s*(?P<num>[0-9０-９]+)\s*[{PUNCT_WS}]+", re.UNICODE)

# 可疑 token（数字与易混字母混杂，如 O/0、I/l/1、S/5、B/8）
RE_SUSPECT_START = re.compile(
    rf"^\s*(?P<tok>[0-9０-９OolLIISSBb]{{1,8}})\s*[{PUNCT_WS}]+",
    re.UNICODE
)

def extract_h4_number(line: str):
    """
    尝试从行首提取编号。
    返回：(编号int或-1, 原始匹配token)
    """
    m = RE_H4_PREFIX.match(line)
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
        if val > 100000:  # 过滤异常大数
            return -1, raw_num
        return val, raw_num
    except ValueError:
        return -1, raw_num

def scan_file(path: str):
    """
    返回：
    rows: [(line_no, raw_line, parsed_no, raw_token)]
    h4_positions: [(parsed_no, line_no)]
    """
    rows, h4_positions = [], []
    with open(path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            s = line.rstrip("\n")
            n, tok = extract_h4_number(s)
            rows.append((idx, s, n, tok))
            if n > 0:
                h4_positions.append((n, idx))
    h4_positions.sort(key=lambda x: (x[0], x[1]))
    return rows, h4_positions

# ========== 打印工具 ==========
def _print_header(title: str):
    bar = "—" * max(8, len(title))
    print(f"\n{title}\n{bar}")

def _chunk_print(nums: List[int], chunk_size: int):
    for i in range(0, len(nums), chunk_size):
        print("  " + ", ".join(map(str, nums[i:i+chunk_size])))

# ========== 主逻辑 ==========
def main():
    if not os.path.isfile(INPUT_PATH):
        print(f"❌ 未找到输入文件：{INPUT_PATH}")
        return

    rows, h4_positions = scan_file(INPUT_PATH)
    nums = [n for (_, _, n, _) in rows if n > 0]
    got  = set(nums)
    expect  = set(range(1, EXPECTED_MAX + 1))
    missing = sorted(expect - got)
    dup     = sorted([n for n, c in Counter(nums).items() if n > 0 and c > 1])

    # —— 概览
    _print_header("总体统计")
    print(f"文件: {INPUT_PATH}")
    print(f"编号期望范围: 1..{EXPECTED_MAX}")
    print(f"成功识别编号总数: {len(nums)}（唯一 {len(set(nums))}）")
    print(f"缺失编号数: {len(missing)}")
    print(f"重复编号种类数: {len(dup)}")

    # —— 缺失编号：列清单 + 邻接锚点
    _print_header("缺失编号清单")
    if missing:
        if CHUNK_SIZE_MISSING:
            _chunk_print(missing, CHUNK_SIZE_MISSING)
        else:
            print("  " + ", ".join(map(str, missing)))
    else:
        print("  ✅ 无缺失编号")

    _print_header("缺失编号定位（前后锚点）")
    if missing:
        pos_sorted = sorted(h4_positions, key=lambda x: x[0])  # (num, line)
        for m in missing:
            left  = max([p for p in pos_sorted if p[0] < m], default=None, key=lambda x: x[0])
            right = min([p for p in pos_sorted if p[0] > m], default=None, key=lambda x: x[0])
            prev_str = f"{left[0]} @ line {left[1]}" if left else "—"
            next_str = f"{right[0]} @ line {right[1]}" if right else "—"
            print(f"  缺失 {m}:  prev={prev_str}  |  next={next_str}")
        print("  提示：在 prev 与 next 之间查漏；注意 O/0、I/l/1、S/5、B/8 混淆。")
    else:
        print("  （无缺失，略）")

    # —— 重复编号详情
    _print_header("重复编号详情（行号与原文）")
    if dup:
        for n in dup:
            print(f"\n  ▸ 编号 {n}：")
            count = 0
            for ln, text, val, _tok in rows:
                if val == n:
                    print(f"    - line {ln}: {text}")
                    count += 1
                    if MAX_DUP_EXAMPLES and count >= MAX_DUP_EXAMPLES:
                        print("    ...（更多已省略）")
                        break
    else:
        print("  ✅ 无重复编号")

    # —— 可疑编号（行首 token 混淆）
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
            if MAX_SUSPECT_ROWS and shown >= MAX_SUSPECT_ROWS:
                print("  ...（更多已省略）")
                break
        print("  提示：这些行可能是漏识的 H4（如 ８３O→830、l76→176、９６４l→964）。")
    else:
        print("  （未检测到明显可疑 token）")

if __name__ == "__main__":
    main()

