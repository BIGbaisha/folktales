# -*- coding: utf-8 -*-
"""
最小改动脚本：
1) 去掉所有 H3（###）标题中的中点“·”（仅作用于标题文字部分）。
2) 行内经纬度 $97^{\\circ}12^{\\prime}$ 这类，输出为具体数值 97°12′；
   其他所有数学插入（$...$、\\(...\\)、\\[...\\]、$$...$$）以及内容统统删除。
"""

import re
from pathlib import Path

# ====== 硬编码路径（自行修改）======
INPUT_PATH  = r"I:\中国民间传统故事\老黑解析版本\正式测试\6_Chinese Folk Tales_sichuan_cleaned.md"
OUTPUT_PATH = r"I:\中国民间传统故事\老黑解析版本\正式测试\6.3_Chinese Folk Tales_sichuan_cleaned.md"
# ==================================


# ---------- 正则：H3 标题 ----------
RE_H3 = re.compile(r"^(?P<hash>#{3})(?P<sp>\s*)(?P<title>.*)$")

# ---------- 正则：数学插入 ----------
# 1) 块级数学（删除）
RE_MATH_DOLLAR_BLOCK = re.compile(r"\$\$(.+?)\$\$", re.DOTALL)   # $$...$$
RE_MATH_BRACKET      = re.compile(r"\\\[(.+?)\\\]", re.DOTALL)   # \[...\]

# 2) 行内数学（$...$ / \(...\)）
RE_MATH_INLINE_DOLLAR = re.compile(r"(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)", re.DOTALL)
RE_MATH_INLINE_PAREN  = re.compile(r"\\\((.+?)\\\)", re.DOTALL)

# 经纬度专用匹配（只接受 97^{\circ}12^{\prime} 这种结构；允许适度空格）
RE_LATLON_TEX = re.compile(
    r"""^\s*
        (?P<deg>\d{1,3})\s*         # 度：1-3 位数字
        \^\{\s*\\circ\s*\}\s*       # ^{\circ}
        (?P<min>\d{1,2})\s*         # 分：1-2 位数字
        \^\{\s*\\prime\s*\}\s*      # ^{\prime}
        $""",
    re.VERBOSE,
)

def replace_inline_math(m: re.Match) -> str:
    """
    行内 $...$ 内容处理：
    - 若是经纬度 ^{\circ}/^{\prime} 结构 -> 输出数值，如 97°12′
    - 否则删除整段（返回空串）
    """
    content = m.group(1).strip()
    mm = RE_LATLON_TEX.match(content)
    if mm:
        return f"{mm.group('deg')}°{mm.group('min')}′"
    return ""  # 其他行内数学全部删除

def replace_inline_paren_math(m: re.Match) -> str:
    """同上"""
    content = m.group(1).strip()
    mm = RE_LATLON_TEX.match(content)
    if mm:
        return f"{mm.group('deg')}°{mm.group('min')}′"
    return ""

def process_text(text: str) -> str:
    lines = text.splitlines(keepends=True)
    out_lines = []

    for ln in lines:
        # 1) H3 标题：去掉标题文本中的“·”
        mh3 = RE_H3.match(ln.rstrip("\n"))
        if mh3:
            h, sp, title = mh3.group("hash", "sp", "title")
            title = title.replace("·", "")  # 仅此处去中点
            out_lines.append(f"{h}{sp}{title}\n")
            continue

        out_lines.append(ln)

    out_text = "".join(out_lines)

    # 2) 数学插入处理
    # 2.1 删除所有块级数学
    out_text = RE_MATH_DOLLAR_BLOCK.sub("", out_text)
    out_text = RE_MATH_BRACKET.sub("", out_text)

    # 2.2 行内数学：经纬度输出数值，其他删除
    out_text = RE_MATH_INLINE_DOLLAR.sub(replace_inline_math, out_text)
    out_text = RE_MATH_INLINE_PAREN.sub(replace_inline_paren_math, out_text)

    return out_text

def main():
    ip = Path(INPUT_PATH)
    if not ip.exists():
        raise FileNotFoundError(f"输入文件不存在：{ip}")
    text = ip.read_text(encoding="utf-8", errors="ignore")
    out = process_text(text)
    Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)
    Path(OUTPUT_PATH).write_text(out, encoding="utf-8")
    print("✅ 完成：", OUTPUT_PATH)

if __name__ == "__main__":
    main()
