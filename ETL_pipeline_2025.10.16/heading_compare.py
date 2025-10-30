# -*- coding: utf-8 -*-
# 创建时间: 2025/10/30
# 版本: v2025.10-debug
"""
headings_compare_debug.py
----------------------------------------
功能：
- 对比两个 Markdown 文件的各级标题数量分布；
- 发生路径错误时自动输出详细诊断信息；
- 支持快速确认实际执行脚本路径、当前工作目录、文件可访问性。
"""

import re
import os
from pathlib import Path

# ==========================================================
# 文件路径配置（请根据需要修改）
# ==========================================================
INPUT_PATH_1 = r"I:\中国民间传统故事\分卷清洗\guizhou\5.3_Chinese Folk Tales_guizhou.md"
INPUT_PATH_2 = r"I:\中国民间传统故事\分卷清洗\guizhou\6.5_Chinese Folk Tales_guizhou.md"

# ==========================================================
# 正则：提取标题等级
# ==========================================================
RE_HEADING = re.compile(r"^(#{1,6})\s+.*$", re.M)

def count_heading_levels(text):
    """返回 {level: count} 的字典"""
    counts = {i: 0 for i in range(1, 7)}
    for m in RE_HEADING.finditer(text):
        level = len(m.group(1))
        counts[level] += 1
    return counts


def print_comparison_table(c1, c2):
    """格式化输出对比表"""
    print("📊 各级标题数量对比（单位：个）")
    print("-" * 50)
    print(f"{'级别':<8}{'文件1':>8}{'文件2':>10}{'差异':>10}")
    print("-" * 50)
    for i in range(1, 7):
        diff = c2[i] - c1[i]
        diff_str = f"{diff:+}" if diff != 0 else "0"
        print(f"H{i:<6}{c1[i]:>8}{c2[i]:>10}{diff_str:>10}")
    print("-" * 50)


def diagnostic_path_report():
    """打印路径诊断信息"""
    print("\n🩺 [路径诊断报告]")
    print(f"  当前执行脚本文件: {__file__}")
    print(f"  当前工作目录: {os.getcwd()}")
    print("-" * 80)
    for label, p in [("文件1", INPUT_PATH_1), ("文件2", INPUT_PATH_2)]:
        print(f"  {label} 原始字符串: {repr(p)}")
        path_obj = Path(p.strip())
        print(f"  {label} 绝对路径: {path_obj.resolve()}")
        print(f"  {label} 存在? {path_obj.exists()}")
        if not path_obj.exists():
            parent = path_obj.parent
            print(f"  → 上级目录存在? {parent.exists()} | 内容数: {len(list(parent.glob('*')))} 项")
    print("-" * 80)


# ==========================================================
# 主函数
# ==========================================================
def main():
    # 打印诊断信息
    diagnostic_path_report()

    p1 = Path(INPUT_PATH_1.strip())
    p2 = Path(INPUT_PATH_2.strip())

    # 使用 os.path.exists 更宽容
    if not (os.path.exists(p1) and os.path.exists(p2)):
        print("\n[错误] ❌ 无法找到输入文件，请检查上方诊断信息。")
        return

    # 读取文件
    try:
        text1 = Path(p1).read_text(encoding="utf-8")
        text2 = Path(p2).read_text(encoding="utf-8")
    except Exception as e:
        print(f"[错误] 文件读取失败: {e}")
        return

    # 统计标题层级
    c1 = count_heading_levels(text1)
    c2 = count_heading_levels(text2)

    total1 = sum(c1.values())
    total2 = sum(c2.values())

    print(f"\n📘 文件1标题总数：{total1} | 文件2标题总数：{total2}")
    print("=" * 50)
    print_comparison_table(c1, c2)

    if c1 == c2:
        print("✅ 两份文件各级标题数量完全一致，层级结构未改变。")
    else:
        changed = [f"H{i}" for i in range(1,7) if c1[i] != c2[i]]
        print(f"⚠️ 检测到以下标题等级数量发生变化：{', '.join(changed)}")

if __name__ == "__main__":
    main()
