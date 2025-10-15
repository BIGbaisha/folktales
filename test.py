# -*- coding: utf-8 -*-
"""
检测 '讲述者' 后面紧跟汉字（或有空格后紧跟汉字）的行
打印命中行及前后一行上下文
"""

import re
from pathlib import Path

# ===== 配置 =====
INPUT_PATH = r"I:\中国民间传统故事\老黑解析版本\正式测试\6.4_Chinese Folk Tales_sichuan_cleaned.md"
# =================

# 匹配 “讲述者” 后紧跟（可选空格/不可见字符）+ 汉字
RE_TELLER_INLINE = re.compile(r"讲述者[\s\u200b\u200c\u200d\uFEFF]*[\u4e00-\u9fff]")

def main():
    ip = Path(INPUT_PATH)
    if not ip.exists():
        raise FileNotFoundError(f"文件不存在：{ip}")

    lines = ip.read_text(encoding="utf-8", errors="ignore").splitlines()
    total = 0

    for i, line in enumerate(lines):
        if RE_TELLER_INLINE.search(line):
            total += 1
            print("\n====================")
            print(f"命中行号：{i+1}")
            print(f"上文：{lines[i-1].strip() if i > 0 else '(无)'}")
            print(f"命中：{line.strip()}")
            print(f"下文：{lines[i+1].strip() if i+1 < len(lines) else '(无)'}")

    print("\n--------------------")
    print(f"共检测到 {total} 行含 '讲述者+汉字' 的情况。")

if __name__ == "__main__":
    main()
# 创建时间: 2025/10/15 11:05