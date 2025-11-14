# -*- coding: utf-8 -*-
# Updated: 2025/11/05
# 文件名称: 5.1_titles_normalize.py
# 版本说明: unified_header_v13（标准日志与I/O接口）
# ------------------------------------------------------------
# 功能简介:
#   标题等级梳理（单文件输入版）
#   - 识别并重新分级 H1~H5 标题；
#   - 放宽规则支持民族名、附记；
#   - 自动输出规范化 Markdown 与 CSV 统计。
# ------------------------------------------------------------

import os
import re
import csv
import sys
from pathlib import Path

# ✅ 项目统一工具模块
sys.path.append(str(Path(__file__).resolve().parents[1]))  # 添加父目录

# ✅ 统一文件 I/O 与日志模块
from utils.template_script_header_manual import (
    load_text, save_text, log_stage, log_summary
)

# ✅ 中文文本标准化模块
from utils.text_normalizer import normalize_chinese_text

# ==========================================================
# 路径配置
# ==========================================================
INPUT_PATH    = Path(r"I:\中国民间传统故事\分卷清洗\sichuan\Chinese Folk Tales_sichuan.md")
OUTPUT_TARGET = Path(r"I:\中国民间传统故事\分卷清洗\sichuan\5.1_Chinese Folk Tales_sichuan.md")
CSV_PATH      = Path(r"I:\中国民间传统故事\分卷清洗\sichuan\5.1_sichuan_heading_stats.csv")

DEBUG_SHOW_PER_LEVEL = 3  # 每级打印多少条命中示例

# ==========================================================
# 通用符号与正则工具
# ==========================================================
PUNCT_WS = r"\s,\.，。:：;；!！\?？·・—\-_\~`'\"“”‘’\(\)（）\[\]【】<>《》、…⋯．·"
ROM_NUMS = "一二三四五六七八九十百千零〇○"

def build_fuzzy_regex(text: str) -> re.Pattern:
    """允许任意空白/标点间隔的宽松匹配"""
    core = re.sub(f"[{PUNCT_WS}]", "", text)
    if not core:
        return re.compile(r"^(?!)$")
    sep = f"[{PUNCT_WS}]*"
    pattern = rf"^\s*[{PUNCT_WS}]*" + sep.join(map(re.escape, core)) + rf"[{PUNCT_WS}]*\s*$"
    return re.compile(pattern)

# ==========================================================
# 标题规则定义
# ==========================================================
H1_TITLES = [
    "前言", "后记",
    "汉族","壮族","满族","回族","苗族","维吾尔族","土家族","彝族","蒙古族","藏族","布依族","侗族","瑶族",
    "朝鲜族","白族","哈尼族","哈萨克族","傣族","黎族","傈僳族","仡佬族","拉祜族","东乡族","佤族","水族",
    "纳西族","羌族","土族","仫佬族","锡伯族","柯尔克孜族","达斡尔族","景颇族","撒拉族","布朗族","毛南族",
    "塔吉克族","普米族","阿昌族","怒族","鄂温克族","京族","基诺族","德昂族","乌孜别克族","俄罗斯族","裕固族",
    "保安族","塔塔尔族","独龙族","鄂伦春族","赫哲族","门巴族","珞巴族","高山族"
]
H2_TITLES = ["神话", "传说", "故事"]
H3_TITLES = [
    "开天辟地神话","天地开辟神话","自然天象神话","动物植物神话","动植物神话","图腾祖先神话","祖先神话","天体自然神话",
    "洪水人类再繁衍神话","文化起源神话","文化起源和祖先神话","神和英雄神话","英雄神话",
    "人物传说","三国蜀汉人物传说","文人传说","现代革命家传说",
    "史事传说","地方传说","名山传说","风俗传说","动植物传说","动物植物传说","丰都鬼城传说",
    "土特产传说","民间工艺传说",
    "动物故事","幻想故事","鬼狐精怪故事","生活故事",
    "机智人物故事","寓言故事","笑话","寓言"
]

# 模糊匹配规则集
H1_PATTERNS = [build_fuzzy_regex(t) for t in H1_TITLES]
H2_PATTERNS = [build_fuzzy_regex(t) for t in H2_TITLES]
H3_PATTERNS = [build_fuzzy_regex(t) for t in H3_TITLES]

# ==========================================================
# 各级正则规则
# ==========================================================
# （一）（二）……
RE_H2_NUM = re.compile(rf"^\s*[（(]\s*[{ROM_NUMS}]+\s*[)）]\s*$")

