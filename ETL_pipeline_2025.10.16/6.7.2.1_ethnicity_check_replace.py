# -*- coding: utf-8 -*-
# Created on: 2025-10-27
# Version: v2025.04
"""
民族名称批量处理工具（验证 / 替换 一体化）
-------------------------------------------------
✅ VALIDATION_MODE = True  → 检查民族名称合法性，仅输出CSV报告
✅ VALIDATION_MODE = False → 执行批量替换，覆盖原文件并打印替换统计
"""

import re
import csv
from pathlib import Path

# ===== Configuration =====
INPUT_PATH  = r"I:\中国民间传统故事\分卷清洗\yunnan\6.7.2_Chinese Folk Tales_yunnan.md"
OUTPUT_CSV  = r"I:\中国民间传统故事\分卷清洗\yunnan\6.7.2.1_invalid_ethnicity_report.csv"

# 控制模式：True=验证合法性；False=替换修正
VALIDATION_MODE = True
# ==========================

# ===== 民族合法性字典 =====
VALID_ETHNICITIES = {
    "汉族","壮族","回族","满族","维吾尔族","苗族","彝族","土家族","藏族","蒙古族",
    "布依族","侗族","瑶族","朝鲜族","白族","哈尼族","哈萨克族","黎族","傣族","畲族",
    "傈僳族","仡佬族","东乡族","高山族","拉祜族","水族","佤族","纳西族","羌族","土族",
    "仫佬族","锡伯族","柯尔克孜族","达斡尔族","景颇族","毛南族","撒拉族","布朗族","塔吉克族",
    "阿昌族","普米族","鄂温克族","怒族","京族","基诺族","德昂族","保安族","俄罗斯族","裕固族",
    "乌孜别克族","门巴族","鄂伦春族","独龙族","塔塔尔族","赫哲族","珞巴族"
}

# ===== 替换映射 =====
REPLACE_MAP = {
    "保保族": "傈僳族",
    "保康族": "傈僳族",
    "倮倮族": "傈僳族",
    "何昌族": "阿昌族",
    "普禾族": "普米族",
    "芯族": "怒族",
    "苗焕": "苗族",
}
# ==========================

# ===== 正则模式 =====
RE_HEADING = re.compile(r"^(#{1,6})\s*\d{1,4}[\.\、,，．：:\s]*.+$")
RE_ETHNICITY_LINE = re.compile(r"^\s*>\s*([\u4e00-\u9fa5——\s]+)$")
# ==========================


def clean_ethnicity(raw: str) -> str:
    """清理民族名称中的杂字符"""
    return re.sub(r"[^\u4e00-\u9fa5——]", "", raw or "").strip()


def check_ethnicity(file_path: Path):
    """检查Markdown文件中 '>' 开头的民族名称是否合法"""
    lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    invalid = []
    current_heading = "（无标题）"

    for i, raw in enumerate(lines, start=1):
        line = raw.strip()
        if RE_HEADING.match(line):
            current_heading = line
            continue
        if not line.startswith(">"):
            continue
        m = RE_ETHNICITY_LINE.match(line)
        if not m:
            continue
        ethnicity = clean_ethnicity(m.group(1))
        if not ethnicity or ethnicity == "——":
            continue
        if ethnicity not in VALID_ETHNICITIES:
            invalid.append({
                "heading": current_heading,
                "line_no": i,
                "ethnicity": ethnicity,
                "status": "❌ Not in dict"
            })
    return invalid


def export_csv(invalid_list, output_path):
    """将无效民族名称导出为CSV"""
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["Heading", "LineNo", "Ethnicity", "Status"])
        for item in invalid_list:
            writer.writerow([item["heading"], item["line_no"], item["ethnicity"], item["status"]])
    print(f"\n🧾 已输出报告：{output_path}")


def replace_ethnicities(text: str, mapping: dict):
    """执行批量替换并统计替换次数"""
    stats = {}
    for old, new in sorted(mapping.items(), key=lambda x: len(x[0]), reverse=True):
        pattern = re.compile(re.escape(old))
        matches = len(pattern.findall(text))
        if matches > 0:
            text = pattern.sub(new, text)
            stats[old] = matches
    return text, stats


def main():
    ip = Path(INPUT_PATH)
    if not ip.exists():
        raise FileNotFoundError(f"❌ 找不到文件: {ip}")

    if VALIDATION_MODE:
        # --- 模式1：合法性验证 ---
        invalid_entries = check_ethnicity(ip)
        print("====== 民族合法性检测 ======")
        if not invalid_entries:
            print("✅ 所有民族名称均在合法字典中。")
        else:
            print(f"⚠️ 检测到 {len(invalid_entries)} 个非法民族名称：")
            for item in invalid_entries:
                print(f"{item['line_no']:>5} | {item['heading']} | {item['ethnicity']}")
            export_csv(invalid_entries, Path(OUTPUT_CSV))
        print("=================================")
    else:
        # --- 模式2：替换修正 ---
        text = ip.read_text(encoding="utf-8", errors="ignore")
        replaced_text, stats = replace_ethnicities(text, REPLACE_MAP)
        ip.write_text(replaced_text, encoding="utf-8")

        if stats:
            total = sum(stats.values())
            for old, count in stats.items():
                print(f"{old} → {REPLACE_MAP[old]} ：{count} 处")
            print(f"总计替换：{total} 处")
        else:
            print("未检测到可替换的民族名称。")


if __name__ == "__main__":
    main()
# 创建时间: 2025/10/28 14:55
