# 创建时间: 2025/10/10 11:03
# -*- coding: utf-8 -*-
"""
功能：
1. 从 Markdown 文件中找到第一个 "# 前言"（H1）行；
2. 将其之前的内容保存到新文件；
3. 修改原文件，使其不再包含这部分内容（即从 "# 前言" 起保留）。
"""

import re

# ====== 硬编码输入输出路径 ======
input_path = r"I:\中国民间传统故事\老黑解析版本\正式测试\Chinese Folk Tales_sichuan_a.md"  # 原始 Markdown 文件
preface_output_path = r"I:\中国民间传统故事\老黑解析版本\正式测试\Chinese Folk Tales_sichuan_a.prologue.md"  # 截取出的前言前部分

# ====== 主逻辑 ======
with open(input_path, "r", encoding="utf-8") as f:
    content = f.read()

# 匹配 "# 前言" （考虑空格和中英文符号）
match = re.search(r"^#\s*前言\s*$", content, flags=re.M)

if match:
    cutoff = match.start()
    before_part = content[:cutoff].rstrip()
    after_part = content[cutoff:].lstrip("\n")

    # 保存截取部分
    with open(preface_output_path, "w", encoding="utf-8") as f:
        f.write(before_part + "\n")

    # 覆盖原文件（删除前部分）
    with open(input_path, "w", encoding="utf-8") as f:
        f.write(after_part)

    print(f"✅ 已截取 '# 前言' 之前的内容到 {preface_output_path}")
    print(f"✅ 已更新原文件 {input_path}，其开头从 '# 前言' 开始。")
else:
    print("⚠️ 未找到 '# 前言'，未作任何修改。")
