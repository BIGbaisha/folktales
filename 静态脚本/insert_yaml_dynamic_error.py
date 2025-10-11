# error：主流程中没有任何运行逻辑
"""
前言/故事 YAML 插入器（动态省市县 + 自动版本时间）
- series_code 可硬编码；书名/省份/行政区/代码自动从文档和配置推断
- pipeline_version / source_file_sha / extracted_at 自动生成（北京时间）
- 删除了原本的JSON文件依赖，改为直接通过配置或文档内容提取行政信息
"""

import re
import json
import unicodedata
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple, List

# =========================
#  路径常量（根据你的机器修改）
# =========================
INPUT_MD_PATH = r"I:\中国民间传统故事\老黑解析版本\v-Chinese Folk Tales_sichuan_shang.text.md"
OUTPUT_MD_PATH = r"I:\中国民间传统故事\老黑解析版本\v-Chinese Folk Tales_sichuan_shang.text.yaml.md"

# 固定前缀
SERIES_CODE = "stories"
BOOK_PREFIX = "chinese-folk-tales_"

# =========================
#   正则
# =========================
STORY_H_RE = re.compile(r"^(\s*(#{2,6})\s+)(\d{3})\.\s*(.+?)\s*$", re.MULTILINE)  # 001. 标题
ANY_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
PREFACE_H1_RE = re.compile(r"^\s*#\s*前言\s*$", re.MULTILINE)
ANY_H1_TXT_RE = re.compile(r"^\s*#\s*([^\r\n]+?)\s*$", re.MULTILINE)
LOC_LINE_RE = re.compile(r"^\s*>\s*地点[:：]\s*(.+?)\s*$", re.MULTILINE)
BOOK_TITLE_LINE_RE = re.compile(r"^\s*#\s*书名[:：]\s*(.+?)\s*$", re.MULTILINE)

NON_ETHNIC_TITLES = {"前言", "序", "序言", "导言"}


# =========================
#   工具函数
# =========================
def ensure_trailing_newlines(s: str, n: int = 1) -> str:
    return s.rstrip("\n") + ("\n" * n)


def build_yaml_block(fields, fence_lang: str = "yaml") -> str:
    def _seq(seq):
        return "[" + ", ".join(f"\"{x}\"" for x in seq) + "]"

    # 判断是前言还是故事，根据其字段的有无，生成不同的yaml块
    if fields.get('story_no') == 0:  # 前言
        lines = [
            f"```{fence_lang}",
            f"series_code: {fields['series_code']}",
            f"book_title: {fields['book_title']}",
            f"book_code: {fields['book_code']}",
            f"ethnic: {fields['ethnic']}",
            f"region: {fields['region']}",  # 提取的region
            f"region_cn: {fields['region_cn']}",  # 提取的region_cn
            f"book_admin_level_cn: {fields['book_admin_level_cn']}",  # 中文的书籍行政级别
            "",
            f"title_raw: {fields['title_raw']}",
            f"title_clean: {fields['title_clean']}",
            f"story_no: {fields['story_no']}",
            f"story_no_padded: \"{fields['story_no_padded']}\"",
            f"title_slug: {fields['title_slug']}",
            "",
            f"location: \"{fields['location']}\"" if fields.get("location") else "location: \"\"",
            "location_codes: []",
            "",
            f"content_id: {fields['content_id']}",
            f"doc_sha: {fields['doc_sha']}",
            "",
            f"pipeline_version: {fields['pipeline_version']}",
            f"source_file_sha: {fields['source_file_sha']}",
            f"extracted_at: {fields['extracted_at']}",
            "```",
        ]
    else:  # 故事
        lines = [
            f"```{fence_lang}",
            f"series_code: {fields['series_code']}",
            f"book_title: {fields['book_title']}",
            f"book_code: {fields['book_code']}",
            f"ethnic: {fields['ethnic']}",
            f"region: {fields['region']}",  # 提取的region
            f"region_cn: {fields['region_cn']}",  # 提取的region_cn
            "",
            f"title_raw: {fields['title_raw']}",
            f"title_clean: {fields['title_clean']}",
            f"story_no: {fields['story_no']}",
            f"story_no_padded: \"{fields['story_no_padded']}\"",
            f"title_slug: {fields['title_slug']}",
            "",
            f"story_uid: {fields['story_uid']}",
            f"categories: {_seq(fields['categories'])}",
            f"category_path_cn: {_seq(fields['category_path_cn'])}" if fields.get(
                "category_path_cn") else "category_path_cn: []",
            f"category_root: \"{fields['category_root']}\"",
            f"category_leaf: \"{fields['category_leaf']}\"",
            f"category_depth: {fields['category_depth']}",
            "",
            f"location: \"{fields['location']}\"" if fields.get("location") else "location: \"\"",
            "location_codes: []",
            "",
            f"content_id: {fields['content_id']}",
            f"doc_sha: {fields['doc_sha']}",
            "",
            f"pipeline_version: {fields['pipeline_version']}",
            f"source_file_sha: {fields['source_file_sha']}",
            f"extracted_at: {fields['extracted_at']}",
            "```",
        ]

    block = "\n".join(lines) + "\n"
    return ensure_trailing_newlines(block, 2)


