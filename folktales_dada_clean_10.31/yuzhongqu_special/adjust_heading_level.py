# -*- coding: utf-8 -*-
# 2025.11.04
# ETL_pipeline_2025.11.04\adjust_heading_level.py
"""
功能说明：
将指定等级的 Markdown 标题调整为目标等级，
支持排除包含特定关键词的标题。
"""

import re
from pathlib import Path

# ========== 用户自定义设置 ==========
input_path = Path(r"I:\中国民间传统故事\分卷清洗\sichuan\Chinese Folk Tales_sichuan.md")  # Markdown 文件路径
source_level = 1          # 原始标题等级（如 1 表示 #）
target_level = 3          # 目标标题等级（如 3 表示 ###）
exclude_keywords = ["前言", "后记", "参考文献"]  # 排除关键词
backup = True             # 是否备份原文件
# ====================================

# ✅ 改进正则：支持BOM、空格、制表符、无空格标题
pattern = re.compile(rf"^[ \t\uFEFF]*#{{{source_level}}}[ \t]*(.+)$", re.M)

with open(input_path, "r", encoding="utf-8") as f:
    content = f.read()


def should_exclude(title_line: str) -> bool:
    """判断该标题是否应被排除"""
    return any(keyword in title_line for keyword in exclude_keywords)


def adjust_heading(match):
    """执行标题等级调整"""
    title = match.group(1).strip()
    if should_exclude(title):
        return match.group(0)  # 原样返回
    return "#" * target_level + " " + title


# ========== 进行替换 ==========
new_content = re.sub(pattern, adjust_heading, content)

# ✅ 输出匹配统计信息（便于验证）
matches = pattern.findall(content)
print(f"🔍 Matched {len(matches)} headings at level H{source_level}.")
if matches:
    print("👉 Example(s):", matches[:3])

# ✅ 备份原文件
if backup:
    bak_path = input_path.with_suffix(".bak.md")
    bak_path.write_text(content, encoding="utf-8")
    print(f"💾 已备份原文件：{bak_path}")

# ✅ 写回修改结果
input_path.write_text(new_content, encoding="utf-8")
print(f"✅ 已调整标题等级：H{source_level} → H{target_level}")
print(f"⚙️ 排除字段：{exclude_keywords}")
print("🎉 处理完成。")
