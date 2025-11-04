# -*- coding: utf-8 -*-
# 2025.11.04
# ETL_pipeline_2025.11.04\add_heading_numbers.py
"""
功能说明：
为指定等级的 Markdown 标题自动添加连续编号（从 001. 开始），
可设置排除关键词（如“前言”等）。
"""

import re
from pathlib import Path

# ========== 用户自定义设置 ==========
input_path = Path(r"I:\中国民间传统故事\分卷清洗\yuzhongqu\Chinese Folk Tales_yuzhongqu.md")  # Markdown 文件路径
target_level = 3             # 要编号的标题等级，如 3 表示 ###
start_num = 1                # 起始编号
exclude_keywords = ["前言", "后记", "参考文献"]  # 不编号的标题
# backup = False  ←❌ 已去除备份功能
# ====================================

pattern = re.compile(rf"^[ \t\uFEFF]*#{{{target_level}}}[ \t]*(.+)$", re.M)

with open(input_path, "r", encoding="utf-8") as f:
    content = f.read()

counter = start_num

def should_exclude(title_line: str) -> bool:
    """判断标题是否应被排除"""
    return any(keyword in title_line for keyword in exclude_keywords)

def add_number(match):
    """为匹配的标题添加编号"""
    global counter
    title = match.group(1).strip()

    # 排除特定标题
    if should_exclude(title):
        return match.group(0)

    # 如果标题已包含编号（例如 "### 001."），跳过
    if re.match(r"^\d{1,3}\.", title):
        return match.group(0)

    # ✅ 改动 1：编号后不加空格
    numbered_title = f"{counter:03d}.{title}"  # ← 删除原来的空格
    counter += 1

    # ✅ 改动 2：直接返回新的标题（保持级别）
    return "#" * target_level + " " + numbered_title

# 执行替换
new_content = re.sub(pattern, add_number, content)

# ✅ 打印统计信息
print(f"✅ 已处理 H{target_level} 级标题，从 {start_num:03d} 开始编号。")
print(f"⚙️ 排除字段：{exclude_keywords}")
print(f"🔢 共编号 {counter - start_num} 个标题。")

# ✅ 改动 3：不再备份，直接覆盖原文件
input_path.write_text(new_content, encoding="utf-8")
print("🎉 已直接写回原文件（未创建备份）。")
# 创建时间: 2025/11/4 11:07
