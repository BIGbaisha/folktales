# 创建时间: 2025/10/10 11:35
# -*- coding: utf-8 -*-
"""
扫描 Markdown，找出所有以“族”结尾的中文词；
允许“族”前的汉字之间掺杂空格（如“维 吾 尔 族”“彝 族”）；
匹配后会去除内部空白再与民族映射表比对，未命中的导出 CSV。
"""

import os
import re
import json
import csv
import difflib

# ====== 硬编码路径 ======
mapping_path = r"D:\pythonprojects\folktales\data\mappings\ethnic_map.json"   # 形如 {"汉族":"han", "壮族":"zhuang", ...}
input_paths = [
    r"I:\中国民间传统故事\老黑解析版本\正式测试\Chinese Folk Tales_sichuan.md",
    "input2.md",
    "input3.md",
]
output_csv = r"I:\中国民间传统故事\老黑解析版本\正式测试\ethnic_unknowns_1.csv"


# ====== 可调参数 ======
MIN_PRE_CHARS = 1      # 抓“族”前至少几个字（统计时不计空格）
MAX_PRE_CHARS = 5      # 抓“族”前最多几个字（不计空格；用于最长优先）
MAX_CH_WORD    = 12    # 允许的最大“汉字或空格”长度（含空格，保险放宽）
FUZZY_TOPN     = 3
FUZZY_CUTOFF   = 0.6

# 常见需要排除的“非民族词”（比较时会先去空格）
EXCLUDE_TERMS = {
    "民族", "氏族", "家族", "部族", "宗族", "族谱", "族群", "族人"
}

# ====== 正则：允许“汉字 或 空白”反复，最后以“族”结尾 ======
# 说明：
# - \s 会覆盖半角空格、制表符、换行；我们再额外处理全角空格 \u3000 和 NBSP \xa0
CHN = r"[\u4e00-\u9fff]"
SPACE_CLASS = r"(?:\s|\u3000|\xa0)"
CHN_OR_SPACE = rf"(?:{CHN}|{SPACE_CLASS})"
PATTERN = re.compile(rf"({CHN_OR_SPACE}{{1,{MAX_CH_WORD}}}族)")

def normalize_spaces(s: str) -> str:
    """统一空白：把各类空白都当空格，再去掉所有空白"""
    # 先把全角空格与 NBSP 归一为普通空格，再删去所有空格
    return re.sub(r"\s+", "", s.replace("\u3000", " ").replace("\xa0", " "))

def load_mapping(path):
    with open(path, "r", encoding="utf-8") as f:
        mp = json.load(f)
    mapping_full = {}
    for k, v in mp.items():
        if not k:
            continue
        k = normalize_spaces(k.strip())
        if k.endswith("族"):
            mapping_full[k] = v
        else:
            mapping_full[k + "族"] = v
    # 反向（去“族”）索引
    nozu_to_full = {}
    for k in mapping_full.keys():
        base = k[:-1] if k.endswith("族") else k
        nozu_to_full[base] = k
    return mapping_full, nozu_to_full

def iter_zu_words(line):
    """在一行里迭代允许空格夹杂的 '...族' 片段"""
    for m in PATTERN.finditer(line):
        word_raw = m.group(1)         # 原样（可能含空格）
        start, end = m.span(1)
        yield word_raw, start, end

def best_map_match(word_raw, mapping_full, nozu_to_full):
    """
    使用“最长优先”在清洗后的词上匹配：
    - 先去除内部空白得到 word（形如 '柯尔克孜族' 或 '彝族'）
    - 在 族 前抓取 MIN..MAX 个“汉字（不计空格）”形成候选子串（含“族”）
    """
    word = normalize_spaces(word_raw)
    if len(word) < 2 or not word.endswith("族"):
        return False, None, None

    # 族前的纯汉字长度
    han_len = len(word) - 1  # 排除最后一个“族”
    # 最长优先
    for pre in range(min(MAX_PRE_CHARS, han_len), MIN_PRE_CHARS - 1, -1):
        cand = word[han_len - pre : ]  # 从倒数 pre 个汉字到“族”的子串
        # 1) 完整键匹配
        if cand in mapping_full:
            return True, cand, mapping_full[cand]
        # 2) 退化：不含“族”的键（兜底）
        base = cand[:-1]
        if base in nozu_to_full:
            full_key = nozu_to_full[base]
            return True, full_key, mapping_full[full_key]
    return False, None, None

def make_context(line, start, end, span=20):
    left = line[max(0, start - span): start]
    mid  = line[start:end]
    right= line[end: end + span]
    return f"…{left}[{mid}]{right}…".replace("\n", " ")

def fuzzy_suggest(target_raw, candidates, topn=3, cutoff=0.6):
    target = normalize_spaces(target_raw)
    return difflib.get_close_matches(target, candidates, n=topn, cutoff=cutoff)

def main():
    if not any(p for p in input_paths):
        print("⚠️ 未提供任何输入路径。")
        return
    if not os.path.exists(mapping_path):
        print(f"❌ 映射表不存在：{mapping_path}")
        return

    mapping_full, nozu_to_full = load_mapping(mapping_path)
    mapping_keys = list(mapping_full.keys())

    rows = []
    unknown_counter = 0

    for path in input_paths:
        if not path:
            continue
        if not os.path.exists(path):
            print(f"⚠️ 跳过不存在的文件：{path}")
            continue

        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for lineno, line in enumerate(lines, start=1):
            for word_raw, s, e in iter_zu_words(line):
                word_norm = normalize_spaces(word_raw)
                # 排除项：先去空白再比较
                if word_norm in EXCLUDE_TERMS:
                    continue

                matched, key, code = best_map_match(word_raw, mapping_full, nozu_to_full)
                if matched:
                    continue  # 命中映射则不导出

                # cand2/cand3 用去空白后的末尾 2/3 字（含“族”）
                cand2 = word_norm[-2:] if len(word_norm) >= 2 else word_norm
                cand3 = word_norm[-3:] if len(word_norm) >= 3 else word_norm

                sugg = fuzzy_suggest(word_raw, mapping_keys, topn=FUZZY_TOPN, cutoff=FUZZY_CUTOFF)

                rows.append({
                    "file": os.path.basename(path),
                    "line": lineno,
                    "word_raw": word_raw,          # 原样（保留空格，便于定位 OCR 问题）
                    "word_norm": word_norm,        # 去空白后（用于比对/修订）
                    "cand2": cand2,
                    "cand3": cand3,
                    "context": make_context(line, s, e, span=20),
                    "suggest_1": sugg[0] if len(sugg) > 0 else "",
                    "suggest_2": sugg[1] if len(sugg) > 1 else "",
                    "suggest_3": sugg[2] if len(sugg) > 2 else "",
                })
                unknown_counter += 1

    if rows:
        with open(output_csv, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "file", "line", "word_raw", "word_norm", "cand2", "cand3",
                "context", "suggest_1", "suggest_2", "suggest_3"
            ])
        # write header + rows
            writer.writeheader()
            writer.writerows(rows)
        print(f"🎯 共发现 {unknown_counter} 处未映射的“*族”词（已放宽空格规则），已导出：{output_csv}")
    else:
        print("✅ 未发现未映射的“*族”词。")

if __name__ == "__main__":
    main()
