# 创建时间: 2025/10/11 12:22
# -*- coding: utf-8 -*-
"""
抽取文档中的数学表达式并导出 CSV（含左右上下文，便于“还原原貌”查看）
- 支持: $$...$$（跨行）, \[...\]（跨行）, $...$（行内）, \(...\)（行内）
- 输出: UTF-8-SIG CSV（Excel 友好）
- 仅提取与导出，不改源文件

硬编码路径：
  INPUT_PATH  - 要扫描的 MD/TXT
  OUTPUT_CSV  - 导出的 CSV
可调参数：
  WINDOW_CHARS - 上下文左右各截取的字符数
"""

import os
import re
import csv
import bisect

# ======== 硬编码路径 ========
INPUT_PATH  = r"I:\中国民间传统故事\老黑解析版本\正式测试\5_Chinese Folk Tales_sichuan_normalized.md"
OUTPUT_CSV  = r"I:\中国民间传统故事\老黑解析版本\正式测试\math_spans_with_context.csv"

# ======== 上下文窗口（左右各取多少字符） ========
WINDOW_CHARS = 40

# ======== 模式定义 ========
RE_MATH_BLOCK_DOLLAR = re.compile(r"\$\$(.+?)\$\$", re.DOTALL)     # $$...$$
RE_MATH_BLOCK_BRACK  = re.compile(r"\\\[(.+?)\\\]", re.DOTALL)     # \[...\]
RE_MATH_INLINE_DOLL  = re.compile(r"(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)")  # $...$
RE_MATH_INLINE_PARE  = re.compile(r"\\\((.+?)\\\)")                # \(...\)

# 查找顺序：先块级（避免与行内嵌套冲突），再行内
PATTERNS = [
    ("block", "$$...$$", RE_MATH_BLOCK_DOLLAR),
    ("block", r"\[...\]", RE_MATH_BLOCK_BRACK),
    ("inline", "$...$", RE_MATH_INLINE_DOLL),
    ("inline", r"\(...\)", RE_MATH_INLINE_PARE),
]

def build_line_index(text: str):
    """返回每一行的起始绝对偏移列表，用于把绝对下标→(行,列)"""
    starts = [0]
    for m in re.finditer(r"\n", text):
        starts.append(m.end())  # 下一行的起点
    return starts

def offset_to_line_col(offset: int, line_starts):
    """将绝对偏移转为(行,列)，行列均从1开始"""
    i = bisect.bisect_right(line_starts, offset) - 1
    line_no = i + 1
    col_no = offset - line_starts[i] + 1
    return line_no, col_no

def collect_math_spans(text: str):
    """
    收集所有数学表达式的 (start, end, type_label, syntax_label, full_match)
    注意：end 为 Python 切片右边界（不含）
    """
    spans = []
    taken = [False] * (len(text) + 1)  # 简易“占位”，避免不同模式重叠匹配
    for type_label, syntax_label, pat in PATTERNS:
        for m in pat.finditer(text):
            s, e = m.start(), m.end()
            if any(taken[s:e]):  # 落在已有更早命中的片段内则跳过
                continue
            spans.append((s, e, type_label, syntax_label, m.group(0)))
            for k in range(s, e):
                taken[k] = True
    spans.sort(key=lambda t: t[0])
    return spans

def clip_context(text: str, s: int, e: int, window: int):
    """返回 (before, math, after, snippet)，snippet = before+math+after"""
    before_start = max(0, s - window)
    after_end    = min(len(text), e + window)
    before = text[before_start:s]
    math   = text[s:e]
    after  = text[e:after_end]
    return before, math, after, before + math + after

def main():
    if not os.path.isfile(INPUT_PATH):
        print(f"❌ 未找到输入文件：{INPUT_PATH}")
        return

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        text = f.read()

    line_starts = build_line_index(text)
    spans = collect_math_spans(text)

    print("=== 数学表达式抽取（带上下文导出 CSV） ===")
    print(f"文件: {INPUT_PATH}")
    print(f"捕获总数: {len(spans)}")
    print(f"上下文窗口: 左右各 {WINDOW_CHARS} 字符")
    print(f"CSV: {OUTPUT_CSV}")

    os.makedirs(os.path.dirname(OUTPUT_CSV) or ".", exist_ok=True)
    with open(OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "math_id",
            "type", "syntax",
            "start", "end",
            "start_line", "start_col",
            "end_line", "end_col",
            "context_before",
            "math_text",
            "context_after",
            "snippet"  # before + math + after（直观看原貌）
        ])

        for idx, (s, e, tlabel, slabel, full) in enumerate(spans):
            l1, c1 = offset_to_line_col(s, line_starts)
            l2, c2 = offset_to_line_col(e - 1, line_starts)  # end-1 是最后一个字符
            before, mtxt, after, snippet = clip_context(text, s, e, WINDOW_CHARS)

            writer.writerow([
                idx,
                tlabel, slabel,
                s, e,
                l1, c1,
                l2, c2,
                before, mtxt, after, snippet
            ])

    print("✅ 导出完成。提示：在 Excel 里可以按 math_id 排序查看。")
    print("   想要更长上下文可调 WINDOW_CHARS；不影响定位。")

if __name__ == "__main__":
    main()
