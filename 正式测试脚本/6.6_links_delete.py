# 创建时间: 2025/10/15 11:17
# -*- coding: utf-8 -*-
"""
Markdown 清洗脚本 v4
--------------------------------
功能：
1️⃣ 检测或清理各类链接；
2️⃣ 各级标题前后有且仅有一个空行；
3️⃣ 普通段落之间也有且仅有一个空行。
"""

import re
from pathlib import Path

# ===== 配置 =====
INPUT_PATH  =r"I:\中国民间传统故事\老黑解析版本\正式测试\6.5_Chinese Folk Tales_sichuan_cleaned.md"
OUTPUT_PATH = r"I:\中国民间传统故事\老黑解析版本\正式测试\6.6_Chinese Folk Tales_sichuan_cleaned.md"

REMOVE_LINKS = False   # True=仅检测打印; False=移除链接
# =================

# --- 正则定义 ---
RE_HEADING = re.compile(r"^\s*#{1,6}\s+.*$")
RE_LINK_MD = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")    # [text](url)
RE_LINK_ANGLE = re.compile(r"<(https?://[^>]+)>")      # <http://xxx>
RE_LINK_BARE = re.compile(r"https?://[^\s)\]]+")       # 裸url
RE_EMPTY = re.compile(r"^[\s\u200b\u200c\u200d\uFEFF]*$")


# === 功能模块 ===

def detect_links(text: str):
    """检测所有类型的链接"""
    md_links = RE_LINK_MD.findall(text)
    angle_links = RE_LINK_ANGLE.findall(text)
    bare_links = RE_LINK_BARE.findall(text)

    total = len(md_links) + len(angle_links) + len(bare_links)
    print(f"\n🔍 检测到 {total} 个链接：")

    if md_links:
        print(f"  • Markdown 链接 {len(md_links)} 个：")
        for t, url in md_links[:10]:
            print(f"    [{t}]({url})")
    if angle_links:
        print(f"  • 尖括号链接 {len(angle_links)} 个（示例前3个）：")
        for u in angle_links[:3]:
            print(f"    <{u}>")
    if bare_links:
        print(f"  • 裸URL {len(bare_links)} 个（示例前3个）：")
        for u in bare_links[:3]:
            print(f"    {u}")

    print("\n✅ 当前为检测模式，不执行删除。")


def remove_links_from_text(text: str) -> str:
    """移除所有类型的链接"""
    text = RE_LINK_MD.sub(r"\1", text)
    text = RE_LINK_ANGLE.sub("", text)
    text = RE_LINK_BARE.sub("", text)
    return text


def normalize_blank_lines(lines):
    """
    确保标题与正文段落前后空行仅1行
    - 标题前后保证1行空行；
    - 段落之间保证1行空行；
    """
    output = []
    prev_blank = True  # 文件开头视为空行
    for i, line in enumerate(lines):
        stripped = line.rstrip("\r\n")

        # 标题行
        if RE_HEADING.match(stripped):
            if not prev_blank:
                output.append("\n")
            output.append(stripped + "\n")
            output.append("\n")
            prev_blank = True
            continue

        # 空行
        if RE_EMPTY.match(stripped):
            if not prev_blank:
                output.append("\n")
                prev_blank = True
            continue

        # 普通正文
        output.append(stripped + "\n")
        prev_blank = False

    if not output or not output[-1].strip():
        pass
    else:
        output.append("\n")

    return output


# === 主程序 ===

def main():
    ip = Path(INPUT_PATH)
    if not ip.exists():
        raise FileNotFoundError(f"输入文件不存在：{ip}")

    text = ip.read_text(encoding="utf-8", errors="ignore")

    if REMOVE_LINKS:
        # 仅检测 & 打印链接
        detect_links(text)
        return

    # 真正清理模式
    print("🧹 执行链接清理 + 空行规范化 ...")
    text = remove_links_from_text(text)
    lines = text.splitlines(True)
    formatted_lines = normalize_blank_lines(lines)
    Path(OUTPUT_PATH).write_text("".join(formatted_lines), encoding="utf-8")

    print(f"\n✅ 已清理并输出结果：{OUTPUT_PATH}")


if __name__ == "__main__":
    main()
