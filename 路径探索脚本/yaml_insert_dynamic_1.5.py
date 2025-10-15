# 2025-09-30
# -*- coding: utf-8 -*-
"""
process_story_md.py (v1.5)

- Input/Output 路径硬编码（见下方常量）。
- 分类与民族映射从硬编码 JSON 路径加载（category_map.json / ethnic_map.json）。
- PIPELINE_VERSION 运行时按 Asia/Seoul 日期生成：vYYYY-MM-DD。
- 前言识别为 H1 "# 前言"；分类来自 H2/H3；故事为 H4 "#### 001. 标题"。
- 在故事标题下方的首个 "> location: xxx" 会被抽取为 collection_place，并从正文删除。
- 输出 Markdown 采用：标题 → 空行 → ```yaml … ``` → 空行 → 正文。
- 输出：
    1) output_with_yaml.md : 单一 Markdown，逐段插入标题后 YAML 围栏块。
    2) manifest.jsonl      : JSON Lines（每行一个段），便于入关系库/向量库。
Python 3.12；依赖第三方 pypinyin。
"""

from __future__ import annotations

import json
import re
import hashlib
import unicodedata
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime
from zoneinfo import ZoneInfo
import os

from pypinyin import pinyin, Style  # pip install pypinyin

# ---------------- Hardcoded paths and constants ----------------

INPUT_MD = r"I:\中国民间传统故事\老黑解析版本\v-Chinese Folk Tales_sichuan_shang.text.md"
OUTPUT_MD = r"I:\中国民间传统故事\老黑解析版本\v-Chinese Folk Tales_sichuan_shang.text.yaml.md"
OUTPUT_JSONL = r"I:\中国民间传统故事\老黑解析版本\manifest.jsonl"  # JSON Lines for downstream ingestion (RDBMS / Vector DB)

CATEGORY_MAP_PATH = r"/data/mappings/category_map.json"
ETHNIC_MAP_PATH = r"/data/mappings/ethnic_map.json"

SERIES_CODE = "stories"
BOOK_ADMIN_LEVEL = "province"
BOOK_ADMIN_LEVEL_CN = "省级"