def normalize_text(t: str) -> str:
    t = t.replace("\ufeff", "")
    t = unicodedata.normalize("NFKC", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def sha256_hex_bytes(b: bytes) -> str:
    import hashlib
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()


def sha256_hex(t: str) -> str:
    import hashlib
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def safe_code_for_label(label: str) -> str:
    import re as _re, hashlib as _hashlib
    try:
        from pypinyin import lazy_pinyin
        p = "".join(lazy_pinyin(label))
        p = _re.sub(r"[^a-z0-9]", "", p.lower())
        if p:
            return p
    except Exception:
        pass
    return "x" + _hashlib.md5(label.encode("utf-8")).hexdigest()[:8]


def pinyin_initials(label: str) -> str:
    try:
        from pypinyin import pinyin, Style
        pys = pinyin(label, style=Style.NORMAL, strict=False)
        letters = "".join(w[0][0] for w in pys if w and w[0])
        return letters.lower()
    except Exception:
        s = safe_code_for_label(label)
        return s[:2]


def unify_code_style(code: str) -> str:
    return code.replace("_", "")


# =========================
#   手动设置的行政区划信息
# =========================
def resolve_admin(prov_name: str, book_title: str) -> Tuple[str, str]:
    # 从书名中提取 `region` 和 `region_cn`
    region = ""
    region_cn = ""
    match = re.search(r"中国民间故事集成(.*)卷", book_title)  # 提取地名
    if match:
        region = match.group(1).strip()  # 提取地名，去除多余空格
        region_cn = region  # 中文地名与 region 一致

    return region, region_cn


# =========================
#   主流程
# =========================
def main():
    # 处理每个故事和前言
    md = "input markdown content"  # 仅为示例占位符
    book_title = "中国民间故事集成·四川卷"  # 示例书名
    ethnic_code = "han"  # 示例民族

    # 提取region和region_cn
    region, region_cn = resolve_admin("四川", book_title)

    # 准备 YAML 字段
    fields_pref = {
        "series_code": "stories",
        "book_title": book_title,
        "book_code": "chinese-folk-tales_sichuan",
        "ethnic": ethnic_code,
        "title_raw": "前言",
        "title_clean": "前言",
        "story_no": 0,
        "story_no_padded": "000",
        "title_slug": "qianyan",
        "story_uid": "stories:chinese-folk-tales_sichuan:han:general_preface:000",
        "categories": ["general"],
        "category_path_cn": ["通用"],
        "category_root": "general",
        "category_leaf": "general",
        "category_depth": 1,
        "region": region,  # 提取的region
        "region_cn": region_cn,  # 提取的region_cn
        "location": "简阳市",  # 如果是更低级别的书籍，手动设置
        "location_codes": ["510185"],
        "content_id": "han_general_preface",
        "doc_sha": "example_doc_sha",
        "pipeline_version": "v2025-09-29",
        "source_file_sha": "example_sha",
        "extracted_at": "2025-09-29T11:02:03+08:00",
        "book_admin_level": "省级",
        "book_admin_level_cn": "省级",
    }

    # 生成 YAML 块
    block = build_yaml_block(fields_pref, "yaml")
    print(block)


# =========================
#   运行主程序
# =========================
if __name__ == "__main__":
    main()
