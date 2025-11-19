# -*- coding: utf-8 -*-
# Updated: 2025/11/05
# 文件名称: count_headings_compare.py
# 版本说明: unified_header_v13（标准路径+统一日志风格）
# ------------------------------------------------------------
# 功能简介:
#   统计 Markdown 文件或目录中各级标题（H1~H6）数量；
#   可选输入第二个路径进行差值对比；
#   支持输出 CSV。
# ------------------------------------------------------------

import os
import re
import csv
from pathlib import Path

# ==========================================================
# 路径配置（可直接改为需要统计的两个路径）
# ==========================================================
# ✅ 单路径统计：
PATH_A = Path(r"I:\中国民间传统故事\分卷清洗\sichuan\5_Chinese Folk Tales_sichuan.md")
PATH_B = None

# ✅ 双路径对比统计：
# PATH_A = Path(r"I:\中国民间传统故事\分卷清洗\sichuan\5.1_Chinese Folk Tales_sichuan.md")
# PATH_B = Path(r"I:\中国民间传统故事\分卷清洗\yuzhongqu\5.1_Chinese Folk Tales_yuzhongqu.md")

# ✅ 输出 CSV（可为空）
CSV_PATH = Path(r"I:\中国民间传统故事\分卷清洗\heading_compare_stats.csv")

# ✅ 最大统计层级（1~6）
MAX_LEVEL = 5

# ✅ 是否打印每个文件详细信息
SHOW_PER_FILE = False

# ==========================================================
# 标题检测规则
# ==========================================================
RE_HASH = re.compile(r"^\s{0,3}(#{1,6})\s+\S")

def count_headings_in_text(text: str, max_level: int = 5):
    """统计单个 Markdown 文本中的标题数量"""
    counts = {lvl: 0 for lvl in range(1, max_level + 1)}
    for line in text.splitlines():
        m = RE_HASH.match(line)
        if not m:
            continue
        lvl = len(m.group(1))
        if 1 <= lvl <= max_level:
            counts[lvl] += 1
    return counts

# ==========================================================
# 文件遍历与统计
# ==========================================================
def iter_markdown_files(path: Path):
    """返回路径下所有 .md 文件"""
    if path.is_file() and path.suffix.lower() == ".md":
        return [path]
    return list(path.rglob("*.md"))

def count_path(path: Path, max_level: int = 5, per_file: bool = False):
    """统计路径内所有 Markdown 文件的标题"""
    totals = {lvl: 0 for lvl in range(1, max_level + 1)}
    details = []
    for md in iter_markdown_files(path):
        try:
            text = md.read_text(encoding="utf-8")
        except Exception:
            text = md.read_text(encoding="utf-8", errors="ignore")
        cnt = count_headings_in_text(text, max_level=max_level)
        if per_file:
            details.append((md, cnt))
        for lvl, n in cnt.items():
            totals[lvl] += n
    return totals, details

# ==========================================================
# 输出与比较
# ==========================================================
def print_counts(title: str, counts):
    total = sum(counts.values())
    parts = [f"H{lvl}={counts[lvl]}" for lvl in sorted(counts)]
    print(f"📊 {title}: " + "，".join(parts) + f" | TOTAL={total}")

def print_diff(a_name: str, a, b_name: str, b):
    levels = sorted(set(a.keys()) | set(b.keys()))
    print("\n🔁 对比结果（A - B 的差值 Δ）：")
    print(f"{'Level':<8}{a_name:^12}{b_name:^12}{'Δ(A-B)':^10}")
    print("-"*44)
    for lvl in levels:
        va, vb = a.get(lvl, 0), b.get(lvl, 0)
        print(f"H{lvl:<7}{va:^12}{vb:^12}{(va-vb):^10}")
    ta, tb = sum(a.values()), sum(b.values())
    print("-"*44)
    print(f"{'TOTAL':<8}{ta:^12}{tb:^12}{(ta-tb):^10}")

def write_csv(csv_path: Path, rows, max_level: int):
    """输出 CSV 汇总"""
    fieldnames = ["path"] + [f"H{lvl}" for lvl in range(1, max_level + 1)] + ["TOTAL"]
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"💾 已写入 CSV：{csv_path}")

# ==========================================================
# 主流程
# ==========================================================
def main():
    if not PATH_A.exists():
        print(f"❌ 路径不存在：{PATH_A}")
        return

    print("阶段1：统计路径 A")
    a_totals, a_details = count_path(PATH_A, max_level=MAX_LEVEL, per_file=SHOW_PER_FILE)
    print_counts("A 汇总", a_totals)
    if SHOW_PER_FILE:
        for md, cnt in a_details:
            print_counts(f"A 明细 | {md.name}", cnt)

    summary_rows = [{
        "path": str(PATH_A),
        **{f"H{lvl}": a_totals.get(lvl, 0) for lvl in range(1, MAX_LEVEL + 1)},
        "TOTAL": sum(a_totals.values())
    }]

    if PATH_B:
        if not PATH_B.exists():
            print(f"❌ 路径不存在：{PATH_B}")
            return
        print("\n阶段2：统计路径 B")
        b_totals, b_details = count_path(PATH_B, max_level=MAX_LEVEL, per_file=SHOW_PER_FILE)
        print_counts("B 汇总", b_totals)
        if SHOW_PER_FILE:
            for md, cnt in b_details:
                print_counts(f"B 明细 | {md.name}", cnt)
        print_diff("A", a_totals, "B", b_totals)
        summary_rows.append({
            "path": str(PATH_B),
            **{f"H{lvl}": b_totals.get(lvl, 0) for lvl in range(1, MAX_LEVEL + 1)},
            "TOTAL": sum(b_totals.values())
        })

    if CSV_PATH:
        write_csv(CSV_PATH, summary_rows, MAX_LEVEL)

    print("\n✅ 统计完成！")

# ==========================================================
# 程序入口
# ==========================================================
if __name__ == "__main__":
    main()
