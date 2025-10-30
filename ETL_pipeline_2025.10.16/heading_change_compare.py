# -*- coding: utf-8 -*-
# 创建时间: 2025/10/30
# 版本: v2025.10
"""
list_h2_headings.py
----------------------------------------
功能：
- 列出两个 Markdown 文件中所有 H2 标题
- 按出现顺序打印，方便人工对比
"""

import re
from pathlib import Path

# ==========================================================
# 文件路径配置（自行修改）
# ==========================================================
INPUT_PATH_1 = r"I:\中国民间传统故事\分卷清洗\guizhou\5_Chinese Folk Tales_guizhou.md"
INPUT_PATH_2 = r"I:\中国民间传统故事\分卷清洗\guizhou\6.2_Chinese Folk Tales_guizhou.md"

# ==========================================================
# 匹配严格的 H2 标题
RE_H2 = re.compile(r"^##(?!#)\s*(.+)$", re.M)


def extract_h2_titles(text):
    """提取 H2 标题文本列表"""
    return [m.group(1).strip() for m in RE_H2.finditer(text)]

# ==========================================================
# 主函数
# ==========================================================
def main():
    p1 = Path(INPUT_PATH_1)
    p2 = Path(INPUT_PATH_2)
    if not p1.exists() or not p2.exists():
        print("[错误] 请确认输入路径存在。")
        return

    text1 = p1.read_text(encoding="utf-8")
    text2 = p2.read_text(encoding="utf-8")

    h2_1 = extract_h2_titles(text1)
    h2_2 = extract_h2_titles(text2)

    print(f"📘 文件1 H2 标题共 {len(h2_1)} 个")
    print("-" * 60)
    for t in h2_1:
        print("  -", t)
    print("=" * 60)

    print(f"📗 文件2 H2 标题共 {len(h2_2)} 个")
    print("-" * 60)
    for t in h2_2:
        print("  -", t)
    print("=" * 60)

    # 如果需要，简单汇总差异
    diff_add = set(h2_2) - set(h2_1)
    diff_del = set(h2_1) - set(h2_2)
    if diff_add or diff_del:
        print("⚠️ 检测到 H2 差异：")
        if diff_add:
            print(f"🆕 文件2新增 {len(diff_add)} 项：")
            for t in diff_add:
                print("  +", t)
        if diff_del:
            print(f"❌ 文件2缺失 {len(diff_del)} 项：")
            for t in diff_del:
                print("  -", t)
    else:
        print("✅ 两份文件的 H2 标题完全一致。")

if __name__ == "__main__":
    main()
# 创建时间: 2025/10/30 11:20
