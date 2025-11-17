# -*- coding: utf-8 -*-
# 2025/11/16
# ETL_pipeline_10.31 — 8.1_yaml_extraction.py
# ------------------------------------------------------------
# 功能：
#   1. 解析统一结构 markdown
#   2. 提取 meta block（>地点 / >民族）
#   3. 使用 category alias → category_map → 英文代码
#   4. 在故事标题 ### 下插入 YAML fenced code block
#   5. fenced block 上下各空一行
#   6. 删除 meta block 行
#   7. 保留原正文和 H4 异文
# ------------------------------------------------------------

# ------------------------------------------------------------
# ❗ 所有可配置项都放在 CONFIG 区
# ------------------------------------------------------------

import re
import json
import hashlib
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import yaml

import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.template_script_header_manual import (
    load_text, save_text, log_stage, log_summary
)
from utils.text_normalizer import normalize_chinese_text


# ============================================================
# CONFIG 区（每一卷只改这里）
# ============================================================

REGION = "sichuan"                 # 省份英文，如 sichuan / guizhou / yunnan
REGION_CN = "四川"                 # 中文省名，如 四川 / 贵州 / 云南

# VOLUME_NO = 1                      # 卷号：第几卷 暂时不拼接
BOOK_TITLE = f"书名:中国民间故事集成·{REGION_CN}卷"

# 输入输出路径：自动根据 REGION 生成
INPUT_MD  = Path(fr"I:\中国民间传统故事\分卷清洗\{REGION}\6.9_Chinese Folk Tales_{REGION}.md")
OUTPUT_MD = Path(fr"I:\中国民间传统故事\分卷清洗\{REGION}\8.1_Chinese Folk Tales_{REGION}.md")
OUTPUT_MD_EXTRA = [
    Path(fr"I:\中国民间传统故事\分卷清洗\8.1_yaml\8.1_Chinese Folk Tales_{REGION}.md"),
]


    # 映射表（固定）
CATEGORY_MAP_PATH       = Path(r"D:\pythonprojects\folktales\data\mappings\category_map.json")
ETHNIC_MAP_PATH         = Path(r"D:\pythonprojects\folktales\data\mappings\ethnic_map.json")
CATEGORY_ALIAS_MAP_PATH = Path(r"D:\pythonprojects\folktales\data\mappings\category_alias.json")

PIPELINE_VERSION = "v2025-11-inline-yaml"



# ============================================================
# 加载 mapping
# ============================================================

CATEGORY_MAP = json.loads(CATEGORY_MAP_PATH.read_text(encoding="utf-8"))
ETHNIC_MAP   = json.loads(ETHNIC_MAP_PATH.read_text(encoding="utf-8"))
CATEGORY_ALIAS = json.loads(CATEGORY_ALIAS_MAP_PATH.read_text(encoding="utf-8"))


# ============================================================
# 正则
# ============================================================
H1 = re.compile(r"^#\s+(.+)")
H2 = re.compile(r"^##\s+(.+)")
H3 = re.compile(r"^###\s+(\d{3})\.\s*(.+)")
H4_VAR = re.compile(r"^####\s+(.+)")

META_LINE = re.compile(r"^>\s*(.+?):\s*(.*)")


# ============================================================
# 工具函数
# ============================================================
def sha256(text: str):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def slug(no: int):
    return f"t{no:03d}"

def normalize_category(cn: str):
    cn = cn.strip()
    return CATEGORY_ALIAS.get(cn, cn)

def category_code(cn: str):
    cn = normalize_category(cn)
    return CATEGORY_MAP.get(cn, "unknown")

def ethnic_to_code(cn: str):
    if not cn or cn == "——":
        return "unknown"
    return ETHNIC_MAP.get(cn.strip(), "unknown")



# ============================================================
# 解析 META
# ============================================================

def parse_meta(lines, start_i):
    meta = {
        "collection_place": "——",
        "ethnic_cn": "——",
        "ethnic": "unknown",
    }
    i = start_i
    total = len(lines)

    # 先跳过标题下面的空行
    while i < total and lines[i].strip() == "":
        i += 1

    # 再正式吃 meta block（连续的 > 开头行）
    while i < total:
        l = lines[i].strip()
        if not l.startswith(">"):
            break

        m = META_LINE.match(l)
        if m:
            key, val = m.group(1), m.group(2).strip()

            if key == "地点":
                meta["collection_place"] = val or "——"

            if key == "民族":
                meta["ethnic_cn"] = val
                meta["ethnic"] = ethnic_to_code(val)

        i += 1

    return meta, i


