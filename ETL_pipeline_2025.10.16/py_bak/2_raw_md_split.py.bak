# -*- coding: utf-8 -*-
"""
功能：
从 Markdown 文件中剪切：
1. "# 前言" 之前的所有内容；
2. "# index"（或 "# Index"）之后的所有内容；
并将这两部分保存为 *_cut.md；
原文件仅保留 "# 前言" 到 "# index" 之间的内容。
"""

import re
import os
import shutil

# ====== 输入路径 ======
input_path = r"I:\中国民间传统故事\分卷清洗\yunnan\Chinese Folk Tales_yunnan.md"

# ====== 自动生成输出路径 ======
base, ext = os.path.splitext(input_path)
output_path = base + "_cut" + ext
backup_path = input_path + ".bak"

# ====== 读取内容 ======
with open(input_path, "r", encoding="utf-8") as f:
    content = f.read()

# ====== 查找 "# 前言" 与 "# index" ======
pattern_preface = re.search(r"^#\s*前言\s*$", content, flags=re.M)
pattern_index = re.search(r"^#\s*index\s*$", content, flags=re.M | re.I)

if not pattern_preface:
    print("⚠️ 未找到 '# 前言'，未作修改。")
elif not pattern_index:
    print("⚠️ 未找到 '# index' 或 '# Index'，未作修改。")
else:
    start_preface = pattern_preface.start()
    end_index = pattern_index.end()

    # 前言前 + index后
    before_part = content[:start_preface].rstrip()
    after_part = content[end_index:].lstrip()

    # 合并写入输出文件
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(before_part + "\n\n" + after_part)
    print(f"✅ 已生成剪切文件：{output_path}")

    # 备份原文件
    shutil.copy2(input_path, backup_path)
    print(f"💾 已备份原文件为：{backup_path}")

    # 原文件仅保留中间部分
    middle_part = content[start_preface:end_index].strip()
    with open(input_path, "w", encoding="utf-8") as f:
        f.write(middle_part + "\n")
    print(f"✂️ 已更新原文件，仅保留 '# 前言' 至 '# index' 部分。")

print("🎉 处理完成。")
