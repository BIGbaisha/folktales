# 创建时间: 2025/10/31 9:52
# -*- coding: utf-8 -*-
# ==========================================================
# 正则清洗脚本（融合版）
# Version: v2025.11
# 功能：
# 1️⃣ 自动执行 normalize_chinese_text()（全角→半角、零宽符、换行标准化）
# 2️⃣ 保留 6.2 原有数学保护 + 标题清洗 + 正文清洗逻辑
# 3️⃣ 融合 5.3：删除所有链接、统一空行排版
# 4️⃣ 使用统一 header（load_text, save_text, log_stage, log_summary）
# ==========================================================

import re
import sys
from typing import List, Tuple
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1])) # ✅ 父路径从0级开始算
# --- 通用模块导入 ---
from utils.text_normalizer import normalize_chinese_text
from utils.template_script_header_manual import (
    load_text, save_text, log_stage, log_summary
)

# ========= 路径配置（人工复核模式） =========
REGION = "sichuan"
INPUT_PATH  = Path(r"I:\中国民间传统故事\分卷清洗\sichuan\Chinese Folk Tales_sichuan.md")
OUTPUT_PATH = Path(r"I:\中国民间传统故事\分卷清洗\sichuan\6.2_Chinese Folk Tales_sichuan.md")

# ========= 链接清理 =========
RE_LINK_MD = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")        # [text](url)
RE_IMAGE_MD = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")      # ![alt](url)
RE_LINK_ANGLE = re.compile(r"<(https?://[^>]+)>")          # <http://xxx>
RE_LINK_BARE = re.compile(r"https?://[^\s)\]]+")           # Bare URL

# ========= 空行规范 =========
def normalize_blank_lines(text: str) -> str:
    """
    保证空行规范化：
    - 标题前后至少一行空行；
    - 段落间仅保留一行空行；
    - 文件末尾保持单换行。
    """
    lines = text.splitlines()
    RE_HEADING = re.compile(r"^\s*#{1,6}\s+.*$")
    RE_EMPTY = re.compile(r"^[\s\u200b\u200c\u200d\uFEFF]*$")
    output = []
    prev_blank = True

    for line in lines:
        stripped = line.rstrip("\r\n")
        if RE_HEADING.match(stripped):
            if not prev_blank:
                output.append("")
            output.append(stripped)
            output.append("")
            prev_blank = True
            continue
        if RE_EMPTY.match(stripped):
            if not prev_blank:
                output.append("")
                prev_blank = True
            continue
        output.append(stripped)
        prev_blank = False

    if output and output[-1].strip():
        output.append("")
    return "\n".join(output)


# ========= Markdown 正则保护 =========
RE_FENCE = re.compile(r"^```.*$")
RE_INLINE_CODE = re.compile(r"`[^`\n]*`")

# ========= 数学保护 =========
RE_MATH_BLOCK = re.compile(r"\$\$(.+?)\$\$", re.DOTALL)
RE_MATH_INL   = re.compile(r"(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)")
RE_MATH_PARE  = re.compile(r"\\\((.+?)\\\)")
RE_MATH_BRKT  = re.compile(r"\\\[(.+?)\\\]", re.DOTALL)


def extract_math_placeholders(text: str) -> Tuple[str, List[str]]:
    """抽取数学公式占位符"""
    math_store: List[str] = []

    def _sub_block(m):
        math_store.append(m.group(0))
        return f"[[MATH_{len(math_store)-1}]]"

    text = RE_MATH_BLOCK.sub(_sub_block, text)
    text = RE_MATH_BRKT.sub(_sub_block, text)

    def _sub_inl(m):
        math_store.append(m.group(0))
        return f"[[MATH_{len(math_store)-1}]]"

    text = RE_MATH_INL.sub(_sub_inl, text)
    text = RE_MATH_PARE.sub(_sub_inl, text)
    return text, math_store


def restore_math_placeholders(text: str, math_store: List[str]) -> str:
    def repl(m):
        idx = int(m.group(1))
        return math_store[idx] if 0 <= idx < len(math_store) else m.group(0)
    return re.sub(r"\[\[MATH_(\d+)\]\]", repl, text)


# ========= 行级清洗函数 =========
RE_HEADING = re.compile(r"^(?P<hash>#{1,6})(?P<sp>\s*)(?P<title>.*)$")