# H4：数字 + 标题，标题字数 ≤ 15
RE_H4_NUM_TITLE = re.compile(rf"^\s*\d{{1,5}}\s*(?:[{PUNCT_WS}]*)\s*(?P<title>.+?)\s*$")

# H5：行首出现“附”，且整行长度 < 10
RE_H5_RELAXED = re.compile(rf"^\s*[{PUNCT_WS}]*附")

# 去除所有开头的 #
RE_ALL_LEADING_HASHES = re.compile(r"^\s{0,3}#{1,6}\s*")

# ==========================================================
# 工具函数
# ==========================================================
def strip_all_leading_hashes(text: str) -> str:
    """去除行首所有 Markdown 井号"""
    s = text
    while True:
        new = RE_ALL_LEADING_HASHES.sub("", s, count=1)
        if new == s:
            return s.strip()
        s = new

def count_title_chars(s: str) -> int:
    """统计标题字数（去标点空白）"""
    return len(re.sub(f"[{PUNCT_WS}]", "", s))

def visible_text(line: str) -> str:
    return line.strip()

# ==========================================================
# 核心：逐行匹配级别
# ==========================================================
def match_level(line: str):
    """
    返回 (level, title_text, had_hash)
    - H5：以“附”开头 + 行长<10；
    - H4：数字 + 标题（≤15字）；
    - H2：（一）（二）…；
    - H1/H3：模糊匹配；
    - 未命中且原行含# => 去#。
    """
    raw = line.rstrip("\n")
    had_hash = bool(re.match(r"^\s*#", raw))
    content = strip_all_leading_hashes(raw)
    if not content.strip():
        return None, None, had_hash

    if len(raw) < 10 and RE_H5_RELAXED.match(content):
        return 5, visible_text(content), had_hash

    if RE_H2_NUM.match(content):
        return 2, visible_text(content), had_hash

    m_h4 = RE_H4_NUM_TITLE.match(content)
    if m_h4:
        title_part = m_h4.group("title")
        if count_title_chars(title_part) <= 15:
            return 4, visible_text(content), had_hash

    for p in H1_PATTERNS:
        if p.match(content):
            return 1, visible_text(content), had_hash

    for p in H2_PATTERNS:
        if p.match(content):
            return 2, visible_text(content), had_hash

    for p in H3_PATTERNS:
        if p.match(content):
            return 3, visible_text(content), had_hash

    return None, None, had_hash

# ==========================================================
# 规范化函数
# ==========================================================
def normalize_text(lines):
    """对一组文本行进行标题规范化"""
    counts = {i: 0 for i in range(1, 6)}
    samples = {i: [] for i in range(1, 6)}
    out_lines = []

    for line in lines:
        lvl, title, had_hash = match_level(line)
        raw = line.rstrip("\n")

        if lvl:
            out_lines.append("#" * lvl + " " + title + "\n")
            counts[lvl] += 1
            if len(samples[lvl]) < DEBUG_SHOW_PER_LEVEL:
                samples[lvl].append(title)
        else:
            if had_hash:
                plain = strip_all_leading_hashes(raw)
                out_lines.append(plain + "\n")
            else:
                out_lines.append(line)

    return "".join(out_lines), counts, samples

# ==========================================================
# 主流程（带日志阶段）
# ==========================================================
def main():
    log_stage("阶段1：加载与标准化")
    text = load_text(INPUT_PATH)
    text = normalize_chinese_text(text)
    lines = text.splitlines(True)

    log_stage("阶段2：逐行识别 H1~H5")
    new_text, counts, samples = normalize_text(lines)

    log_stage("阶段3：输出 Markdown 与 CSV")
    save_text(OUTPUT_TARGET, new_text)

    # 打印统计信息
    hit_parts = []
    for lvl in range(1, 6):
        n = counts[lvl]
        if n:
            eg = "；".join(samples[lvl])
            hit_parts.append(f"H{lvl}={n}" + (f"（例：{eg}）" if eg else ""))
    hits = "，".join(hit_parts) if hit_parts else "无命中"
    print(f"✅ 标题识别完成 | {hits}")

    rows = [{
        "file": os.path.basename(INPUT_PATH),
        **{f"H{i}": counts[i] for i in range(1, 6)},
        "TOTAL": sum(counts.values())
    }]
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["file","H1","H2","H3","H4","H5","TOTAL"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"📄 统计CSV已生成：{CSV_PATH}")
    log_summary("标题结构规范化", INPUT_PATH, OUTPUT_TARGET)

# ==========================================================
# 程序入口
# ==========================================================
if __name__ == "__main__":
    main()
