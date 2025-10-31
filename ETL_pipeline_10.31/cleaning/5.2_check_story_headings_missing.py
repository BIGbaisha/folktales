
# -*- coding: utf-8 -*-
# Created: 2025/10/31
# ETL_pipeline_2025.10.31\5.2_check_story_headings_missing.py
"""
----------------------------------------
功能：
- 自动识别带数字编号标题的 Markdown 层级（H1~H6）
- 检查编号连续性（缺号 / 跳号）
- 生成详细 CSV 报告（标题、编号、连续状态）
- 兼容不同卷（云南 H3、四川 H4 等）
- ✅ 自动补齐标题间空行（直接覆盖输入文件）
"""

import re
import csv
from pathlib import Path
# ✅ 新增：统一模块导入
from utils.template_script_header_manual import (
    load_text, save_text, log_stage, log_summary
)
from utils.text_normalizer import normalize_chinese_text

# ==========================================================
# 文件路径配置
# ==========================================================
INPUT_PATH = Path(r"I:\中国民间传统故事\分卷清洗\guizhou\5.1_Chinese Folk Tales_guizhou.md")
CSV_REPORT_PATH = Path(r"I:\中国民间传统故事\分卷清洗\guizhou\5.2_heading_number_check_report.csv")

# ==========================================================
# 正则定义
# ==========================================================
RE_NUM_TITLE = re.compile(
    r"^(#{1,6})\s*\d{1,4}[\.\、,，．：:\s]*[\u4e00-\u9fa5A-Za-z0-9（）()《》〈〉「」『』“”‘’·—\-　\s]*$",
    re.M
)
RE_HEADING = re.compile(r"^(#{1,6})\s+.*$")

# ==========================================================
# 核心函数（原逻辑保持）
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

def extract_titles_by_level(text, level):
    pattern = re.compile(rf"^({'#' * level})(?!#)\s*(.+)$", re.M)
    return [m.group(2).strip() for m in pattern.finditer(text)]

def detect_numbering_issues(titles):
    nums, entries = [], []
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

def export_csv_report(entries, issues, csv_path):
    missing_nums = set()
    for i in range(1, len(entries)):
        prev, curr = entries[i - 1]["num"], entries[i]["num"]
        if prev is None or curr is None:
            continue
        if curr != prev + 1:
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

def ensure_blank_lines_between_headings(text: str) -> str:
    lines = text.splitlines()
    new_lines = []
    for i, line in enumerate(lines):
        new_lines.append(line)
        if RE_HEADING.match(line):
            if i + 1 < len(lines) and RE_HEADING.match(lines[i + 1]):
                new_lines.append("")
    return "\n".join(new_lines) + "\n"

# ==========================================================
# 主函数
# ==========================================================
def main():
    log_stage("阶段1：加载与标准化")  # ✅ 新增统一日志
    ip = Path(INPUT_PATH)
    if not ip.exists():
        print(f"[错误] 文件不存在: {INPUT_PATH}")
        return

    # 🧩 替换原 read_text 为标准化加载
    text = load_text(ip)

    log_stage("阶段2：检测数字标题等级")
    main_level, samples = detect_numbered_heading_levels(text, limit=10)
    if not main_level:
        return

    log_stage("阶段3：提取并检测编号连续性")
    titles = extract_titles_by_level(text, main_level)
    issues, nums, entries = detect_numbering_issues(titles)
    export_csv_report(entries, issues, CSV_REPORT_PATH)

    log_stage("阶段4：补齐标题间空行")
    new_text = ensure_blank_lines_between_headings(text)
    save_text(ip, new_text)  # ✅ 替代 write_text
    print(f"✅ 已补齐标题间空行并覆盖原文件: {INPUT_PATH}")

    log_summary("标题编号检测", INPUT_PATH, CSV_REPORT_PATH)  # ✅ 新增阶段总结

if __name__ == "__main__":
    main()
