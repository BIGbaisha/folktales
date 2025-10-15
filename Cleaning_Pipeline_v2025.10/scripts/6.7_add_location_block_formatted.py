# 创建时间: 2025/10/15 14:20
# 版本: v2025.10
# -*- coding: utf-8 -*-
"""
6.7_add_location_block.py
----------------------------------------
功能：识别并标准化地名（保留原逻辑）
输入输出路径硬编码为：
I:\中国民间传统故事\老黑解析版本\正式测试\\
"""


识别故事标题下地名并标准化为 YAML 友好格式（含“缺页”过滤逻辑）
------------------------------------------------
新增逻辑：
- 若标题下的下一行含“缺页”二字，则不当作地名；
- 仅在行总汉字数 ≤ 15 且无标点时，才将该行当地名。

"""

import re
import csv
from pathlib import Path

# ===== 配置 =====
INPUT_PATH  = r"I:\中国民间传统故事\老黑解析版本\正式测试\6.6_Chinese Folk Tales_sichuan_cleaned.md"
OUTPUT_PATH = r"I:\中国民间传统故事\老黑解析版本\正式测试\6.7_Chinese Folk Tales_sichuan_cleaned.md"
CSV_PATH    = r"I:\中国民间传统故事\老黑解析版本\正式测试\6.6_location_detected.csv"

ONLY_DETECT = False   # True=仅检测打印; False=写出文件
PLACEHOLDER = "——"     # 无地名占位符
MAX_LINE_HANZI = 15   # “可视为地名”的行最大汉字数
# =================

# 四级编号标题
re_heading = re.compile(r'^(####)\s*(\d+)[\.\．]?\s*(.+?)\s*$', re.UNICODE)
# 括号地名行
re_location_paren = re.compile(r'^\s*[（(]\s*([^\s()（）]+?)\s*[)）]\s*$', re.UNICODE)
# 已标准化的 > 地点 行
re_location_line = re.compile(r'^\s*>\s*地点[:：]\s*(.*)\s*$', re.UNICODE)
# 汉字检测
re_hanzi = re.compile(r'[\u4e00-\u9fff]')


def count_hanzi(text: str) -> int:
    """统计汉字数"""
    return len(re_hanzi.findall(text))


def is_potential_location_line(line: str) -> bool:
    """
    判断某行是否可能是“地名行”：
    - 不含明显标点；
    - 汉字数 <= MAX_LINE_HANZI；
    - 不包含“缺页”。
    """
    line = line.strip()
    if not line:
        return False
    if "缺页" in line:
        return False
    if any(p in line for p in ["。", "，", "！", "？", "；"]):
        return False
    hanzi_len = count_hanzi(line)
    return 0 < hanzi_len <= MAX_LINE_HANZI


def transform(lines):
    """主逻辑"""
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

        heading_num = m.group(2)
        heading_title = m.group(3).strip()

        out.append(line)
        j = i + 1

        # 跳过空行
        if j < n and lines[j].strip() == "":
            out.append(lines[j])
            j += 1

        # 若已有 > 地点： 行
        if j < n and (ml := re_location_line.match(lines[j])):
            loc = ml.group(1).strip() or PLACEHOLDER
            results.append((heading_num, heading_title, loc, "已存在", lines[j].strip()))
            out.append(lines[j])
            i = j + 1
            continue

        location = None
        raw_line = ""
        status = "空缺或正文"

        if j < n:
            raw_line = lines[j].strip()

            # 1️⃣ 括号地名
            lm = re_location_paren.match(raw_line)
            if lm:
                location = lm.group(1).strip("、，。 \t")
                status = "括号地名"

            # 2️⃣ 非括号短句地名
            elif is_potential_location_line(raw_line):
                location = raw_line.strip("、，。 \t")
                status = "短句地名"

        if location:
            out.append(f"> 地点：{location}")
            results.append((heading_num, heading_title, location, status, raw_line))
        else:
            out.append(f"> 地点：{PLACEHOLDER}")
            results.append((heading_num, heading_title, PLACEHOLDER, status, raw_line))

        out.append("")  # 保持标题与正文间空行
        i = j + (1 if location else 0)

    return out, results


def export_csv(records, path: Path):
    """输出 CSV"""
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["编号", "标题", "地点", "状态", "原始行"])
        for num, title, loc, status, raw in records:
            writer.writerow([num, title, loc, status, raw])
    print(f"\n🧾 已导出 CSV 文件：{path}")


def main():
    ip = Path(INPUT_PATH)
    if not ip.exists():
        raise FileNotFoundError(f"输入文件不存在：{ip}")

    lines = ip.read_text(encoding="utf-8", errors="ignore").splitlines()
    processed, results = transform(lines)

    print("====== 检测结果 ======")
    print(f"共检测到故事标题 {len(results)} 个\n")
    for num, title, loc, status, raw in results[:15]:
        print(f"#### {num}. {title}\n  ↳ 地点：{loc}  ({status}) 原行: {raw}")
    if len(results) > 15:
        print(f"... 其余 {len(results)-15} 条省略")

    export_csv(results, Path(CSV_PATH))

    if ONLY_DETECT:
        print("\n🔍 当前为检测模式，仅打印结果并导出CSV，不写入文件。")
        return

    Path(OUTPUT_PATH).write_text("\n".join(processed), encoding="utf-8")
    print(f"\n✅ 已处理完成并写出文件：{OUTPUT_PATH}")


if __name__ == "__main__":
    main()
