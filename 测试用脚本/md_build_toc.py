# -*- coding: utf-8 -*-
"""
md_build_toc.py — 从 Markdown 提取标题并重建 TOC（目录），同级去重
- 输入：硬编码 INPUT_PATH
- 输出：
  1) *.toc.md         （仅目录）
  2) *.with_toc.md    （在原文中用标记插入/替换 TOC 后的完整文档）
- 去重策略：同级（相同 level）内去重；从第二次开始追加 -1, -2…
"""

import os
import re
import unicodedata
from collections import defaultdict
from typing import List, Tuple

# ========= 按需修改 =========
INPUT_PATH = r"I:\中国民间传统故事\老黑解析版本\v-Chinese Folk Tales_sichuan_shang.md"
INSERT_TOC_IN_DOC = True         # True: 生成 *.with_toc.md；False: 只输出 *.toc.md
TOC_TITLE = "## 目录"            # 目录标题
TOC_START = "<!-- TOC START -->"
TOC_END   = "<!-- TOC END -->"
INDENT_PER_LEVEL = 2             # TOC 缩进空格数（每级）

# ========= 标题提取：^#{1,6}\s+... =========
HEADING_PATTERN = re.compile(r'^(#{1,6})\s+(.+?)\s*$', re.MULTILINE)

# 保留中文、字母、数字、连字符与空格，去大多西文标点
_PUNCT_RE = re.compile(r"[^\w\u4e00-\u9fff\- ]+", re.UNICODE)

def slugify_github_like(text: str) -> str:
    """
    简化版 GitHub 风格锚点：
      - Unicode NFKD
      - 去大多标点，空格→'-'，多连字符折叠
      - 小写；中文保留
    """
    t = unicodedata.normalize("NFKD", text)
    t = _PUNCT_RE.sub("", t)
    t = t.replace("_", " ")
    t = "-".join(t.strip().split())
    t = re.sub(r"-{2,}", "-", t)
    return t.lower() or "section"

def extract_headings(md_text: str) -> List[Tuple[int, str, str]]:
    """返回 [(level, title, slug_base), ...]"""
    out = []
    for m in HEADING_PATTERN.finditer(md_text):
        hashes, title = m.group(1), m.group(2).strip()
        level = len(hashes)
        base = slugify_github_like(title)
        out.append((level, title, base))
    return out

def build_unique_slugs_same_level(headings: List[Tuple[int, str, str]]) -> List[Tuple[int, str, str]]:
    """
    同级（相同 level）内去重：
      - 第一次出现：不加后缀
      - 第二次及以后：追加 -1, -2, ...
    """
    counter = defaultdict(int)  # key: (level, base) -> count
    out = []
    for level, title, base in headings:
        n = counter[(level, base)]
        slug = base if n == 0 else f"{base}-{n}"
        counter[(level, base)] += 1
        out.append((level, title, slug))
    return out

def render_toc(headings_with_slugs: List[Tuple[int, str, str]]) -> str:
    """渲染缩进无序列表目录"""
    lines = []
    for level, title, slug in headings_with_slugs:
        indent = " " * ((level - 1) * INDENT_PER_LEVEL)
        lines.append(f"{indent}- [{title}](#{slug})")
    return "\n".join(lines)

def insert_or_replace_toc(md_text: str, toc_block: str) -> str:
    """用标记插入/替换 TOC；不存在标记则文首插入"""
    block = f"{TOC_START}\n{TOC_TITLE}\n\n{toc_block}\n{TOC_END}"
    if TOC_START in md_text and TOC_END in md_text:
        pattern = re.compile(re.escape(TOC_START) + r".*?" + re.escape(TOC_END), flags=re.DOTALL)
        return pattern.sub(block, md_text, count=1)
    return block + "\n\n" + md_text.lstrip("\ufeff")

def main():
    if not os.path.isfile(INPUT_PATH):
        raise FileNotFoundError(f"File not found: {INPUT_PATH}")

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        md = f.read()

    headings = extract_headings(md)
    if not headings:
        print("No headings found.")
    dedup = build_unique_slugs_same_level(headings)   # ← 同级去重
    toc_body = render_toc(dedup)

    base, ext = os.path.splitext(INPUT_PATH)

    # 仅 TOC
    toc_path = f"{base}.toc.md"
    with open(toc_path, "w", encoding="utf-8") as fw:
        fw.write(TOC_TITLE + "\n\n" + toc_body + "\n")
    print(f"TOC written to: {toc_path}")

    # 插入/替换 TOC 的完整文档
    if INSERT_TOC_IN_DOC:
        out_doc = f"{base}.with_toc{ext}"
        new_md = insert_or_replace_toc(md, toc_body)
        with open(out_doc, "w", encoding="utf-8") as fw:
            fw.write(new_md)
        print(f"Document with TOC written to: {out_doc}")

if __name__ == "__main__":
    main()