def clean_heading_line(line: str) -> str:
    """标题行清洗逻辑"""
    m = RE_HEADING.match(line)
    if not m:
        return line
    hashes, sp, title = m.group("hash"), m.group("sp"), m.group("title")

    code_inl = []
    def _hold_code(mm):
        code_inl.append(mm.group(0))
        return f"[[CODE_{len(code_inl)-1}]]"
    title = RE_INLINE_CODE.sub(_hold_code, title)

    title = normalize_chinese_text(title)
    title = re.sub(r'(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])', '', title)
    title = re.sub(r'(?<=[\u4e00-\u9fff])\s+(?=[\.\,\!\?\;\:\-\—])', '', title)
    title = re.sub(r'(?<=[\.\,\!\?\;\:\-\—])\s+(?=[\u4e00-\u9fff])', '', title)

    def _back_code(mm):
        idx = int(mm.group(1))
        return code_inl[idx]
    title = re.sub(r"\[\[CODE_(\d+)\]\]", _back_code, title)
    sp = " " if sp == "" else sp
    return f"{hashes}{sp}{title}"


def clean_body_line(line: str) -> str:
    """正文清洗逻辑 + 链接删除（融合自5.3）"""
    code_inl = []
    def _hold_code(mm):
        code_inl.append(mm.group(0))
        return f"[[CODE_{len(code_inl)-1}]]"
    tmp = RE_INLINE_CODE.sub(_hold_code, line)

    tmp = normalize_chinese_text(tmp)

    # 删除各种链接形式（融合自5.3）
    tmp = RE_IMAGE_MD.sub("", tmp)
    tmp = RE_LINK_MD.sub(r"\1", tmp)
    tmp = RE_LINK_ANGLE.sub("", tmp)
    tmp = RE_LINK_BARE.sub("", tmp)

    def _back_code(mm):
        idx = int(mm.group(1))
        return code_inl[idx]
    tmp = re.sub(r"\[\[CODE_(\d+)\]\]", _back_code, tmp)
    return tmp


# ========= 代码块分割 =========
def split_blocks_by_code_fence(lines: List[str]) -> List[Tuple[str, List[str]]]:
    """按 fenced code block 切分，避免误清洗"""
    out, buf, in_code = [], [], False
    for ln in lines:
        if RE_FENCE.match(ln.rstrip("\n")):
            buf.append(ln)
            if in_code:
                out.append(("code", buf))
                buf, in_code = [], False
            else:
                if buf[:-1]:
                    out.append(("text", buf[:-1]))
                buf, in_code = [ln], True
        else:
            buf.append(ln)
    if buf:
        out.append(("code" if in_code else "text", buf))
    return out


# ========= 主函数 =========
def main():
    log_stage("阶段1：加载与标准化")
    raw = load_text(INPUT_PATH)

    log_stage("阶段2：数学片段抽取")
    text_math_held, math_store = extract_math_placeholders(raw)
    print(f"🔢 捕获数学片段：{len(math_store)}")

    lines = text_math_held.splitlines(True)
    blocks = split_blocks_by_code_fence(lines)

    cleaned_lines: List[str] = []
    heading_cnt = body_cnt = 0

    log_stage("阶段3：标题与正文清洗（融合链接删除）")
    for btype, chunk in blocks:
        if btype == "code":
            cleaned_lines.extend(chunk)
            continue
        for ln in chunk:
            if RE_HEADING.match(ln):
                cleaned = clean_heading_line(ln)
                cleaned_lines.append(cleaned.rstrip("\r\n") + "\n")
                heading_cnt += 1
            else:
                cleaned = clean_body_line(ln)
                cleaned_lines.append(cleaned.rstrip("\r\n") + "\n")
                body_cnt += 1

    cleaned_text = "".join(cleaned_lines)

    log_stage("阶段4：数学还原与空行规范化")
    restored_text = restore_math_placeholders(cleaned_text, math_store)
    restored_text = normalize_blank_lines(restored_text)

    log_stage("阶段5：输出结果")
    save_text(OUTPUT_PATH, restored_text)
    log_summary("正则清洗与链接清理", INPUT_PATH, OUTPUT_PATH)

if __name__ == "__main__":
    main()
