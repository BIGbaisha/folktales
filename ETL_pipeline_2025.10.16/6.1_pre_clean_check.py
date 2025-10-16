# 创建时间: 2025/10/16 10:20
# 版本: v2025.10.1
# -*- coding: utf-8 -*-
"""
6.1_foreign_text_check_fullwidth.py
----------------------------------------
功能：前置输入质量检测（适配关系库与向量库构建）
重点：检测文本中存在的全角形态（符号、字母、数字等）
说明：为后续统一半角化提供依据，无出版排版需求。
"""

import re, csv
from pathlib import Path
from collections import Counter

# === Config ===
INPUT_PATH = r"I:\中国民间传统故事\老黑解析版本\正式测试\2.1_raw_sichuan.md"
OUTPUT_CSV = r"I:\中国民间传统故事\老黑解析版本\正式测试\6.1_text_anomaly_report.csv"
ENC = "utf-8"

# === 检测模式 ===
PATTERNS = {
    "long_spaces": re.compile(r" {3,}"),
    "isolated_empty_line": re.compile(r"^\s*$"),
    "foreign_char": re.compile(r"[A-Za-z№§]"),
    "special_symbol": re.compile(r"[★◎※→×✦✧•○●◆◇■□▽△✪✦]"),
    "zero_width": re.compile(r"[\u200B-\u200F\uFEFF\u2060]"),
    "fullwidth_space": re.compile(r"\u3000"),  # 全角空格
    "fullwidth_symbol": re.compile(r"[\uff01-\uff5e]"),  # ✅ 全角符号检测
    "number_mixed": re.compile(r"(?<!第)[0-9０-９一二三四五六七八九〇]+"),
    "mismatch_bracket": re.compile(r"（[^）]*$|^[^（]*）|\[\s*\]|\(\s*\)"),
    "non_chinese_scripts": re.compile(r"[ぁ-んァ-ンㄱ-ㅎㅏ-ㅣА-Яа-яЁё]"),
    "markdown_anomaly": re.compile(r"#{4,}|`{3,}|\*{3,}|_{3,}"),
}

CONTEXT_WIDTH = 30


def unicode_repr(s: str) -> str:
    """将字符转为 Unicode 码位可读形式"""
    return " ".join(f"U+{ord(ch):04X}" for ch in s)


def analyze_file(input_path):
    """分析文件行内容并捕捉异常"""
    p = Path(input_path)
    if not p.exists():
        print(f"[ERROR] 输入文件不存在: {p}")
        return []

    lines = p.read_text(encoding=ENC, errors="ignore").splitlines()
    results = []
    for lineno, line in enumerate(lines, start=1):
        for name, pattern in PATTERNS.items():
            for m in pattern.finditer(line):
                start = max(0, m.start() - CONTEXT_WIDTH)
                end = min(len(line), m.end() + CONTEXT_WIDTH)
                snippet = line[start:end].replace("\n", " ")
                results.append({
                    "line": lineno,
                    "type": name,
                    "snippet": snippet,
                    "char": m.group(0),
                    "unicode": unicode_repr(m.group(0))
                })
    return results


def export_csv(results, out_csv):
    """导出检测结果 CSV"""
    path = Path(out_csv)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["line_no", "anomaly_type", "text_snippet", "matched_text", "unicode_repr"])
        for r in results:
            w.writerow([r["line"], r["type"], r["snippet"], r["char"], r["unicode"]])

    print(f"[DONE] 导出检测结果: {path} ({len(results)} items)")


def summary_print(results):
    """打印汇总统计"""
    cnt = Counter(r["type"] for r in results)
    print("\n[SUMMARY] 异常类型统计：")
    for k, v in cnt.most_common():
        print(f"  {k}: {v}")

    # 特别统计：全角符号频率
    fullwidth_chars = [r["char"] for r in results if r["type"] == "fullwidth_symbol"]
    if fullwidth_chars:
        freq = Counter(fullwidth_chars)
        print("\n[DETAIL] 全角符号出现频率：")
        for ch, n in freq.most_common():
            print(f"  {ch} ({unicode_repr(ch)}): {n} 次")


def main():
    print("=== Running 6.1_foreign_text_check_fullwidth ===")
    results = analyze_file(INPUT_PATH)
    if not results:
        print("[INFO] 未检测到异常项或文件不存在。")
    else:
        summary_print(results)
        export_csv(results, OUTPUT_CSV)
    print("=== 检测完成 ===")


if __name__ == "__main__":
    main()
