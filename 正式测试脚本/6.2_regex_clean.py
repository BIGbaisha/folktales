# 创建时间: 2025/10/11 12:05
# -*- coding: utf-8 -*-
"""
三阶段正则清洗（仅打印报告；输出1个清洗后的MD文件）
1) 抽取数学 -> 用 [[MATH_i]] 占位（支持 $...$, $$...$$, \(...\), \[...\]，跨行）
2) 清洗标题：只处理井号后的标题文本，不改 Markdown 语法符号
3) 清洗正文：避开代码块/行内代码/数学占位符

注意：
- 不生成 CSV；只在控制台打印统计与预览
- 硬编码路径：INPUT_PATH / OUTPUT_PATH
"""

import os
import re
from typing import List, Tuple

# ========= 硬编码路径 =========
INPUT_PATH  = r"I:\中国民间传统故事\老黑解析版本\正式测试\5_Chinese Folk Tales_sichuan_normalized.md"
OUTPUT_PATH = r"I:\中国民间传统故事\老黑解析版本\正式测试\6.2_Chinese Folk Tales_sichuan_cleaned.md"

# ========= 通用：全角/半角、空白、标点 =========
# 全角数字与英字转半角（按需可扩展）
_FW2HW_MAP = {
    **{ord(f): ord('0') + i for i, f in enumerate('０１２３４５６７８９')},
    **{ord(f): ord('A') + i for i, f in enumerate('ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ')},
    **{ord(f): ord('a') + i for i, f in enumerate('ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ')},
    ord('　'): ord(' '),
}

def to_halfwidth(s: str) -> str:
    return s.translate(_FW2HW_MAP)

# 统一一些常见 OCR 标点/空白（非常保守；不改 Markdown 结构符号）
RE_MULTI_SPACE = re.compile(r"[ \t\u00A0]+")  # 连续空白
RE_WEIRD_SP    = re.compile(r"[\u2000-\u200B\u202F\u2060]+")  # 各类零宽/细空

# 将“奇怪点号/间隔符”收敛为普通点或间隔符（用于标题与正文）
DOT_LIKE = "·・•‧∙◦。．·"
DASH_LIKE = "—–-‒―─"
RE_DOT_LIKE  = re.compile(f"[{re.escape(DOT_LIKE)}]+")
RE_DASH_LIKE = re.compile(f"[{re.escape(DASH_LIKE)}]+")

def normalize_light_punct(s: str) -> str:
    s = RE_WEIRD_SP.sub(" ", s)
    s = RE_DOT_LIKE.sub("·", s)       # 统一为中点
    s = RE_DASH_LIKE.sub("——", s)     # 统一为中文破折号
    s = RE_MULTI_SPACE.sub(" ", s)
    return s

# ========= 数学抽取（优先于一切）=========
# 支持：$$...$$（多行）、$...$（行内）、\(...\)、\[...\]
RE_MATH_BLOCK = re.compile(r"\$\$(.+?)\$\$", re.DOTALL)
RE_MATH_INL   = re.compile(r"(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)")
RE_MATH_PARE  = re.compile(r"\\\((.+?)\\\)")
RE_MATH_BRKT  = re.compile(r"\\\[(.+?)\\\]", re.DOTALL)

def extract_math_placeholders(text: str) -> Tuple[str, List[str]]:
    """
    将文中数学块替换为 [[MATH_i]]，返回 (替换后的文本, 数学列表)
    替换顺序：先块，再行内，避免嵌套冲突
    """
    math_store: List[str] = []

    def _sub_block(m):
        math_store.append(m.group(0))
        return f"[[MATH_{len(math_store)-1}]]"

    def _sub_inl(m):
        math_store.append(m.group(0))
        return f"[[MATH_{len(math_store)-1}]]"

    # 先 $$...$$ 再 \[...\]（都可能跨行）
    text = RE_MATH_BLOCK.sub(_sub_block, text)
    text = RE_MATH_BRKT.sub(_sub_block, text)
    # 再行内
    text = RE_MATH_INL.sub(_sub_inl, text)
    text = RE_MATH_PARE.sub(_sub_inl, text)

    return text, math_store

def restore_math_placeholders(text: str, math_store: List[str]) -> str:
    def repl(m):
        idx = int(m.group(1))
        return math_store[idx] if 0 <= idx < len(math_store) else m.group(0)
    return re.sub(r"\[\[MATH_(\d+)\]\]", repl, text)

# ========= Markdown 语法保护：代码块 / 行内代码 =========
RE_FENCE = re.compile(r"^```.*$")   # 三反引号围栏
RE_INLINE_CODE = re.compile(r"`[^`\n]*`")  # 行内代码：一行内不跨行

