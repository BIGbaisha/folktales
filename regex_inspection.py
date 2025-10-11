# 创建时间: 2025/10/9 10:12
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re, sys, csv
from pathlib import Path

# ===== 配置：改成你的路径 =====
TARGET = Path(r"I:\中国民间传统故事\老黑解析版本\v-Chinese Folk Tales_sichuan_shang.text.yaml.regex.md")
REPORT = Path(r"I:\中国民间传统故事\老黑解析版本\REPORT_CLEAN_QA_1.csv")
ENCODING = "utf-8"
# ============================

CJK = r'\u4e00-\u9fff'
RE_CODE_FENCE = re.compile(r'^(\s*)(`{3,}|~{3,})')
RE_ATX = re.compile(r'^(\s{0,3}#{1,6})\s+(.*)$')
RE_TABLE = re.compile(r'^\s*\|.*\|\s*$')

def split_inline_code(line: str):
    parts, buf, in_code = [], [], False
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == '`':
            if buf: parts.append((''.join(buf), in_code)); buf=[]
            in_code = not in_code
            parts.append(('`', True))
            i += 1; continue
        buf.append(ch); i += 1
    if buf: parts.append((''.join(buf), in_code))
    # merge
    out, cur, flag = [], [], None
    for seg, is_code in parts:
        if flag is None: flag, cur = is_code, [seg]
        elif is_code == flag: cur.append(seg)
        else: out.append((''.join(cur), flag)); flag, cur = is_code, [seg]
    if cur: out.append((''.join(cur), flag))
    return out

def files(root: Path):
    if root.is_file():
        yield root; return
    for p in root.rglob("*.md"):
        if p.is_file(): yield p

def check_line(line: str, in_codeblock: bool):
    issues = []
    if in_codeblock:
        # 结构误伤：围栏内不检查内容
        trailing = bool(re.search(r'[ \t]+$', line))
        if trailing: issues.append(("trailing_space", "代码块行尾空格", line))
        return issues

    # 标题检测
    m = RE_ATX.match(line)
    is_heading = bool(m)
    heading_text = m.group(2) if m else ""

    # 行内代码保护：只检非代码片段
    segs = split_inline_code(heading_text if is_heading else line)
    text_parts = [seg for seg, is_code in segs if not is_code]
    text = ''.join(text_parts)

    # 1) 半角中文句读残留（紧邻中文）
    if re.search(rf'(?<=[{CJK}])[\,\.\?\!\;](?=[{CJK}])', text):
        issues.append(("halfwidth_punct", "半角中文句读残留", line))

    # 2) 全角标点前空格 / 后多空格
    if re.search(rf'\s+([，、。；：！？…])', text):
        issues.append(("space_before_fullwidth", "全角标点前有空格", line))
    if re.search(r'([，、。；：！？…])\s{2,}', text):
        issues.append(("multi_space_after_fullwidth", "全角标点后多空格", line))

    # 3) 省略号/破折号异常
    if re.search(r'…{3,}', text) or re.search(r'\.{3,}(?=[^{`])', text):
        issues.append(("ellipsis_weird", "省略号异常", line))
    if re.search(r'[—–―−]{2,}', text):
        issues.append(("dash_weird", "破折号/长横线异常", line))

    # 4) CJK↔CJK 间空格
    if re.search(rf'[{CJK}]\s+[{CJK}]', text):
        issues.append(("cjk_cjk_space", "CJK↔CJK 间空格", line))

    # 5) 开引/左括后空格
    if re.search(r'[“‘（《【「『]\s+', text):
        issues.append(("space_after_opening", "开引号/左括号后空格", line))

    # 6) 中西混排夹缝空格
    if re.search(rf'(?<=[A-Za-z0-9])\s+(?=[{CJK}])', text) or re.search(rf'(?<=[{CJK}])\s+(?=[A-Za-z0-9])', text):
        issues.append(("cjk_latin_gap", "中西相邻夹缝空格", line))

    # 7) URL/时间误改检测（保守抽样：出现中文句读紧邻 :// 或 12:30）
    if re.search(r'：//', text):
        issues.append(("url_colon_fullwidth", "URL 中出现全角冒号", line))
    if re.search(r'[0-9]：[0-9]{2}', text):
        issues.append(("time_colon_fullwidth", "时间中出现全角冒号", line))

    # 8) 行尾空格
    if re.search(r'[ \t]+$', line):
        issues.append(("trailing_space", "行尾多余空格", line))

    # 9) 标题专属：半角冒号/结尾冒号
    if is_heading:
        plain = text.strip()
        if re.search(r':(?!//)', plain):
            issues.append(("heading_halfwidth_colon", "标题含半角冒号", line))
        if re.search(r'[:：]\s*$', plain):
            issues.append(("heading_trailing_colon", "标题以冒号结尾", line))

    # 10) Markdown 结构保护：简单断言（不应出现被替换的 #/*/> 等）
    # 这里仅提示：若 # 前缀非半角 #，视作潜在误改
    if re.match(r'^\s*[＃]+', line):
        issues.append(("fullwidth_hash", "标题前缀由全角＃组成", line))

    return issues

def quality_scan(path: Path):
    rows = []
    totals = {
        "files": 0, "lines": 0, "issue_lines": 0, "trailing_spaces": 0
    }
    for fp in files(path):
        totals["files"] += 1
        try:
            lines = fp.read_text(encoding=ENCODING, errors="ignore").splitlines()
        except Exception as e:
            print(f"[SKIP] {fp} ({e})", file=sys.stderr)
            continue

        in_block = False
        fence_ch = None
        for i, ln in enumerate(lines, 1):
            m = RE_CODE_FENCE.match(ln)
            if m:
                token = m.group(2)[0]
                if not in_block:
                    in_block, fence_ch = True, token
                else:
                    if token == fence_ch:
                        in_block, fence_ch = False, None
                # 仍计入 trailing 空格
                if re.search(r'[ \t]+$', ln):
                    rows.append((str(fp), i, "trailing_space", "围栏行尾空格", ln.strip()))
                    totals["trailing_spaces"] += 1
                totals["lines"] += 1
                continue

            issues = check_line(ln, in_block)
            totals["lines"] += 1
            if issues:
                totals["issue_lines"] += 1
                for key, desc, sample in issues:
                    if key == "trailing_space":
                        totals["trailing_spaces"] += 1
                    rows.append((str(fp), i, key, desc, sample.strip()))
    return rows, totals

def write_csv(rows):
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with REPORT.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["file","line_no","issue_key","issue_desc","sample_line"])
        for r in rows:
            w.writerow(r)

def main():
    if not TARGET.exists():
        print(f"[ERROR] not found: {TARGET}", file=sys.stderr); return 2
    rows, totals = quality_scan(TARGET)
    # 终端摘要
    print("\n=== MD 正则清洗质量体检 ===")
    print(f"文件数: {totals['files']}  总行数: {totals['lines']}")
    print(f"出现问题的行: {totals['issue_lines']}  行尾空格计数: {totals['trailing_spaces']}")
    print(f"详情 CSV: {REPORT}")
    # 示例预览（前 20 条）
    for r in rows[:20]:
        print(f"- {r[2]:>26} | {r[0]}:{r[1]} | {r[4]}")
    write_csv(rows)
    # 简单打分（0~100）
    if totals["lines"] == 0:
        score = 100
    else:
        penalty = min(1.0, totals["issue_lines"]/max(1, totals["lines"]))
        score = round(100 * (1 - penalty), 1)
    print(f"\n粗略质量分：{score}/100（问题行占比越低越好）")
    return 0

if __name__ == "__main__":
    main()