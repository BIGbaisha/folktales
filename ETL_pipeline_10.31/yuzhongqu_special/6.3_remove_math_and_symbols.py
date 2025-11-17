# -*- coding: utf-8 -*-
# Created: 2025/10/31
# yuzhongqu_special\6.3_remove_math_and_symbols.py
"""
脚本功能：
1️⃣ 检查/删除数学插入符（$...$、$$...$$、\(...\)、\[...\]）
2️⃣ 检查/删除圆圈数字（①②③…）
3️⃣ 检查/删除“以数字或数学符号开头的整行”
4️⃣ 新增：输出检测报告到 CSV（整行内容）
5️⃣ 可切换：仅检测 或 检测+删除
"""

import re
import sys
import csv
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.template_script_header_manual import load_text, save_text, log_stage, log_summary
from utils.text_normalizer import normalize_chinese_text

# ====== 路径配置 ======
INPUT_PATH  = Path(r"I:\中国民间传统故事\分卷清洗\sichuan\6.3_Chinese Folk Tales_sichuan.md")
OUTPUT_PATH = Path(r"I:\中国民间传统故事\分卷清洗\sichuan\6.3_Chinese Folk Tales_sichuan.md")
CSV_REPORT  = Path(r"I:\中国民间传统故事\分卷清洗\sichuan\6.3_detected_math_symbols.csv")
# ==================================
ONLY_DETECT = True              # ✅ True=仅检测, False=删除
REMOVE_NUMBERED_LINES = True     # ✅ 是否检测并删除“数字或数学符号开头的行”

# ---------- 正则 ----------
RE_MATH_BLOCK_DOLLAR = re.compile(r"\$\$(.+?)\$\$", re.DOTALL)
RE_MATH_BLOCK_BRACK  = re.compile(r"\\\[(.+?)\\\]", re.DOTALL)
RE_MATH_INLINE_DOLLAR = re.compile(r"(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)", re.DOTALL)
RE_MATH_INLINE_PAREN  = re.compile(r"\\\((.+?)\\\)", re.DOTALL)
RE_CIRCLED_NUM = re.compile(r"[\u2460-\u2473\u3251-\u325F\u32B1-\u32BF]")
# ✅ 改进：匹配“整行以数字或数学符号开头”的行
RE_NUMBER_OR_MATH_LINE = re.compile(
    r"^[ \t]*([$①②③④⑤⑥⑦⑧⑨⑩ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫ\d].*)$", re.MULTILINE
)
RE_HEADING = re.compile(r"^(#{1,6})\s*(.+)$", re.M)


def find_current_heading(text: str, pos: int) -> tuple:
    """根据匹配位置查找最近标题"""
    headings = [(m.start(), len(m.group(1)), m.group(2).strip()) for m in RE_HEADING.finditer(text)]
    current = ("", "", "")
    for start, level, title in headings:
        if start <= pos:
            current = (level, "#" * level, title)
        else:
            break
    return current


def remove_math_and_symbols(text: str):
    """检测 + 删除 数学表达式、圆圈数字、以及数字/符号开头行"""
    all_found = []

    # --- 数学表达式 ---
    for pattern in [RE_MATH_BLOCK_DOLLAR, RE_MATH_BLOCK_BRACK,
                    RE_MATH_INLINE_DOLLAR, RE_MATH_INLINE_PAREN]:
        for m in pattern.finditer(text):
            pos = m.start()
            expr = m.group(0).strip()
            level, marks, title = find_current_heading(text, pos)
            all_found.append(("数学符号", marks, title, expr))

    # --- 圆圈数字 ---
    for m in RE_CIRCLED_NUM.finditer(text):
        pos = m.start()
        level, marks, title = find_current_heading(text, pos)
        all_found.append(("圆圈数字", marks, title, m.group(0)))

    # --- 数字或数学符号开头的整行 ---
    if REMOVE_NUMBERED_LINES:
        for m in RE_NUMBER_OR_MATH_LINE.finditer(text):
            pos = m.start()
            full_line = m.group(1).strip()
            level, marks, title = find_current_heading(text, pos)
            all_found.append(("数字或数学符号开头行", marks, title, full_line))

    # --- 打印报告 ---
    print("【检测报告】")
    if not all_found:
        print("✅ 未发现任何数学、圆圈或数字/符号开头行。")
    else:
        print(f"共发现 {len(all_found)} 处：")
        for i, (typ, marks, title, expr) in enumerate(all_found, 1):
            print(f"{i:03d}. [{typ}] ({title}) {expr.replace(chr(10),' ')}")

    # --- 输出到 CSV ---
    if all_found:
        with open(CSV_REPORT, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["序号", "类型", "标题层级", "标题内容", "命中行"])
            for i, (typ, marks, title, expr) in enumerate(all_found, 1):
                writer.writerow([i, typ, marks, title, expr])
        print(f"🧾 已输出检测报告：{CSV_REPORT}")

    if ONLY_DETECT:
        print("🔍 当前为检测模式，仅输出报告，不修改文件。")
        return text

    # --- 删除匹配 ---
    text = RE_MATH_BLOCK_DOLLAR.sub("", text)
    text = RE_MATH_BLOCK_BRACK.sub("", text)
    text = RE_MATH_INLINE_DOLLAR.sub("", text)
    text = RE_MATH_INLINE_PAREN.sub("", text)
    text = RE_CIRCLED_NUM.sub("", text)
    if REMOVE_NUMBERED_LINES:
        text = RE_NUMBER_OR_MATH_LINE.sub("", text)

    return text


def main():
    log_stage("阶段1：加载文件与标准化")
    ip = Path(INPUT_PATH)
    if not ip.exists():
        raise FileNotFoundError(f"输入文件不存在：{ip}")
    text = load_text(ip)

    log_stage("阶段2：检测与清理数学/数字符号")
    cleaned = remove_math_and_symbols(text)

    if ONLY_DETECT:
        log_summary("数学/数字符号检测（仅检测模式）", INPUT_PATH, CSV_REPORT)
        return

    log_stage("阶段3：输出文件")
    save_text(OUTPUT_PATH, cleaned)
    print(f"✅ 已删除所有数学、圆圈符号及数字/符号开头行（开关：{REMOVE_NUMBERED_LINES}）")
    log_summary("数学/数字符号清理", INPUT_PATH, OUTPUT_PATH)


if __name__ == "__main__":
    main()
