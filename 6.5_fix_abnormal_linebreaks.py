# -*- coding: utf-8 -*-
"""
检测 & 修复 “异常断行”（反向规则版）
-------------------------------------------------
规则：
- 当前行末尾为汉字或数字；
- 下一行是空行（含软断符、空格、控制符）；
- 再下一行是正文；
=> 判定为异常断行，可检测或修复。
"""

import re
from pathlib import Path

# ===== 配置 =====
INPUT_PATH  = r"I:\中国民间传统故事\老黑解析版本\正式测试\6.4_Chinese Folk Tales_sichuan_cleaned.md"
OUTPUT_PATH = r"I:\中国民间传统故事\老黑解析版本\正式测试\6.5_Chinese Folk Tales_sichuan_cleaned.md"
ONLY_DETECT = True   # True=仅检测；False=修复
CONTEXT_LINES = 1    # 打印上下文行
# =================

# Markdown结构识别
RE_HEADING = re.compile(r"^(#+)\s*(.*)$")
RE_CODE = re.compile(r"^```")
RE_LIST = re.compile(r"^\s*([-*+]|\d{1,3}[.)])\s+")
RE_QUOTE = re.compile(r"^\s*>")
RE_EMPTY = re.compile(r"^[\s\u200b\u200c\u200d\uFEFF\u2028\u2029]*$")

# 实义字符判定：汉字或数字
RE_VALID_END = re.compile(r"[\u4e00-\u9fff0-9０-９]$")
RE_VALID_START = re.compile(r"^[\u4e00-\u9fff0-9０-９]")

def is_md_boundary(line: str) -> bool:
    """判断是否为 Markdown 结构边界"""
    return (
        RE_HEADING.match(line)
        or RE_CODE.match(line)
        or RE_LIST.match(line)
        or RE_QUOTE.match(line)
        or RE_EMPTY.match(line)
    )

def normalize_line(line: str) -> str:
    """清理所有隐形字符"""
    return re.sub(r"[\u200b\u200c\u200d\uFEFF]", "", line).rstrip("\r\n\u2028\u2029").strip()

def detect_and_fix(lines):
    fixed = []
    merged_records = []
    merged_count = 0
    current_heading = "（无标题）"
    n = len(lines)
    i = 0

    while i < n:
        line = normalize_line(lines[i])

        # 更新标题
        m = RE_HEADING.match(line)
        if m:
            current_heading = f"{'#'*len(m.group(1))} {m.group(2).strip()}"
            fixed.append(lines[i])
            i += 1
            continue

        # --- 检查反向规则：行尾为汉字/数字 + 下一行空行 + 下下行正文 ---
        if (
            i + 2 < n
            and RE_VALID_END.search(line)
            and RE_EMPTY.match(lines[i + 1])
            and RE_VALID_START.search(normalize_line(lines[i + 2]))
            and not is_md_boundary(line)
            and not is_md_boundary(lines[i + 2])
        ):
            merged_line = line + normalize_line(lines[i + 2])
            merged_records.append({
                "heading": current_heading,
                "before": line,
                "after": merged_line,
                "context_before": normalize_line(lines[i-1]) if i > 0 else "",
                "context_after": normalize_line(lines[i+3]) if i + 3 < n else ""
            })
            merged_count += 1

            if ONLY_DETECT:
                fixed.extend([lines[i], lines[i + 1], lines[i + 2]])
            else:
                fixed.append(merged_line + "\n")
            i += 3
            continue

        fixed.append(lines[i])
        i += 1

    return fixed, merged_records, merged_count


def main():
    ip = Path(INPUT_PATH)
    op = Path(OUTPUT_PATH)
    if not ip.exists():
        raise FileNotFoundError(f"输入文件不存在：{ip}")

    lines = ip.read_text(encoding="utf-8", errors="ignore").splitlines(True)
    fixed_lines, merged_records, merged_count = detect_and_fix(lines)

    print("====== 检测结果 ======")
    print(f"总行数：{len(lines)}")
    print(f"检测到异常断行：{merged_count}")
    print("======================")

    if merged_records:
        print("\n====== 异常断行（按最近标题） ======")
        for rec in merged_records:
            print(f"\n{rec['heading']}")
            print(f"  原始：{rec['before']}")
            print(f"  合并：{rec['after']}")
            if rec['context_before']:
                print(f"  上文：{rec['context_before']}")
            if rec['context_after']:
                print(f"  下文：{rec['context_after']}")

    if ONLY_DETECT:
        print("\n🔍 当前为检测模式，仅打印结果，不写文件。")
    else:
        Path(OUTPUT_PATH).write_text("".join(fixed_lines), encoding="utf-8")
        print(f"\n✅ 已写出修复后文件：{OUTPUT_PATH}")

if __name__ == "__main__":
    main()