# ---------------- Utilities ----------------


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def normalize_text(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"\s+\n", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def slugify_ascii(s: str, default: str = "") -> str:
    t = unicodedata.normalize("NFKD", s)
    t = "".join(ch for ch in t if ord(ch) < 128)
    t = t.lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t or default


def now_iso_seoul() -> str:
    return datetime.now(ZoneInfo("Asia/Seoul")).isoformat()


def today_version_seoul() -> str:
    return "v" + datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d")


def region_slugify_from_cn(region_cn: str) -> str:
    if not region_cn:
        return ""
    syls = pinyin(region_cn, style=Style.NORMAL, heteronym=False)
    merged = "".join(s for [s] in syls).lower()
    merged = re.sub(r"[^a-z0-9]+", "-", merged).strip("-")
    return merged


def detect_book_title(lines: List[str]) -> Optional[str]:
    # Prefer H1 that contains "卷"
    for line in lines:
        if line.startswith("# "):
            t = line[2:].strip()
            if "卷" in t:
                return t
    # Fallback to first H1
    for line in lines:
        if line.startswith("# "):
            return line[2:].strip()
    return None


def detect_region_cn(book_title: str) -> Optional[str]:
    m = re.search(r"·([^·《》]+?)卷", book_title)
    if m:
        return m.group(1).strip()
    return None


def category_code(chs: str, category_map: Dict[str, str]) -> str:
    return category_map.get(chs, slugify_ascii(chs, "cat"))


def detect_ethnic_from_h1(lines: List[str], ethnic_map: Dict[str, str]) -> Optional[str]:
    for line in lines:
        if line.startswith("# "):
            t = line[2:].strip()
            if t == "前言":
                continue
            if t in ethnic_map:
                return ethnic_map[t]
    return None


# ---------------- Parsing core ----------------


@dataclass
class Section:
    kind: str  # "preface" | "story"
    heading: str  # original heading line
    title_raw: str
    title_clean: str
    story_no: int
    story_no_padded: str
    categories_cn: List[str]
    categories_code: List[str]
    body_lines: List[str]
    collection_place: Optional[str] = None


def parse_markdown(md_text: str, category_map: Dict[str, str]) -> Tuple[str, List[Section]]:
    lines = md_text.splitlines()
    book_title = detect_book_title(lines) or "未命名书卷"
    current_cat_cn: List[str] = []
    current_cat_code: List[str] = []
    sections: List[Section] = []

    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]

        # Preface as H1 "# 前言"
        if line.startswith("# "):
            h1 = line[2:].strip()
            if h1 == "前言":
                start = i + 1
                j = start
                while j < n and not lines[j].startswith("# "):
                    j += 1
                body = lines[start:j]
                sections.append(
                    Section(
                        kind="preface",
                        heading=line,
                        title_raw="前言",
                        title_clean="前言",
                        story_no=0,
                        story_no_padded="000",
                        categories_cn=["通用"],
                        categories_code=[category_code("通用", category_map)],
                        body_lines=body,
                    )
                )
                i = j
                continue

        # H2 / H3 as category path
        if line.startswith("## "):
            h2 = line[3:].strip()
            current_cat_cn = [h2]
            current_cat_code = [category_code(h2, category_map)]
            i += 1
            continue

        if line.startswith("### "):
            h3 = line[4:].strip()
            if current_cat_cn:
                current_cat_cn = [current_cat_cn[0], h3]
                current_cat_code = [current_cat_code[0], category_code(h3, category_map)]
            else:
                current_cat_cn = [h3]
                current_cat_code = [category_code(h3, category_map)]
            i += 1
            continue

        # Story headline H4: #### 001. 标题
        m = re.match(r"^####\s+(\d{3})\.\s*(.+?)\s*$", line)
        if m:
            no_padded = m.group(1)
            title_clean = m.group(2).strip()
            no_int = int(no_padded)
            start = i + 1
            j = start
            while j < n and not (
                lines[j].startswith("#### ")
                or lines[j].startswith("## ")
                or lines[j].startswith("# ")
            ):
                j += 1
            body = lines[start:j]

            # Extract collection_place: first occurrence of '> location: xxx'
            collection_place = None
            new_body = []
            loc_pat = re.compile(r"^>\s*location:\s*(.+)\s*$", re.IGNORECASE)
            removed = False
            for bl in body:
                if not removed:
                    pm = loc_pat.match(bl)
                    if pm:
                        collection_place = pm.group(1).strip()
                        removed = True
                        continue  # drop the line
                new_body.append(bl)

            sections.append(
                Section(
                    kind="story",
                    heading=line,
                    title_raw=f"{no_padded}. {title_clean}",
                    title_clean=title_clean,
                    story_no=no_int,
                    story_no_padded=no_padded,
                    categories_cn=current_cat_cn[:] if current_cat_cn else [],
                    categories_code=current_cat_code[:] if current_cat_code else [],
                    body_lines=new_body,
                    collection_place=collection_place,
                )
            )
            i = j
            continue

        i += 1

    return book_title, sections


# ---------------- YAML generation ----------------


