# 创建时间: 2025/11/4 15:36
# -*- coding: utf-8 -*-
# 功能：在指定标题层级后插入 markdown 引用行
# 示例：### 故事标题  →  ### 故事标题\n\n> 地点：渝中区

import re

# ===== 参数设置 =====
INPUT_FILE = r"I:\中国民间传统故事\分卷清洗\yuzhongqu\6.5_Chinese Folk Tales_yuzhongqu.md"      # 输入文件
OUTPUT_FILE = r"I:\中国民间传统故事\分卷清洗\yuzhongqu\6.6_Chinese Folk Tales_yuzhongqu.md"    # 输出文件
TARGET_LEVEL = 3             # 目标标题层级，如 3 表示 "###"
INSERT_TEXT = "> 地点：渝中区"  # 要插入的内容
# ===================

pattern = re.compile(rf'^(#{{{TARGET_LEVEL}}}\s.*)$', re.M)

def add_quote_line(content):
    def insert_after_heading(match):
        heading = match.group(1)
        return f"{heading}\n\n{INSERT_TEXT}\n"
    return pattern.sub(insert_after_heading, content)

if __name__ == "__main__":
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        text = f.read()

    new_text = add_quote_line(text)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(new_text)

    print(f"✅ 已在所有 {TARGET_LEVEL} 级标题下插入：{INSERT_TEXT}")
    print(f"输出文件：{OUTPUT_FILE}")
