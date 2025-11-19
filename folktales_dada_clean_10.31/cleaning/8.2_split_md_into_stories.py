# -*- coding: utf-8 -*-
# Created: 2025/02/xx
# 8.2_split_md_into_stories.py
"""
大MD → 前言 + 多故事拆分器（支持 REGION + 保留标题原文作为文件名）
-------------------------------------------------
【新增功能】
✔ REGION 配置自动切换输入输出路径
✔ 前言从 # 前言开始 → 下一个 H1 之前
✔ 故事标题识别更稳：匹配 H2/H3/H4 行作为故事
✔ 输出文件名 = “标题原文（去掉###）.md”
✔ 自动清理非法文件名字符
✔ 符合所有 ETL 日志规范（阶段1~7）
-------------------------------------------------
"""

import re
import csv
import sys
from pathlib import Path

# ==== 引入项目统一工具 ====
sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.template_script_header_manual import (
    load_text, save_text, log_stage, log_summary
)
from utils.text_normalizer import normalize_chinese_text

# ==========================================================
# 配置区（你只需改 REGION）
# ==========================================================
REGION = "yuzhongqu"   # ← ★ 改这里即可处理不同卷 ★

# 输入大MD路径模板
INPUT_MD_PATTERN = r"I:\中国民间传统故事\分卷清洗\8.1_yaml\8.1_Chinese Folk Tales_{region}.md"

# 输出根目录模板
OUTPUT_BASE_PATTERN = r"I:\中国民间传统故事\分卷清洗\8.2_story_storage\{region}_split_stories"

# 可疑标题 CSV 输出路径（虽然现在很少需要）
CSV_PATTERN = r"I:\中国民间传统故事\分卷清洗\8.2_story_storage\{region}_split_stories\8.2_suspicious_titles_{region}.csv"

# ---- 按 REGION 自动生成最终路径 ----
INPUT_PATH = Path(INPUT_MD_PATTERN.format(region=REGION))
OUTPUT_DIR = Path(OUTPUT_BASE_PATTERN.format(region=REGION))
CSV_SUSPICIOUS = Path(CSV_PATTERN.format(region=REGION))

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ==========================================================
# 正则规则
# ==========================================================

RE_H1 = re.compile(r"^#\s+(.+)$", re.M)

# 故事标题匹配规则：允许 H2 / H3 / H4
# 示例：
#   ## 001.天和地
#   ### 001．天和地
#   #### 001 天和地
#   ### 天和地
RE_STORY = re.compile(
    r"^\s*#{3}\s+(.+)$",    # 只要 H2/H3/H4 + 任意标题 → 视为故事
    re.UNICODE
)

# 可疑标题（一般不再需要，但保留）
RE_SUSPICIOUS = re.compile(r"^\s*#{2,4}\s*\d{1,4}\s*$")


# ==========================================================
# 阶段2：提取前言 (# 前言 → 下一个 H1)
# ==========================================================
def extract_intro(md_text: str):
    h1_list = list(RE_H1.finditer(md_text))
    if not h1_list:
        return "", md_text

    intro_start = None
    intro_index = None

    for i, m in enumerate(h1_list):
        if m.group(1).strip() == "前言":
            intro_start = m.start()
            intro_index = i
            break

    if intro_start is None:
        return "", md_text

    if intro_index + 1 < len(h1_list):
        intro_end = h1_list[intro_index + 1].start()
    else:
        intro_end = len(md_text)

    intro_text = md_text[intro_start:intro_end].strip()
    remainder = md_text[intro_end:]

    return intro_text, remainder


# ==========================================================
# 阶段3：拆分故事
# ==========================================================
def split_stories(md_text: str):
    lines = [normalize_chinese_text(line) for line in md_text.splitlines()]
    stories = []
    suspicious_records = []
    current_story = None

    for line in lines:

        # 1) 判断是否为故事标题（H2/H3/H4）
        m = RE_STORY.match(line)
        if m:
            raw_title = m.group(1).strip()  # 标题原文（去掉 ###）
            clean_title = safe_filename(raw_title)

            if current_story:
                stories.append(current_story)

            current_story = {
                "raw_title": raw_title,
                "clean_title": clean_title,
                "content": [line]
            }
            continue

        # 2) 可疑标题逻辑（不影响拆分）
        if RE_SUSPICIOUS.match(line):
            suspicious_records.append(line)
            print(f"⚠ WARNING: 可疑标题（可能缺格式）：{line}")

        # 3) 普通正文行
        if current_story:
            current_story["content"].append(line)

    if current_story:
        stories.append(current_story)

    return stories, suspicious_records


# ==========================================================
# 文件名清洗
# ==========================================================
def safe_filename(name: str) -> str:
    """清理 Windows 文件名非法字符"""
    return re.sub(r'[\\/:*?"<>|]', "_", name)


# ==========================================================
# 阶段4~6：输出
# ==========================================================
def write_intro(text: str):
    path = OUTPUT_DIR / "intro.md"
    save_text(path, text)
    print(f"✔ 前言已写出：{path}")

def write_stories(stories):
    for s in stories:
        fname = f"{s['clean_title']}.md"   # ← 标题原文作为文件名
        out_path = OUTPUT_DIR / fname
        save_text(out_path, "\n".join(s["content"]))
        print(f"✔ 写出故事：{out_path}")

def export_suspicious(records):
    if not records:
        print("✔ 无可疑标题")
        return
    with open(CSV_SUSPICIOUS, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["SuspiciousTitle"])
        for r in records:
            w.writerow([r])
    print(f"⚠ 可疑标题已写出：{CSV_SUSPICIOUS}")


# ==========================================================
# 主流程
# ==========================================================
def main():

    log_stage("阶段1：加载大MD文件")
    md_text = load_text(INPUT_PATH)

    log_stage("阶段2：提取前言 (# 前言 → 下一个H1)")
    intro_text, remainder = extract_intro(md_text)

    log_stage("阶段3：拆分故事部分")
    stories, suspicious = split_stories(remainder)
    print(f"✔ 故事总数：{len(stories)}")

    log_stage("阶段4：输出前言")
    write_intro(intro_text)

    log_stage("阶段5：输出单故事文件")
    write_stories(stories)

    log_stage("阶段6：输出可疑标题报告")
    export_suspicious(suspicious)

    log_stage("阶段7：总结")
    log_summary(f"拆分区 {REGION}", INPUT_PATH, OUTPUT_DIR)


if __name__ == "__main__":
    main()

# 创建时间: 2025/11/19
