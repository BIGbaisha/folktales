# -*- coding: utf-8 -*-
# 创建时间: 2025-10-30
# 版本: v2025.10.30
"""
民族 + 地点 双抽取统一版 v4
----------------------------------------
新增功能：
✅ 支持识别被 Markdown 修饰符包裹的括号，如：
   **(布依族贵阳市花溪区)**、*(布依族)*、——(布依族贵州省)——
✅ CSV 中标题保留数字编号（如 013.当万和蓉莲）
"""

import re
import csv
from pathlib import Path

# ==========================================================
# 文件路径配置
# ==========================================================
INPUT_PATH  = r"I:\中国民间传统故事\分卷清洗\guizhou\6.5_Chinese Folk Tales_guizhou.md"
OUTPUT_PATH = r"I:\中国民间传统故事\分卷清洗\guizhou\6.6.3_Chinese Folk Tales_guizhou.md"
CSV_PATH    = r"I:\中国民间传统故事\分卷清洗\guizhou\6.6.3_ethnicity_location_detected.csv"

ONLY_DETECT = False       # True = 仅检测打印，不写文件
TARGET_LEVEL = 3          # 目标标题层级（3=###，4=####）
PLACEHOLDER = "——"
# ==========================================================


# ==========================================================
# 正则配置，加入负向匹配
# ==========================================================

RE_HEADING = re.compile(
    rf"^(#{{{TARGET_LEVEL}}})(?!#)\s*(\d+[\.\．]?)?\s*(.+?)\s*$"
)

# 放宽括号匹配：允许括号前后被 markdown 修饰符包裹
RE_PAREN = re.compile(
    r"^[\*\_—\-~>《“”\"\']*\s*[（(]\s*([\u4e00-\u9fa5\s·,，。；;:：、\-——～~]*)\s*[)）]\s*[\*\_—\-~<》“”\"\']*\s*$"
)
RE_EMPTY = re.compile(r"^[\s\u200b\u200c\u200d\uFEFF]*$")
RE_HANZI = re.compile(r"[\u4e00-\u9fff]+")


# ==========================================================
# 功能函数
# ==========================================================
def split_ethnicity_location(text: str):
    """
    根据“族”字分割民族和地点：
    - 若含“族”，以最后一个“族”字为界；
    - 若不含“族”，全部视为地点；
    - 自动去除空格、全角空格、轻微标点；
    """
    raw = text.strip()
    # 清理空格和轻微标点
    raw = re.sub(r"[　\s·,，。；;:：、\-——~～]", "", raw)
    # 只保留汉字和“族”
    raw = re.sub(r"[^\u4e00-\u9fa5族]", "", raw)

    if not raw:
        return PLACEHOLDER, PLACEHOLDER

    ethnicity = ""
    location = ""

    if "族" in raw:
        idx = raw.rfind("族") + 1
        ethnicity = raw[:idx]
        location = raw[idx:]
    else:
        ethnicity = PLACEHOLDER
        location = raw

    ethnicity = ethnicity.strip() or PLACEHOLDER
    location = location.strip() or PLACEHOLDER
    return ethnicity, location


def transform(lines):
    """主逻辑"""
    out = []
    i = 0
    n = len(lines)
    results = []

    while i < n:
        line = lines[i]
        m = RE_HEADING.match(line)

        if not m:
            out.append(line)
            i += 1
            continue

        heading_num = m.group(2) or ""
        heading_text = m.group(3).strip()
        heading_full = (heading_num + heading_text).strip()

        out.append(line)
        j = i + 1

        # 跳过空行
        while j < n and RE_EMPTY.match(lines[j]):
            out.append(lines[j])
            j += 1

        ethnicity = PLACEHOLDER
        location = PLACEHOLDER
        raw_line = ""

        if j < n:
            raw_line = lines[j].strip()
            pm = RE_PAREN.match(raw_line)

            if pm:
                raw = pm.group(1).strip()
                ethnicity, location = split_ethnicity_location(raw)
                j += 1
            else:
                # 兼容两行格式 (布依族)\n(惠水县)
                if j + 1 < n:
                    first, second = lines[j].strip(), lines[j + 1].strip()
                    pm1, pm2 = RE_PAREN.match(first), RE_PAREN.match(second)
                    if pm1 and pm2:
                        e1, l1 = split_ethnicity_location(pm1.group(1))
                        e2, l2 = split_ethnicity_location(pm2.group(1))
                        if "族" in pm1.group(1):
                            ethnicity, location = e1, l2
                        elif "族" in pm2.group(1):
                            ethnicity, location = e2, l1
                        else:
                            ethnicity, location = PLACEHOLDER, PLACEHOLDER
                        j += 2

        out.append(f"> 民族：{ethnicity}")
        out.append(f"> 地点：{location}\n")

        results.append({
            "Heading": heading_full,
            "Ethnicity": ethnicity,
            "Location": location,
            "EthnicityMissing": (ethnicity == PLACEHOLDER),
            "LocationMissing": (location == PLACEHOLDER),
            "RawLine": raw_line
        })

        i = j

    return out, results


def export_csv(records, path: Path):
    """导出检测结果 CSV"""
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["编号标题", "民族", "地点", "民族缺失", "地点缺失", "原始行"])
        for r in records:
            writer.writerow([
                r["Heading"], r["Ethnicity"], r["Location"],
                "True" if r["EthnicityMissing"] else "False",
                "True" if r["LocationMissing"] else "False",
                r["RawLine"]
            ])
    print(f"\n🧾 已导出检测报告：{path}")


# ==========================================================
# 主函数
# ==========================================================
def main():
    ip = Path(INPUT_PATH)
    if not ip.exists():
        raise FileNotFoundError(f"输入文件不存在：{ip}")

    lines = ip.read_text(encoding="utf-8", errors="ignore").splitlines()
    processed, results = transform(lines)

    print("====== 检测结果预览 ======")
    for r in results[:15]:
        print(f"📘 {r['Heading']}\n  ↳ 民族：{r['Ethnicity']} | 地点：{r['Location']} | 原行: {r['RawLine']}")
    if len(results) > 15:
        print(f"... 其余 {len(results)-15} 条省略")

    export_csv(results, Path(CSV_PATH))

    missing_eth = sum(r["EthnicityMissing"] for r in results)
    missing_loc = sum(r["LocationMissing"] for r in results)
    print(f"\n📊 统计结果：共 {len(results)} 条记录，民族缺失 {missing_eth} 条，地点缺失 {missing_loc} 条。")

    if ONLY_DETECT:
        print("\n🔍 当前为检测模式，仅打印结果并导出CSV，不写入文件。")
        return

    Path(OUTPUT_PATH).write_text("\n".join(processed), encoding="utf-8")
    print(f"\n✅ 已处理完成并写出文件：{OUTPUT_PATH}")


if __name__ == "__main__":
    main()
