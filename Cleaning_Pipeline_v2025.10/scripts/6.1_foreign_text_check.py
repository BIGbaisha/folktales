# 创建时间: 2025/10/15 14:20
# 版本: v2025.10
# -*- coding: utf-8 -*-
"""
6.1_foreign_text_check.py
----------------------------------------
功能：前置输入质量检测：多类异常检测（外文/特殊符号/零宽空间/括号不匹配等）
输入输出路径硬编码为：
I:\中国民间传统故事\老黑解析版本\正式测试\\
"""

\
import re, csv
from pathlib import Path

# Config - change if needed
INPUT_PATH = r"I:\中国民间传统故事\老黑解析版本\正式测试\2.1_raw_sichuan.md"
OUTPUT_CSV = r"I:\中国民间传统故事\老黑解析版本\正式测试\6.1_text_anomaly_report.csv"
ENC = "utf-8"

# Patterns for anomaly detection
PATTERNS = {
    "long_spaces": re.compile(r" {3,}"),
    "isolated_empty_line": re.compile(r"^\s*$"),
    "foreign_char": re.compile(r"[A-Za-z№§]"),
    "special_symbol": re.compile(r"[★◎※→×✦✧•○●◆◇■□▽△✪✦]"),
    "zero_width": re.compile(r"[\u200B-\u200F\uFEFF\u2060]"),
    "fullwidth_space": re.compile(r"\u3000"),
    "number_mixed": re.compile(r"(?<!第)[0-9０-９一二三四五六七八九〇]+"),
    "mismatch_bracket": re.compile(r"（[^）]*$|^[^（]*）|\[\s*\]|\(\s*\)"),
    "non_chinese_scripts": re.compile(r"[ぁ-んァ-ンㄱ-ㅎㅏ-ㅣА-Яа-яЁё]"),
    "markdown_anomaly": re.compile(r"#{4,}|`{3,}|\*{3,}|_{3,}"),
}

CONTEXT_WIDTH = 30

def unicode_repr(s: str) -> str:
    return " ".join(f"U+{ord(ch):04X}" for ch in s)

def analyze_file(input_path):
    p = Path(input_path)
    if not p.exists():
        print(f"[ERROR] 输入文件不存在: {p}")
        return []
    lines = p.read_text(encoding=ENC, errors="ignore").splitlines()
    results = []
    for lineno, line in enumerate(lines, start=1):
        for name, pattern in PATTERNS.items():
            for m in pattern.finditer(line):
                start = max(0, m.start()-CONTEXT_WIDTH)
                end = min(len(line), m.end()+CONTEXT_WIDTH)
                snippet = line[start:end].replace("\n"," ")
                results.append({
                    "line": lineno,
                    "type": name,
                    "snippet": snippet,
                    "char": m.group(0),
                    "unicode": unicode_repr(m.group(0))
                })
    return results

def export_csv(results, out_csv):
    path = Path(out_csv)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["line_no","anomaly_type","text_snippet","matched_text","unicode_repr"])
        for r in results:
            w.writerow([r["line"], r["type"], r["snippet"], r["char"], r["unicode"]])
    print(f"[DONE] 导出检测结果: {path} ({len(results)} items)")

def summary_print(results):
    from collections import Counter
    cnt = Counter(r["type"] for r in results)
    print("[SUMMARY] Detected anomalies by type:")
    for k, v in cnt.most_common():
        print(f"  {k}: {v}")

def main():
    print("[INFO] Running 6.1_foreign_text_check (enhanced)")
    results = analyze_file(INPUT_PATH)
    if not results:
        print("[INFO] 未检测到异常项或文件不存在。")
    else:
        summary_print(results)
        export_csv(results, OUTPUT_CSV)
    print("[DONE] 6.1 finished.")

if __name__ == "__main__":
    main()
