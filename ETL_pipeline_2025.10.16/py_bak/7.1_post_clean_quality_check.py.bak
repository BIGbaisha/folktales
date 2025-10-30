# 创建时间: 2025/10/16 10:00
# 版本: v2025.10.28.heading
# -*- coding: utf-8 -*-
"""
7.1_post_clean_quality_check_enhanced.py
--------------------------------------------------
功能：
对清洗完成的民间故事文本进行终末质量检测（适用于关系库/向量库使用）。
重点检测：全角符号存在、异常字符、括号不匹配、空格异常等。

更新：
✅ isolated_digit 仅检测独立一位数字，排除年月日岁种
✅ markdown_error 排除合法 H1–H5
✅ CSV 增加“最近标题 heading”列
"""

import re
import csv
from collections import Counter
from pathlib import Path

# === 硬编码路径（可修改） ===
INPUT_PATH  = r"I:\中国民间传统故事\分卷清洗\yunnan\6.8_Chinese Folk Tales_yunnan.md"
OUTPUT_CSV  = r"I:\中国民间传统故事\分卷清洗\yunnan\7.1_final_clean_report.csv"
ENC = "utf-8"


# === 检测规则定义 ===
PATTERNS = {
    "long_spaces": re.compile(r"[ ]{3,}"),                # 连续3个以上空格
    "foreign_text": re.compile(r"[A-Za-z§№]"),            # 外文字母及编号符号
    "abnormal_symbol": re.compile(r"[★◎※→×§¤♣♦♠♥◇◆○●■□◎◎※→←↑↓]"),  # 特殊符号
    "rare_chars": re.compile(r"[\u200b\u3000\ufeff]"),    # 零宽、全角空格、BOM
    "isolated_digit": re.compile(r"(?<!\d)(\d)(?!\d)(?![年月日岁种])"),  # 独立单个数字，排除年月日岁种
    "unmatched_brackets": re.compile(r"[\(（][^\)）]*$|^[^\(（]*[\)）]"), # 括号未匹配
    "multilingual": re.compile(r"[\u3040-\u30ff\u1100-\u11ff\u3130-\u318f\uac00-\ud7af\u0400-\u04ff]"), # 日韩俄文
    "markdown_error": re.compile(r"(^|[^#])#{6,}|[*_]{4,}|`{3,}"),  # 排除合法H1-H5标题
    "fullwidth_symbol": re.compile(r"[\uff01-\uff5e]"),  # 全角符号检测
}

CONTEXT_WIDTH = 30
RE_HEADING = re.compile(r"^(#{1,6})\s*[\d\u4e00-\u9fa5].*$")  # 标题行识别


def unicode_repr(s: str) -> str:
    """返回字符的Unicode码点表示"""
    return " ".join(f"U+{ord(ch):04X}" for ch in s)


def detect_anomalies(text_lines):
    """检测文本中异常项并记录所在标题"""
    anomalies = []
    current_heading = "（无标题）"

    for i, line in enumerate(text_lines):
        # 检测标题更新
        if RE_HEADING.match(line.strip()):
            current_heading = line.strip()
            continue

        # 检测异常项
        for key, pattern in PATTERNS.items():
            for match in pattern.finditer(line):
                snippet = line[max(0, match.start()-CONTEXT_WIDTH):match.end()+CONTEXT_WIDTH].strip()
                anomalies.append({
                    "line_no": i + 1,
                    "heading": current_heading,
                    "anomaly_type": key,
                    "text_snippet": snippet[:60],
                    "matched_text": match.group(0),
                    "unicode_repr": unicode_repr(match.group(0))
                })
    return anomalies


def export_report(anomalies, output_path):
    """导出检测报告"""
    if not anomalies:
        print("[INFO] 未检测到异常，文本质量良好。")
        return

    path = Path(output_path)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["line_no", "heading", "anomaly_type", "text_snippet", "matched_text", "unicode_repr"])
        writer.writeheader()
        writer.writerows(anomalies)

    # 汇总统计
    summary = Counter([a["anomaly_type"] for a in anomalies])
    print("\n[SUMMARY] 异常检测统计：")
    for k, v in summary.items():
        print(f"  {k}: {v}")

    # 全角符号频率统计
    fw_chars = [a["matched_text"] for a in anomalies if a["anomaly_type"] == "fullwidth_symbol"]
    if fw_chars:
        freq = Counter(fw_chars)
        freq_csv = path.with_name(path.stem + "_fullwidth_freq.csv")
        with freq_csv.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["character", "unicode", "count"])
            for ch, n in freq.most_common():
                w.writerow([ch, unicode_repr(ch), n])
        print(f"\n[DONE] 全角符号频率统计已导出：{freq_csv}")

    print(f"\n[FINISH] 异常报告导出完成：{output_path} (共 {len(anomalies)} 项)\n")


def main():
    print("=== 7.1 Post-Clean Quality Check (Enhanced) ===")
    try:
        with open(INPUT_PATH, "r", encoding=ENC) as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"[ERROR] 未找到输入文件：{INPUT_PATH}")
        return

    anomalies = detect_anomalies(lines)
    export_report(anomalies, OUTPUT_CSV)
    print("=== 检测完成 ===")


if __name__ == "__main__":
    main()
