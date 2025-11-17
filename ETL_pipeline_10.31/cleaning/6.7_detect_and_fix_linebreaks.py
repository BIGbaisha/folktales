# -*- coding: utf-8 -*-
# Created: 2025/10/31
# 6.7_detect_and_fix_linebreaks.py
"""
检测 & 修复 “异常断行”（反向规则版 + CSV输出）
-------------------------------------------------
【功能说明】
适用于 Markdown 故事文本中错误换行的检测与修复。

【判定规则】
若出现以下模式：
    当前行末尾为汉字或数字；
    下一行为空行（含零宽符、空格、控制符）；
    再下一行为正文（非标题/代码块/列表等）；
则判定为“异常断行”。
可选择：
- ONLY_DETECT = True  → 仅检测，输出 CSV 报告；
- ONLY_DETECT = False → 自动拼接断行并写出修复文件。

【本脚本融合与规范】
✅ 统一 header 格式；
✅ 调用 load_text / save_text（自动 normalize）；
✅ 分阶段日志输出；
✅ 生成 CSV 报告；
✅ 保留原检测逻辑。
-------------------------------------------------
"""

import re
import csv
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
# ✅ 新增：导入统一环境模块
from utils.template_script_header_manual import (
    load_text, save_text, log_stage, log_summary
)
from utils.text_normalizer import normalize_chinese_text

# ===== 配置 =====
INPUT_PATH  = Path(r"I:\中国民间传统故事\分卷清洗\sichuan\6.7_Chinese Folk Tales_sichuan.md")
OUTPUT_PATH = Path(r"I:\中国民间传统故事\分卷清洗\sichuan\6.7_Chinese Folk Tales_sichuan.md")
CSV_PATH    = Path(r"I:\中国民间传统故事\分卷清洗\sichuan\6.8_detected_linebreaks.csv")
ONLY_DETECT = False   # True=仅检测；False=修复
# =================

# ==========================================================
# Markdown结构识别与检测规则
# ==========================================================
RE_HEADING = re.compile(r"^(#+)\s*(.*)$")
RE_CODE = re.compile(r"^```")
RE_LIST = re.compile(r"^\s*([-*+]|\d{1,3}[.)])\s+")
RE_QUOTE = re.compile(r"^\s*>")
RE_EMPTY = re.compile(r"^[\s\u200b\u200c\u200d\uFEFF\u2028\u2029]*$")
RE_VALID_END = re.compile(r"[\u4e00-\u9fff0-9０-９]$")
RE_VALID_START = re.compile(r"^[\u4e00-\u9fff0-9０-９]")

def is_md_boundary(line: str) -> bool:
    """判断是否为 Markdown 结构边界"""
    return (
        RE_HEADING.match(line)
        or RE_CODE.match(line)
        or RE_LIST.match(line)
        or RE_QUOTE.match(line)
        or RE_EMPTY.match(line)
    )

def normalize_line(line: str) -> str:
    """清理所有隐形字符"""
    return re.sub(r"[\u200b\u200c\u200d\uFEFF]", "", line).rstrip("\r\n\u2028\u2029").strip()

# ==========================================================
# 检测与修复主函数
# ==========================================================
def detect_and_fix(lines):
    fixed = []
    merged_records = []
    merged_count = 0
    current_heading = "（无标题）"
    n = len(lines)
    i = 0

    while i < n:
        line = normalize_line(lines[i])

        # 更新标题
        m = RE_HEADING.match(line)
        if m:
            current_heading = f"{'#'*len(m.group(1))} {m.group(2).strip()}"
            fixed.append(lines[i])
            i += 1
            continue

        # --- 检查反向规则：行尾为汉字/数字 + 下一行空行 + 下下行正文 ---
        if (
            i + 2 < n
            and RE_VALID_END.search(line)
            and RE_EMPTY.match(lines[i + 1])
            and RE_VALID_START.search(normalize_line(lines[i + 2]))
            and not is_md_boundary(line)
            and not is_md_boundary(lines[i + 2])
        ):
            merged_line = line + normalize_line(lines[i + 2])
            marked_before = line + "[ +++++++++++++ ]" + normalize_line(lines[i + 2])

            merged_records.append({
                "heading": current_heading,
                "before": marked_before,
                "after": merged_line,
                "context_before": normalize_line(lines[i-1]) if i > 0 else "",
                "context_after": normalize_line(lines[i+3]) if i + 3 < n else ""
            })
            merged_count += 1

            if ONLY_DETECT:
                fixed.extend([lines[i], lines[i + 1], lines[i + 2]])
            else:
                fixed.append(merged_line + "\n")
            i += 3
            continue

        fixed.append(lines[i])
        i += 1

    return fixed, merged_records, merged_count


def export_csv(records, path: Path):
    """导出检测结果为CSV"""
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["Heading", "Before (原文形态)", "After (拼接后形态)", "ContextBefore", "ContextAfter"])
        for rec in records:
            writer.writerow([
                rec["heading"],
                rec["before"],
                rec["after"],
                rec["context_before"],
                rec["context_after"],
            ])
    print(f"\n🧾 已导出检测结果 CSV：{path}")

# ==========================================================
# 主流程
# ==========================================================
def main():
    log_stage("阶段1：加载与标准化")
    text = load_text(INPUT_PATH)
    lines = text.splitlines(True)

    log_stage("阶段2：检测与修复异常断行")
    fixed_lines, merged_records, merged_count = detect_and_fix(lines)

    print("====== 检测结果 ======")
    print(f"总行数：{len(lines)}")
    print(f"检测到异常断行：{merged_count}")
    print("======================")

    if merged_records:
        for rec in merged_records[:10]:
            print(f"\n{rec['heading']}")
            print(f"  原始：{rec['before']}")
            print(f"  合并：{rec['after']}")
        export_csv(merged_records, CSV_PATH)

    log_stage("阶段3：输出结果")
    if ONLY_DETECT:
        print("\n🔍 当前为检测模式，仅输出CSV，不修改原文件。")
        log_summary("异常断行检测（仅检测模式）", INPUT_PATH, CSV_PATH)
    else:
        save_text(OUTPUT_PATH, "".join(fixed_lines))
        print(f"\n✅ 已写出修复后文件：{OUTPUT_PATH}")
        log_summary("异常断行检测与修复", INPUT_PATH, OUTPUT_PATH)


if __name__ == "__main__":
    main()
