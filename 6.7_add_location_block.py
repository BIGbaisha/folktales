# 创建时间: 2025/10/15 11:30
# -*- coding: utf-8 -*-
"""
识别故事标题下地名并标准化为 YAML 友好格式
------------------------------------------------
功能：
1️⃣ 检测或插入 “> 地点：xxx” 行；
2️⃣ 地名可有括号或无括号；
3️⃣ 未检测到地名时仍插入空占位；
4️⃣ 幂等安全，可多次运行；
5️⃣ 兼容清洗后 Markdown 文件（标题下有一空行）；
6️⃣ 自动输出 CSV 文件，包含标题编号、标题、地名。

配置：
- ONLY_DETECT=True：仅检测、打印结果；
- ONLY_DETECT=False：实际写入新文件 + 输出CSV。
"""

import re
import csv
from pathlib import Path

# ===== 配置 =====
INPUT_PATH  = r"I:\中国民间传统故事\老黑解析版本\正式测试\6.6_Chinese Folk Tales_sichuan_cleaned.md"
OUTPUT_PATH = r"I:\中国民间传统故事\老黑解析版本\正式测试\6.7_Chinese Folk Tales_sichuan_cleaned.md"
CSV_PATH    = r"I:\中国民间传统故事\老黑解析版本\正式测试\6.6_location_detected.csv"

ONLY_DETECT = True    # True=仅检测打印; False=写出文件
PLACEHOLDER = "——"     # 无地名占位符
# =================

# 四级编号标题，如：#### 002. 标题（兼容不同点号）
re_heading = re.compile(r'^(####)\s*(\d+)[\.\．]?\s*(.+?)\s*$', re.UNICODE)

# 可能存在的地名形式：（德昌县）、德昌县、（ 德昌县 ）等
re_location_any = re.compile(r'^\s*[（(]?\s*([^\s()（）]+?)\s*[)）]?\s*$', re.UNICODE)

# 已存在的标准化格式行
re_location_line = re.compile(r'^\s*>\s*地点[:：]\s*(.*)\s*$', re.UNICODE)


def transform(lines):
    """
    主处理逻辑
    返回:
      - 新行列表
      - 检测结果（标题编号、标题文本、地名）
    """
    out = []
    i = 0
    n = len(lines)
    results = []

    while i < n:
        line = lines[i]
        m = re_heading.match(line)

        if not m:
            out.append(line)
            i += 1
            continue

        heading_full = m.group(0)
        heading_num = m.group(2)
        heading_title = m.group(3).strip()

        out.append(line)
        j = i + 1

        # 跳过空行
        if j < n and lines[j].strip() == "":
            out.append(lines[j])
            j += 1

        # 若已存在 > 地点：xxx，直接读取并记录
        if j < n and (ml := re_location_line.match(lines[j])):
            loc = ml.group(1).strip() or PLACEHOLDER
            results.append((heading_num, heading_title, loc))
            out.append(lines[j])
            i = j + 1
            continue

        # 否则检测下一行是否为地名形式
        location = None
        if j < n:
            lm = re_location_any.match(lines[j])
            if lm:
                location = lm.group(1).strip("、，。 \t")

        if location:
            out.append(f"> 地点：{location}")
            results.append((heading_num, heading_title, location))
        else:
            out.append(f"> 地点：{PLACEHOLDER}")
            results.append((heading_num, heading_title, PLACEHOLDER))

        # 确保正文前一空行
        out.append("")
        i = j + (1 if location else 0)

    return out, results


def export_csv(records, path: Path):
    """输出检测结果到 CSV"""
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["编号", "标题", "地点"])
        for num, title, loc in records:
            writer.writerow([num, title, loc])
    print(f"\n🧾 已导出 CSV 文件：{path}")


def main():
    ip = Path(INPUT_PATH)
    if not ip.exists():
        raise FileNotFoundError(f"输入文件不存在：{ip}")

    lines = ip.read_text(encoding="utf-8", errors="ignore").splitlines()
    processed, results = transform(lines)

    print("====== 检测结果 ======")
    print(f"共检测到故事标题 {len(results)} 个\n")
    for num, title, loc in results[:15]:
        print(f"#### {num}. {title}\n  ↳ 地点：{loc}")
    if len(results) > 15:
        print(f"... 其余 {len(results)-15} 条省略")

    # 输出CSV（两种模式都执行）
    export_csv(results, Path(CSV_PATH))

    if ONLY_DETECT:
        print("\n🔍 当前为检测模式，仅打印结果并导出CSV，不写入文件。")
        return

    Path(OUTPUT_PATH).write_text("\n".join(processed), encoding="utf-8")
    print(f"\n✅ 已处理完成并写出文件：{OUTPUT_PATH}")


if __name__ == "__main__":
    main()