def yaml_dump(obj: Any, indent: int = 0) -> str:
    sp = "  " * indent
    if obj is None:
        return "null"
    if isinstance(obj, bool):
        return "true" if obj else "false"
    if isinstance(obj, (int, float)):
        return str(obj)
    if isinstance(obj, str):
        if re.search(r'[:#\-\[\]\{\},]|^\s|\'|"', obj):
            esc = obj.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{esc}"'
        return obj
    if isinstance(obj, list):
        if not obj:
            return "[]"
        lines = []
        for it in obj:
            dumped = yaml_dump(it, indent + 1)
            if "\n" in dumped:
                lines.append(f"- |\n{_indent_block(dumped, indent + 2)}")
            else:
                lines.append(f"- {dumped}")
        return "\n".join(sp + ln if not ln.startswith("- ") else sp + ln for ln in lines)
    if isinstance(obj, dict):
        if not obj:
            return "{}"
        lines = []
        for k, v in obj.items():
            vd = yaml_dump(v, indent + 1)
            if "\n" in vd:
                lines.append(f"{k}:\n{_indent_block(vd, indent + 1)}")
            else:
                lines.append(f"{k}: {vd}")
        return "\n".join(sp + ln for ln in lines)
    return yaml_dump(str(obj), indent)


def _indent_block(s: str, indent: int) -> str:
    sp = "  " * indent
    return "\n".join(sp + ln if ln.strip() != "" else "" for ln in s.splitlines())


def build_yaml_for_section(
    sec: Section,
    *,
    series_code: str,
    book_title: str,
    book_code: str,
    ethnic: str,
    region: Optional[str],
    region_cn: Optional[str],
    pipeline_version: str,
    source_file_sha: str,
    is_preface: bool,
) -> Tuple[Dict[str, Any], str]:
    body_text = "\n".join(sec.body_lines).strip()
    norm = normalize_text(body_text)
    doc_sha = sha256_hex(norm)

    if is_preface:
        cat_path_code = "general_preface"
    else:
        cat_path_code = ".".join(sec.categories_code) if sec.categories_code else "uncategorized"

    story_uid = f"{series_code}:{book_code}:{ethnic}:{cat_path_code}:{sec.story_no_padded}"
    slug = slugify_ascii(sec.title_clean, default=f"t{sec.story_no_padded or '000'}")

    cat_path_cn = sec.categories_cn if sec.categories_cn else (["通用"] if is_preface else [])
    cat_codes = sec.categories_code if sec.categories_code else (["general"] if is_preface else [])
    category_leaf = (cat_codes[-1] if cat_codes else "general") if not is_preface else "general"
    category_depth = len(cat_codes) if cat_codes else (1 if is_preface else 0)

    if is_preface:
        content_id = f"{ethnic}_general_preface"
    else:
        no = sec.story_no_padded or "000"
        content_id = f"{ethnic}_{category_leaf}_{no}"

    base = {
        "series_code": series_code,
        "book_title": book_title,
        "book_code": book_code,
        "ethnic": ethnic,
        "region": region or "",
        "region_cn": region_cn or "",
        "book_admin_level": BOOK_ADMIN_LEVEL,
        "book_admin_level_cn": BOOK_ADMIN_LEVEL_CN,
        "title_raw": sec.title_raw,
        "title_clean": sec.title_clean,
        "story_no": sec.story_no,
        "story_no_padded": sec.story_no_padded,
        "title_slug": slug,
        "story_uid": story_uid,
        "categories": cat_codes if cat_codes else ["general"],
        "category_path_cn": cat_path_cn if cat_path_cn else ["通用"],
        "category_root": cat_codes[0] if cat_codes else "general",
        "category_leaf": category_leaf,
        "category_depth": category_depth if category_depth else 1,
        **({"collection_place": sec.collection_place or ""} if not is_preface else {}),
        "content_id": content_id,
        "doc_sha": doc_sha,
        "pipeline_version": pipeline_version,
        "source_file_sha": source_file_sha,
        "extracted_at": now_iso_seoul(),
        "extra": {},
    }

    # 生成原始 YAML
    yml = yaml_dump(base)

    # 可选：在指定键后插入 n 行空行（分组更清晰）
    def _add_blank_lines(yml_text: str, after_keys: list[str], n: int = 1) -> str:
        lines = yml_text.splitlines()
        out = []
        for ln in lines:
            out.append(ln)
            if any(ln.startswith(f"{k}:") for k in after_keys):
                for _ in range(n):  # 连续插入 n 行空行
                    out.append("")
        return "\n".join(out)

    # 需要的话把 n 改成 2/3；也可调整 after_keys 顺序或内容
    yml = _add_blank_lines(
        yml,
        after_keys=[
            "book_admin_level_cn",  # 书籍信息段末
            "story_uid",            # 标题编号段末
            "category_depth",       # 分类段末
            "collection_place",     # 地点段末（前言无此字段时不会插入）
            "source_file_sha",      # ID/哈希段中再分一下
        ],
        n=1
    )

    return base, yml