def split_blocks_by_code_fence(lines: List[str]) -> List[Tuple[str, List[str]]]:
    """
    将文档按 fenced code blocks 切分。返回 [(type, chunk_lines)]
    type in {"code", "text"}
    """
    out = []
    buf = []
    in_code = False
    for ln in lines:
        if RE_FENCE.match(ln.rstrip("\n")):
            # 切分点也应包含在 code 块里
            buf.append(ln)
            if in_code:
                # 结束 code
                out.append(("code", buf))
                buf = []
            else:
                # 开始 code，之前的 text flush
                if buf[:-1]:
                    out.append(("text", buf[:-1]))
                buf = [ln]  # 新 code 块起始
                in_code = True
        else:
            buf.append(ln)

    if buf:
        out.append(("code" if in_code else "text", buf))
    return out

# ========= 标题与正文清洗 =========
RE_HEADING = re.compile(r"^(?P<hash>#{1,6})(?P<sp>\s*)(?P<title>.*)$")
# 小心：标题清洗只作用在 title 部分，保留 hash 与空格

def clean_heading_line(line: str) -> str:
    m = RE_HEADING.match(line)
    if not m:
        return line
    hashes = m.group("hash")
    sp     = m.group("sp")
    title  = m.group("title")

    # 不触碰 Markdown 链接/代码/强调标记，仅做温和替换
    original = title
    title = to_halfwidth(title)
    # 行内代码不清洗：用占位再还原
    code_inl = []
    def _hold_code(mm):
        code_inl.append(mm.group(0))
        return f"[[CODE_{len(code_inl)-1}]]"
    title = RE_INLINE_CODE.sub(_hold_code, title)

    title = normalize_light_punct(title)
    title = title.strip()

    # 还原行内代码
    def _back_code(mm):
        idx = int(mm.group(1))
        return code_inl[idx]
    title = re.sub(r"\[\[CODE_(\d+)\]\]", _back_code, title)

    # 至少一个空格分隔井号与标题
    sp = " " if sp == "" else sp
    return f"{hashes}{sp}{title}"

def clean_body_line(line: str) -> str:
    # 保留行内代码块：先占位
    code_inl = []
    def _hold_code(mm):
        code_inl.append(mm.group(0))
        return f"[[CODE_{len(code_inl)-1}]]"
    tmp = RE_INLINE_CODE.sub(_hold_code, line)

    # 数字/英字转半角；轻量标点/空白收敛
    tmp = to_halfwidth(tmp)
    tmp = normalize_light_punct(tmp)

    # 还原行内代码
    def _back_code(mm):
        idx = int(mm.group(1))
        return code_inl[idx]
    tmp = re.sub(r"\[\[CODE_(\d+)\]\]", _back_code, tmp)

    return tmp

# ========= 主流程 =========
def main():
    if not os.path.isfile(INPUT_PATH):
        print(f"❌ 未找到输入文件：{INPUT_PATH}")
        return

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        raw = f.read()

    # 阶段 1：抽取数学
    text_math_held, math_store = extract_math_placeholders(raw)
    print("【阶段1】数学片段抽取")
    print(f"  - 捕获数学片段数量：{len(math_store)}")
    for i, mexpr in enumerate(math_store[:10]):  # 预览前10条
        preview = mexpr.replace("\n", " ")[:120]
        print(f"    #{i}: {preview}{'...' if len(preview) == 120 else ''}")
    if len(math_store) > 10:
        print(f"    …（其余 {len(math_store)-10} 条略）")

    # 将文档拆成 code 与 text 区块，避免清洗误触代码块
    lines = text_math_held.splitlines(True)
    blocks = split_blocks_by_code_fence(lines)

    cleaned_lines: List[str] = []
    heading_cnt = 0
    body_cnt    = 0

    # 阶段 2 & 3：标题、正文分别清洗（跳过 code 块）
    for btype, chunk in blocks:
        if btype == "code":
            cleaned_lines.extend(chunk)  # 原样保留代码块
            continue
        # text 块：按行处理
        for ln in chunk:
            if RE_HEADING.match(ln):
                cleaned = clean_heading_line(ln)
                cleaned_lines.append(cleaned)
                heading_cnt += 1
            else:
                cleaned = clean_body_line(ln)
                cleaned_lines.append(cleaned)
                body_cnt += 1

    cleaned_text = "".join(cleaned_lines)

    # 阶段 4：数学占位符还原
    restored_text = restore_math_placeholders(cleaned_text, math_store)

    # 写出
    os.makedirs(os.path.dirname(OUTPUT_PATH) or ".", exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(restored_text)

    # 报告
    print("\n【阶段2】标题清洗完成")
    print(f"  - 处理标题行数：{heading_cnt}")
    print("  - 仅清洗井号后的标题内容，保留 Markdown 井号与间距")
    print("【阶段3】正文清洗完成")
    print(f"  - 处理正文行数：{body_cnt}")
    print("  - 已避开 fenced code 与行内代码、数学片段")
    print("\n✅ 已输出：", OUTPUT_PATH)

if __name__ == "__main__":
    main()