# ============================================================
# 解析 markdown：H1/H2/H3/H4
# ============================================================
def parse_md(lines):

    results = []
    h1_cat = None
    h2_cat = None

    i = 0
    total = len(lines)

    while i < total:
        line = lines[i]

        # H1
        m1 = H1.match(line)
        if m1:
            h1_cat = normalize_category(m1.group(1))
            i += 1
            continue

        # H2
        m2 = H2.match(line)
        if m2:
            h2_cat = normalize_category(m2.group(1))
            i += 1
            continue

        # STORY
        m3 = H3.match(line)
        if m3:
            story_no = int(m3.group(1))
            story_title = m3.group(2).strip()
            story_slug = slug(story_no)

            meta, j = parse_meta(lines, i + 1)

            content = []
            variants = []

            while j < total:
                l2 = lines[j]

                mv = H4_VAR.match(l2)
                if mv:
                    v_title = mv.group(1).strip()
                    v_lines = []
                    j += 1
                    while j < total:
                        l3 = lines[j]
                        if H4_VAR.match(l3) or H3.match(l3) or H2.match(l3) or H1.match(l3):
                            break
                        v_lines.append(l3)
                        j += 1
                    variants.append({
                        "variant_title": v_title,
                        "content": "\n".join(v_lines).strip()
                    })
                    continue

                if H3.match(l2) or H2.match(l2) or H1.match(l2):
                    break

                content.append(l2)
                j += 1

            obj = build_yaml_obj(
                story_no, story_title, story_slug,
                "\n".join(content).strip(),
                h1_cat, h2_cat, meta, variants
            )
            results.append(obj)

            i = j
            continue

        i += 1

    return results



# ============================================================
# 构建 YAML content
# ============================================================
def build_yaml_obj(no, title, slug, content, h1_cat, h2_cat, meta, variants):

    cat_cn = []
    if h1_cat: cat_cn.append(h1_cat)
    if h2_cat: cat_cn.append(h2_cat)

    cat_codes = [category_code(c) for c in cat_cn]

    return {
        "series_code": "stories",
        "book_title": BOOK_TITLE,
        "book_code": f"chinese-folk-tales_{REGION}",
        "region": REGION,
        "region_cn": REGION_CN,
        "book_admin_level": "province",
        "book_admin_level_cn": "省级",

        "title_raw": title,
        "title_clean": title,
        "story_no": no,
        "story_no_padded": f"{no:03d}",
        "title_slug": slug,
        "story_uid": f"stories:chinese-folk-tales_{REGION}:{meta['ethnic']}:{slug}",
        "content_id": f"{meta['ethnic']}_{slug}",

        "categories": cat_codes,
        "category_path_cn": cat_cn,
        "category_root": cat_codes[0] if cat_codes else "",
        "category_leaf": cat_codes[-1] if cat_codes else "",
        "category_depth": len(cat_codes),

        "doc_sha": sha256(content),
        "pipeline_version": PIPELINE_VERSION,
        "extracted_at": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),

        "ethnic": meta["ethnic"],
        "ethnic_cn": meta["ethnic_cn"],
        "collection_place": meta["collection_place"],

        "extra": {
            "story_profile": {
                "ethnicity_profile": meta["ethnic_cn"],
                "region_profile": REGION_CN,
                "motif_profile": [],
                "character_profile": [],
                "era_profile": "",
                "keyword_profile": [],
                "cultural_profile": "",
                "custom_notes": "",
                "pipeline_version": PIPELINE_VERSION
            },
            "variants": variants
        }
    }



# ============================================================
# MAIN — 生成内嵌 YAML 的 Markdown
# ============================================================
def main():

    log_stage("读取 markdown")
    raw = load_text(INPUT_MD)
    raw = normalize_chinese_text(raw)
    lines = raw.splitlines()

    log_stage("解析 stories")
    stories = parse_md(lines)

    story_lookup = {s["story_no"]: s for s in stories}

    new_lines = []
    i = 0
    total = len(lines)

    while i < total:
        line = lines[i]

        m = H3.match(line)
        if m:
            story_no = int(m.group(1))
            obj = story_lookup[story_no]

            new_lines.append(line)
            new_lines.append("")

            new_lines.append("```yaml")
            new_lines.append(
                yaml.dump(obj, allow_unicode=True, sort_keys=False).rstrip("\n")
            )
            new_lines.append("```")
            new_lines.append("")

            # 写完 YAML 后
            i += 1
            # 先跳过空行
            while i < total and lines[i].strip() == "":
                i += 1
            # 再跳过以 > 开头的 meta 行
            while i < total and lines[i].strip().startswith(">"):
                i += 1
            continue


        new_lines.append(line)
        i += 1

    md_out = "\n".join(new_lines).rstrip() + "\n"
    # 原写入
    save_text(OUTPUT_MD, md_out)

    # 新增：循环写入多个备份
    for extra_path in OUTPUT_MD_EXTRA:
        save_text(extra_path, md_out)

    log_stage(f"输出 Markdown → {OUTPUT_MD}")

    log_summary(
        str(INPUT_MD),
        str(OUTPUT_MD),
        {
            "stories": len(stories),
            "pipeline_version": PIPELINE_VERSION
        }
    )


if __name__ == "__main__":
    main()


