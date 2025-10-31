# -*- coding: utf-8 -*-
# Created: 2025/10/31
# ETL_pipeline_2025.10.31\7.1_post_clean_quality_check.py
"""
==============================================================
终末质量检测脚本（Post-Clean Quality Check Enhanced）
--------------------------------------------------------------
【脚本功能】
对清洗完成的民间故事文本进行“最终质量检测”，
主要用于关系库、向量库入库前的质量确认。

【检测维度】
1️⃣ 全角符号；
2️⃣ 零宽字符 / 全角空格；
3️⃣ 外文字母及编号符号；
4️⃣ 特殊符号；
5️⃣ 独立数字（排除年月日岁种）；
6️⃣ 括号不匹配；
7️⃣ Markdown 错误格式；
8️⃣ 多语言字符（日韩俄等）。

【更新记录】
✅ isolated_digit 仅检测独立一位数字，排除年月日岁种；
✅ markdown_error 排除合法 H1–H5；
✅ CSV 增加“最近标题 heading”列；
✅ 统一 pipeline header、日志与文本标准化；
==============================================================
"""

import re
import csv
from collections import Counter
from pathlib import Path
# ✅ 新增：统一导入日志与加载模块
from utils.template_script_header_manual import (
    load_text, log_stage, log_summary
)
from utils.text_normalizer import normalize_chinese_text

# ==========================================================
# 文件路径配置
# ==========================================================
INPUT_PATH  = Path(r"I:\中国民间传统故事\分卷清洗\guizhou\6.8_Chinese Folk Tales_guizhou.md")
OUTPUT_CSV  = Path(r"I:\中国民间传统故事\分卷清洗\guizhou\7.1_final_clean_report.csv")

# ==========================================================
# 检测规则定义
# ==========================================================
PATTERNS = {
    "long_spaces": re.compile(r"[ ]{3,}"),                     # 连续3个以上空格
    "foreign_text": re.compile(r"[A-Za-z§№]"),                 # 外文字母及编号符号
    "abnormal_symbol": re.compile(r"[★◎※→×§¤♣♦♠♥◇◆○●■□◎◎※→←↑↓]"),  # 特殊符号
    "rare_chars": re.compile(r"[\u200b\u3000\ufeff]"),         # 零宽、全角空格、BOM
    "isolated_digit": re.compile(r"(?<!\d)(\d)(?!\d)(?![年月日岁种])"),  # 独立单个数字
    "unmatched_brackets": re.compile(r"[\(（][^\)）]*$|^[^\(（]*[\)）]"), # 括号未匹配
    "multilingual": re.compile(r"[\u3040-\u30ff\u1100-\u11ff\u3130-\u318f\uac00-\ud7af\u0400-\u04ff]"), # 日韩俄文
    "markdown_error": re.compile(r"(^|[^#])#{6,}|[*_]{4,}|`{3,}"), # 排除合法H1-H5标题
    "fullwidth_symbol": re.compile(r"[\uff01-\uff5e]"),        # 全角符号检测
}

CONTEXT_WIDTH = 30
RE_HEADING = re.compile(r"^(#{1,6})\s*[\d\u4e00-\u9fa5].*$")  # 标题行识别

# ==========================================================
# 核心检测函数
# ==========================================================
def unicode_repr(s: str) -> str:
    """返回字符的Unicode码点表示"""
    return " ".join(f"U+{ord(ch):04X}" for ch in s)


def detect_anomalies(text_lines):
    """检测文本中异常项并记录所在标题"""
    anomalies = []
    current_heading = "（无标题）"

    for i, line in enumerate(text_lines):
        if RE_HEADING.match(line.strip()):
            current_heading = line.strip()
            continue

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


def export_report(anomalies, output_path: Path):
    """导出检测报告"""
    if not anomalies:
        print("[INFO] 未检测到异常，文本质量良好。")
        return

    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
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
        freq_csv = output_path.with_name(output_path.stem + "_fullwidth_freq.csv")
        with freq_csv.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["character", "unicode", "count"])
            for ch, n in freq.most_common():
                w.writerow([ch, unicode_repr(ch), n])
        print(f"\n[DONE] 全角符号频率统计已导出：{freq_csv}")

    print(f"\n[FINISH] 异常报告导出完成：{output_path} (共 {len(anomalies)} 项)\n")

# ==========================================================
# 主函数
# ==========================================================
def main():
    log_stage("阶段1：加载与标准化")
    text = load_text(INPUT_PATH)
    lines = text.splitlines()

    log_stage("阶段2：执行终末质量检测")
    anomalies = detect_anomalies(lines)

    log_stage("阶段3：导出报告")
    export_report(anomalies, OUTPUT_CSV)

    log_summary("终末质量检测报告", INPUT_PATH, OUTPUT_CSV)


if __name__ == "__main__":
    main()
