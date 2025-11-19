# -*- coding: utf-8 -*-
# Created: 2025/10/31
# 6.3_remove_math_and_symbols.py
"""
脚本功能：
1️⃣ 检查所有数学插入符（$...$、$$...$$、\(...\)、\[...\]）
2️⃣ 检查并删除圆圈数字（①②③…）
3️⃣ 可切换：仅检测 或 检测+删除
4️⃣ 控制台打印所有被检测到的内容
"""

import re
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1])) # ✅ 父路径从0级开始算
# ✅ 新增：统一环境模块导入
from utils.template_script_header_manual import (
    load_text, save_text, log_stage, log_summary
)
from utils.text_normalizer import normalize_chinese_text

# ====== 硬编码路径（可修改）======
INPUT_PATH  = Path(r"I:\中国民间传统故事\分卷清洗\sichuan\6.2_Chinese Folk Tales_sichuan.md")
OUTPUT_PATH = Path(r"I:\中国民间传统故事\分卷清洗\sichuan\6.3_Chinese Folk Tales_sichuan.md")
# ==================================
ONLY_DETECT = False  # ✅ True = 仅检测; False = 删除并输出

# ---------- 正则：所有数学插入 ----------
RE_MATH_BLOCK_DOLLAR = re.compile(r"\$\$(.+?)\$\$", re.DOTALL)
RE_MATH_BLOCK_BRACK  = re.compile(r"\\\[(.+?)\\\]", re.DOTALL)
RE_MATH_INLINE_DOLLAR = re.compile(r"(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)", re.DOTALL)
RE_MATH_INLINE_PAREN  = re.compile(r"\\\((.+?)\\\)", re.DOTALL)

# ---------- 新增：圆圈数字符号 ----------
RE_CIRCLED_NUM = re.compile(r"[\u2460-\u2473\u3251-\u325F\u32B1-\u32BF]")

def remove_math_and_symbols(text: str) -> str:
    """检测 + 删除 数学表达式和圆圈数字"""
    all_found = []

    # --- 捕获所有数学表达式 ---
    for pattern in [RE_MATH_BLOCK_DOLLAR, RE_MATH_BLOCK_BRACK,
                    RE_MATH_INLINE_DOLLAR, RE_MATH_INLINE_PAREN]:
        for m in pattern.finditer(text):
            expr = m.group(0).strip()
            all_found.append(("math", expr))

    # --- 捕获所有圆圈数字 ---
    for m in RE_CIRCLED_NUM.finditer(text):
        all_found.append(("circled", m.group(0)))

    # --- 打印检测报告 ---
    print("【检测报告】")
    if not all_found:
        print("✅ 未发现任何数学或圆圈符号。")
    else:
        print(f"共发现 {len(all_found)} 处：")
        for i, (typ, expr) in enumerate(all_found, 1):
            tag = "数学" if typ == "math" else "圆圈数字"
            preview = expr.replace("\n", " ")
            print(f"{i:03d}. [{tag}] {preview}")

    if ONLY_DETECT:
        print("\n🔍 当前为检测模式，仅打印报告，不修改文件。")
        return text

    # --- 删除所有数学表达式和圆圈数字 ---
    text = RE_MATH_BLOCK_DOLLAR.sub("", text)
    text = RE_MATH_BLOCK_BRACK.sub("", text)
    text = RE_MATH_INLINE_DOLLAR.sub("", text)
    text = RE_MATH_INLINE_PAREN.sub("", text)
    text = RE_CIRCLED_NUM.sub("", text)

    return text


def main():
    log_stage("阶段1：加载文件与标准化")  # ✅ 新增阶段日志
    ip = Path(INPUT_PATH)
    if not ip.exists():
        raise FileNotFoundError(f"输入文件不存在：{ip}")

    # 🧩 替换 read_text → load_text（含 normalize）
    text = load_text(ip)

    log_stage("阶段2：检测与删除数学符号、圆圈数字")
    cleaned = remove_math_and_symbols(text)

    if ONLY_DETECT:
        log_summary("数学/圆圈符号检测（仅检测模式）", INPUT_PATH, None)  # ✅ 新增总结
        return

    log_stage("阶段3：输出文件")
    save_text(OUTPUT_PATH, cleaned)  # ✅ 统一写出
    print(f"✅ 已删除所有数学插入与圆圈符号。")

    log_summary("数学/圆圈符号清理", INPUT_PATH, OUTPUT_PATH)  # ✅ 新增总结日志


if __name__ == "__main__":
    main()
