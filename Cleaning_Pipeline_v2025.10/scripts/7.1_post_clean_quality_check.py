# 创建时间: 2025/10/15 14:20
# 版本: v2025.10
# -*- coding: utf-8 -*-
"""
7.4_post_clean_quality_check_enhanced.py
--------------------------------------------------
功能：
对清洗完成的民间故事文本进行终末质量检测。
包括空格、外文、特殊符号、异常数字、括号匹配、
多语混排、Markdown错位、不常见字符，
以及【新增】半角符号检测。

输入输出路径（已硬编码）：
INPUT_PATH  = I:\中国民间传统故事\老黑解析版本\正式测试\6.8_Chinese Folk Tales_sichuan_cleaned.md
OUTPUT_CSV  = I:\中国民间传统故事\老黑解析版本\正式测试\7.4_final_clean_report.csv
"""

import re
import csv
from collections import Counter

# 硬编码路径
INPUT_PATH  = r"I:\中国民间传统故事\老黑解析版本\正式测试\6.8_Chinese Folk Tales_sichuan_cleaned.md"
OUTPUT_CSV  = r"I:\中国民间传统故事\老黑解析版本\正式测试\7.1_final_clean_report.csv"

def detect_anomalies(text_lines):
    anomalies = []

    # 正则模式定义
    patterns = {
        "long_spaces": r"[ ]{3,}",  # 连续3个以上空格
        "foreign_text": r"[A-Za-z§№]",  # 英文及特殊编号
        "abnormal_symbol": r"[★◎※→×§¤♣♦♠♥◇◆○●■□◎◎※→←↑↓]",  # 特殊符号
        "rare_chars": r"[\u200b\u3000\ufeff]",  # 零宽、全角空格、BOM
        "isolated_digit": r"(?<!\d)\d{1,2}(?!\d)",  # 孤立数字
        "unmatched_brackets": r"[\(（][^\)）]*$|^[^\(（]*[\)）]",  # 括号未匹配
        "multilingual": r"[\u3040-\u30ff\u1100-\u11ff\u3130-\u318f\uac00-\ud7af\u0400-\u04ff]",  # 日文韩文俄文
        "markdown_error": r"#{4,}|[*_]{3,}|`{3,}",  # Markdown格式异常
        # 新增：半角符号检测
        "halfwidth_symbol": r"[(){}\[\]\"',.;:!?@#$%^&*_+=<>\\/`~]"
    }

    for i, line in enumerate(text_lines):
        for key, pattern in patterns.items():
            if re.search(pattern, line):
                matches = re.findall(pattern, line)
                anomalies.append({
                    "line_no": i + 1,
                    "anomaly_type": key,
                    "text_snippet": line.strip()[:60],
                    "matched_text": ", ".join(set(matches))
                })
    return anomalies


def export_report(anomalies):
    if not anomalies:
        print("[INFO] 未检测到异常，文本质量良好。")
        return

    # 写入CSV
    with open(OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["line_no", "anomaly_type", "text_snippet", "matched_text"])
        writer.writeheader()
        writer.writerows(anomalies)

    # 汇总统计
    summary = Counter([a["anomaly_type"] for a in anomalies])
    print("\n[SUMMARY] 异常检测结果：")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    print(f"[DONE] 导出报告: {OUTPUT_CSV} (共 {len(anomalies)} 项)\n")


def main():
    print("=== 7.4 Post-Clean Quality Check (Enhanced) ===")
    try:
        with open(INPUT_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"[ERROR] 未找到输入文件：{INPUT_PATH}")
        return

    anomalies = detect_anomalies(lines)
    export_report(anomalies)
    print("=== 检测完成 ===")


if __name__ == "__main__":
    main()