# ---------------- Main ----------------


def main() -> None:
    # Load mappings from hardcoded JSON files
    if not os.path.exists(CATEGORY_MAP_PATH):
        raise FileNotFoundError(f"Missing category map JSON: {CATEGORY_MAP_PATH}")
    if not os.path.exists(ETHNIC_MAP_PATH):
        raise FileNotFoundError(f"Missing ethnic map JSON: {ETHNIC_MAP_PATH}")
    with open(CATEGORY_MAP_PATH, "r", encoding="utf-8") as f:
        category_map: Dict[str, str] = json.load(f)
    with open(ETHNIC_MAP_PATH, "r", encoding="utf-8") as f:
        ethnic_map: Dict[str, str] = json.load(f)

    # Read input MD and compute source hash
    with open(INPUT_MD, "r", encoding="utf-8") as f:
        md_text = f.read()
    source_file_sha = sha256_hex(normalize_text(md_text))

    # Book-level metadata
    lines = md_text.splitlines()
    book_title = detect_book_title(lines) or "未命名书卷"
    region_cn = detect_region_cn(book_title) or ""
    region_slug = region_slugify_from_cn(region_cn) if region_cn else ""
    book_code = f"chinese-folk-tales_{region_slug or 'unknown'}"

    # Ethnic detected from H1 using ethnic_map (fallback "han")
    ethnic = detect_ethnic_from_h1(lines, ethnic_map) or "han"

    # Runtime pipeline version
    pipeline_version = today_version_seoul()

    # Parse sections
    _, sections = parse_markdown(md_text, category_map)

    # Build outputs
    out_lines: List[str] = []
    manifest_records: List[Dict[str, Any]] = []

    for sec in sections:
        is_preface = sec.kind == "preface"
        rec, yml = build_yaml_for_section(
            sec,
            series_code=SERIES_CODE,
            book_title=book_title,
            book_code=book_code,
            ethnic=ethnic,
            region=region_slug,
            region_cn=region_cn,
            pipeline_version=pipeline_version,
            source_file_sha=source_file_sha,
            is_preface=is_preface,
        )

        # 标题
        out_lines.append(sec.heading)
        out_lines.append("")

        # 标题后 YAML 围栏块
        out_lines.append("```yaml")
        out_lines.append(yml)
        out_lines.append("```")
        out_lines.append("")

        # 正文
        out_lines.extend(sec.body_lines)
        out_lines.append("")

        full_text = "\n".join(sec.body_lines).strip()
        manifest_records.append(rec | {"full_text": full_text, "kind": sec.kind})

    # Write outputs
    with open(OUTPUT_MD, "w", encoding="utf-8") as fo:
        fo.write("\n".join(out_lines).rstrip() + "\n")

    with open(OUTPUT_JSONL, "w", encoding="utf-8") as fj:
        for r in manifest_records:
            fj.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Console summary
    print(f"[OK] Wrote: {OUTPUT_MD}")
    print(f"[OK] Wrote: {OUTPUT_JSONL}")
    print(f"[INFO] pipeline_version={pipeline_version}")
    print(f"[INFO] book_title={book_title}, region_cn={region_cn}, book_code={book_code}, ethnic={ethnic}")
    print(f"[INFO] sections: preface={sum(1 for s in sections if s.kind=='preface')}, stories={sum(1 for s in sections if s.kind=='story')}")


if __name__ == "__main__":
    main()
