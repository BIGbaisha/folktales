# -*- coding: utf-8 -*-
# 创建时间: 2025/10/24
# 版本: v2025.10
"""
5.2_check_heading_numbering_v4.py
----------------------------------------
功能：
- 自动识别带数字编号标题的 Markdown 层级（H1~H6）
- 使用宽松匹配：支持 “001.鲁班”、“001、鲁班”、“001：鲁班”等
- 检查编号连续性（缺号 / 跳号）
- 生成详细 CSV 报告（标题、编号、连续状态）
- 兼容不同卷（云南 H3、四川 H4 等）
"""

import re
import csv
from pathlib import Path

# ==========================================================
# 文件路径配置
# ==========================================================
INPUT_PATH = r"I:\中国民间传统故事\分卷清洗\yunnan\5_Chinese Folk Tales_yunnan.md"
CSV_REPORT_PATH = r"I:\中国民间传统故事\分卷清洗\yunnan\5.2_heading_number_check_report.csv"

# ==========================================================
# 宽松匹配带数字编号的标题（允许混合标点、空格）
# ==========================================================
RE_NUM_TITLE = re.compile(
    r"^(#{1,6})\s*\d{1,4}[\.\、,，．：:\s]*[\u4e00-\u9fa5A-Za-z0-9（）()《》〈〉「」『』“”‘’·—\-　\s]*$",
    re.M
)

# ==========================================================
# 查找前 N 个数字标题并统计等级
# ==========================================================
def detect_numbered_heading_levels(text, limit=10):
    results = []
    for m in RE_NUM_TITLE.finditer(text):
        hashes = m.group(1)
        title = m.group(0).strip()
        level = len(hashes)
        results.append((level, title))
        if len(results) >= limit:
            break

    if not results:
        print("⚠️ 未发现数字编号标题（例如 ### 001.鲁班）")
        return None, []

    print("📘 检测结果（前 10 个数字编号标题）")
    print("-" * 60)
    for i, (lvl, title) in enumerate(results, 1):
        print(f"{i:02d}. H{lvl} | {title}")
    print("-" * 60)

    level_counts = {}
    for lvl, _ in results:
        level_counts[lvl] = level_counts.get(lvl, 0) + 1

    main_level = max(level_counts, key=level_counts.get)
    print(f"📊 主要标题等级为：H{main_level}（{level_counts}）")
    return main_level, results

# ==========================================================
# 提取指定等级的所有标题
# ==========================================================
def extract_titles_by_level(text, level):
    pattern = re.compile(rf"^({'#' * level})\s*(.+)$", re.M)
    return [m.group(2).strip() for m in pattern.finditer(text)]

# ==========================================================
# 检测编号连续性
# ==========================================================
def detect_numbering_issues(titles):
    nums = []
    entries = []

    for idx, t in enumerate(titles, 1):
        m = re.match(r"^\D*(\d+)", t)
        num = int(m.group(1)) if m else None
        nums.append(num)
        entries.append({"index": idx, "num": num, "title": t})

    issues = []
    for i in range(1, len(nums)):
        if nums[i] is None or nums[i - 1] is None:
            continue
        if nums[i] != nums[i - 1] + 1:
            issues.append((i, nums[i - 1], nums[i]))

    return issues, nums, entries

# ==========================================================
# 导出 CSV 报告
# ==========================================================
def export_csv_report(entries, issues, csv_path):
    missing_nums = set()
    for i in range(1, len(entries)):
        prev = entries[i - 1]["num"]
        curr = entries[i]["num"]
        if prev is None or curr is None:
            continue
        if curr != prev + 1:
            # 计算缺号区间
            for n in range(prev + 1, curr):
                missing_nums.add(n)

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["序号", "编号", "标题文本", "状态"])
        for e in entries:
            status = ""
            if e["num"] in missing_nums:
                status = "缺号前后"
            elif e["num"] is None:
                status = "无编号"
            else:
                status = "正常"
            writer.writerow([e["index"], e["num"] or "", e["title"], status])

    print(f"💾 已生成 CSV 报告: {csv_path}")

# ==========================================================
# 主函数
# ==========================================================
def main():
    ip = Path(INPUT_PATH)
    if not ip.exists():
        print(f"[错误] 文件不存在: {INPUT_PATH}")
        return

    text = ip.read_text(encoding="utf-8")

    # 1️⃣ 自动识别数字标题等级
    main_level, samples = detect_numbered_heading_levels(text, limit=10)
    if not main_level:
        return

    # 2️⃣ 提取该等级的所有标题
    titles = extract_titles_by_level(text, main_level)
    print(f"共检测到 {len(titles)} 个 H{main_level} 标题。")

    # 3️⃣ 检查编号连续性
    issues, nums, entries = detect_numbering_issues(titles)

    if issues:
        print(f"⚠️ 检测到 {len(issues)} 处编号不连续：")
        for idx, prev, curr in issues:
            print(f"  序号 {idx}: {prev} → {curr}")
    else:
        print("✅ 所有编号连续。")

    if nums:
        valid_nums = [n for n in nums if n is not None]
        if valid_nums:
            print(f"📈 编号范围：{valid_nums[0]} ~ {valid_nums[-1]}")

    # 4️⃣ 导出 CSV 报告
    export_csv_report(entries, issues, CSV_REPORT_PATH)

if __name__ == "__main__":
    main()
