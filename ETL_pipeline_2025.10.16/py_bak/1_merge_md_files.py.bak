# 创建时间: 2025/10/10 11:08
# -*- coding: utf-8 -*-
"""
合并多个 Markdown 文件。
- 保留 4 个输入路径（可有空）
- 仅处理存在且非空的文件
- 合并时各文件之间空一行
"""

import os

# ====== 硬编码输入输出 ======
inputs = [
    r"I:\中国民间传统故事\分卷清洗\yunnan\Chinese Folk Tales_yunnan_a_1.md",
    r"I:\中国民间传统故事\分卷清洗\yunnan\Chinese Folk Tales_yunnan_a_2.md",
    r"I:\中国民间传统故事\分卷清洗\yunnan\Chinese Folk Tales_yunnan_b_1.md",
    r"I:\中国民间传统故事\分卷清洗\yunnan\Chinese Folk Tales_yunnan_b_2.md"
]
output_path = r"I:\中国民间传统故事\分卷清洗\yunnan\Chinese Folk Tales_yunnan.md"

# ====== 合并逻辑 ======
merged_parts = []

for path in inputs:
    if not path or not os.path.exists(path):
        print(f"⚠️ 跳过不存在的文件：{path}")
        continue

    # 读取内容
    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            print(f"⚠️ 跳过空文件：{path}")
            continue

        merged_parts.append(content)
        print(f"✅ 已添加：{path}")

# ====== 输出结果 ======
if merged_parts:
    merged_text = "\n\n".join(merged_parts) + "\n"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(merged_text)
    print(f"\n🎉 合并完成！输出文件：{output_path}")
else:
    print("⚠️ 没有可合并的文件。未生成输出。")
