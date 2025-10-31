# -*- coding: utf-8 -*-
# Created: 2025/10/31
# ETL_pipeline_2025.10.31\6.6_add_meta_quote.py
"""
==============================================================
民族 / 地点 信息提取统一版（融合脚本）
--------------------------------------------------------------
【脚本来源】
融合自：
- 6.6.1_add_location_quote.py     → 仅识别地点（如 "(岑巩县)"）
- 6.6.2_add_ethnic_quote.py       → 仅识别民族（如 "(侗族)"）
- 6.6.3_add_ethnicity_location_quote.py → 同时识别民族+地点（如 "(侗族岑巩县)"）

【核心功能】
本脚本用于在故事标题下方自动补全：
> 民族：xxx
> 地点：yyy

支持以下模式切换：
- MODE = "location" : 仅输出地点信息；
- MODE = "ethnic"   : 仅输出民族信息；
- MODE = "both"     : 同时输出民族 + 地点。

【逻辑说明】
1️⃣ 识别形如 “### 321. 三天皇客当知府” 的标题；
2️⃣ 检查下方若存在括号行（可能为 “(侗族岑巩县)” / “(侗族)” / “(岑巩县)”）；
3️⃣ 自动拆分括号内内容：
   - 若含“族” → “族”前为民族，“族”后为地点；
   - 若无“族” → 全部视为地点；
4️⃣ 输出 Markdown 引用格式：
   > 民族：侗族
   > 地点：岑巩县
5️⃣ 若检测不到括号行，则输出占位符 “——”。

【兼容性】
✅ 适用于贵州、云南、四川等不同卷排版；
✅ 自动跳过空行、支持 H3~H6 各级标题；
✅ CSV 汇总民族与地点对应结果。
==============================================================
"""

import re
import csv
from pathlib import Path
# ✅ 新增：统一导入日志与I/O模块
from utils.template_script_header_manual import (
    load_text, save_text, log_stage, log_summary
)
# ✅ 新增：正则标准化模块
from utils.text_normalizer import normalize_chinese_text

# ==========================================================
# 参数配置
# ==========================================================
MODE = "both"        # 可选: "location" / "ethnic" / "both"
TARGET_LEVEL = 3     # 识别标题等级，如 ### 为3、#### 为4
PLACEHOLDER = "——"   # 无信息时的占位符

INPUT_PATH  = Path(r"I:\中国民间传统故事\分卷清洗\guizhou\6.5_Chinese Folk Tales_guizhou.md")
OUTPUT_PATH = Path(r"I:\中国民间传统故事\分卷清洗\guizhou\6.6_Chinese Folk Tales_guizhou.md")
CSV_PATH    = Path(r"I:\中国民间传统故事\分卷清洗\guizhou\6.6_meta_extraction_summary.csv")

# ==========================================================
# 正则定义
# ==========================================================
# 标题检测：### 321. 三天皇客当知府
RE_HEADING = re.compile(rf"^(#{{{TARGET_LEVEL}}})(?!#)\s*(\d+[\.\．]?)?\s*(.+?)\s*$")
# 括号行检测：（侗族岑巩县）
RE_PAREN   = re.compile(r"^[\*\_—\-~>《“”\"\']*\s*[（(]\s*([\u4e00-\u9fa5\s·,，。；;:：、\-——～~]*)\s*[)）]\s*[\*\_—\-~<》“”\"\']*\s*$")
RE_EMPTY   = re.compile(r"^[\s\u200b\u200c\u200d\uFEFF]*$")

# ==========================================================
# 工具函数
# ==========================================================
def split_ethnicity_location(raw: str):
    """
    根据 '族' 拆分民族与地点。
    例如：
      "侗族岑巩县" → ("侗族", "岑巩县")
      "侗族" → ("侗族", "——")
      "岑巩县" → ("——", "岑巩县")
    """
    raw = re.sub(r"[　\s·,，。；;:：、\-——~～]", "", raw)
    raw = re.sub(r"[^\u4e00-\u9fa5族]", "", raw)
    if not raw:
        return PLACEHOLDER, PLACEHOLDER
    if "族" in raw:
        idx = raw.rfind("族") + 1
        eth = raw[:idx]
        loc = raw[idx:] or PLACEHOLDER
        return eth, loc
    else:
        return PLACEHOLDER, raw


def parse_meta(raw: str, mode: str):
    """根据模式返回民族/地点"""
    eth, loc = split_ethnicity_location(raw)
    if mode == "ethnic":   return eth, PLACEHOLDER
    if mode == "location": return PLACEHOLDER, loc
    return eth, loc


def transform(lines):
    """
    主处理函数：
    - 检测标题；
    - 检查下一行括号；
    - 自动插入民族 / 地点 引用；
    - 输出CSV统计信息。
    """
    out, results, i, n = [], [], 0, len(lines)

    while i < n:
        line = lines[i]
        m = RE_HEADING.match(line)
        if not m:
            out.append(line)
            i += 1
            continue

        # ---- 标题匹配 ----
        heading_text = (m.group(2) or "") + (m.group(3) or "").strip()
        out.append(line)
        j = i + 1
        while j < n and RE_EMPTY.match(lines[j]):
            out.append(lines[j])
            j += 1

        # ---- 检查括号行 ----
        eth, loc, raw = PLACEHOLDER, PLACEHOLDER, ""
        if j < n and (pm := RE_PAREN.match(lines[j].strip())):
            raw = pm.group(1)
            e, l = parse_meta(raw, MODE)
            eth, loc = e or PLACEHOLDER, l or PLACEHOLDER
            j += 1

        # ---- 输出结果 ----
        if MODE in ("ethnic", "both"):
            out.append(f"> 民族：{eth}")
        if MODE in ("location", "both"):
            out.append(f"> 地点：{loc}")
        out.append("")

        results.append((heading_text, eth, loc, raw))
        i = j

    return out, results


def export_csv(results, csv_path: Path):
    """导出民族/地点对应表"""
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["标题", "民族", "地点", "原括号文本"])
        writer.writerows(results)
    print(f"\n🧾 已导出 CSV：{csv_path}（共 {len(results)} 条）")

# ==========================================================
# 主流程
# ==========================================================
def main():
    log_stage("阶段1：加载文件与标准化")
    text = load_text(INPUT_PATH)
    lines = text.splitlines()

    log_stage("阶段2：执行民族/地点识别与补全")
    transformed, results = transform(lines)

    log_stage("阶段3：写出文件与汇总表")
    save_text(OUTPUT_PATH, "\n".join(transformed))
    export_csv(results, CSV_PATH)

    log_summary(f"民族/地点信息提取 ({MODE})", INPUT_PATH, OUTPUT_PATH)


if __name__ == "__main__":
    main()
