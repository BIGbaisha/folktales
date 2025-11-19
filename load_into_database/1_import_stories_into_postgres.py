# -*- coding: utf-8 -*-
"""
将 split_stories/*.md （含 YAML）导入 PostgreSQL
适配 core / meta / mm schema（无 pgvector）
"""

import re
import yaml
from pathlib import Path

from psycopg.types.json import Json
from utils_db.db_conn import get_conn, get_cursor


# ---------------------------------
# 只改这个 REGION
# ---------------------------------
REGION = "yunnan"

STORIES_DIR = Path(r"I:\中国民间传统故事\分卷清洗\8.2_story_storage") / f"{REGION}_split_stories"


# ---------------------------------
# 提取 YAML + 正文
# ---------------------------------
def extract_yaml_and_text(md_text):
    m = re.search(r"```yaml(.*?)```(.*)", md_text, re.S)
    if not m:
        raise ValueError("未找到 ```yaml fenced block")
    yaml_data = yaml.safe_load(m.group(1).strip())
    content_md = m.group(2).strip()
    return yaml_data, content_md


# ---------------------------------
# 插入单个故事
# ---------------------------------
def insert_story(cur, yaml_data, content_md):
    uid = yaml_data["story_uid"]

    # ---------- core.stories ----------
    cur.execute("""
        INSERT INTO core.stories (
            series_code, book_title, book_code,
            region, region_cn,
            book_admin_level, book_admin_level_cn,
            title_raw, title_clean,
            story_no, story_no_padded,
            title_slug, story_uid, content_id,
            category_root, category_leaf, category_depth,
            doc_sha, pipeline_version, extracted_at,
            ethnic, ethnic_cn, collection_place
        )
        VALUES (
            %(series_code)s, %(book_title)s, %(book_code)s,
            %(region)s, %(region_cn)s,
            %(book_admin_level)s, %(book_admin_level_cn)s,
            %(title_raw)s, %(title_clean)s,
            %(story_no)s, %(story_no_padded)s,
            %(title_slug)s, %(story_uid)s, %(content_id)s,
            %(category_root)s, %(category_leaf)s, %(category_depth)s,
            %(doc_sha)s, %(pipeline_version)s, %(extracted_at)s,
            %(ethnic)s, %(ethnic_cn)s, %(collection_place)s
        )
        ON CONFLICT (story_uid) DO NOTHING
    """, yaml_data)

    # ---------- core.story_category ----------
    for cat in yaml_data.get("categories", []):
        cur.execute("""
            INSERT INTO core.story_category (story_uid, category_code)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        """, (uid, cat))

    # ---------- meta.story_profile ----------
    profile = yaml_data.get("extra", {}).get("story_profile", {})

    cur.execute("""
        INSERT INTO meta.story_profile (
            story_uid, ethnicity_profile, region_profile,
            motif_profile, character_profile,
            era_profile, keyword_profile, cultural_profile,
            custom_notes, pipeline_version
        )
        VALUES (
            %s, %s, %s,
            %s, %s,
            %s, %s, %s,
            %s, %s
        )
        ON CONFLICT (story_uid) DO NOTHING
    """, (
        uid,
        profile.get("ethnicity_profile"),
        profile.get("region_profile"),
        Json(profile.get("motif_profile") or []),
        Json(profile.get("character_profile") or []),
        profile.get("era_profile"),
        Json(profile.get("keyword_profile") or []),
        profile.get("cultural_profile"),
        profile.get("custom_notes"),
        profile.get("pipeline_version"),
    ))

    # ---------- meta.story_variants ----------
    for v in yaml_data.get("extra", {}).get("variants", []):
        cur.execute("""
            INSERT INTO meta.story_variants (story_uid, variant_json)
            VALUES (%s, %s)
        """, (uid, Json(v)))

    # ---------- mm.story_contents ----------
    cur.execute("""
        INSERT INTO mm.story_contents (story_uid, content_md)
        VALUES (%s, %s)
        ON CONFLICT (story_uid) DO UPDATE SET content_md = EXCLUDED.content_md
    """, (uid, content_md))


# ---------------------------------
# 主流程
# ---------------------------------
def import_stories():
    conn = get_conn()
    cur = get_cursor(conn)

    print(f"\n🚀 开始导入故事 REGION = {REGION}\n")

    missing_yaml_files = []   # ← 新增：收集 YAML 缺失的文件名

    for f in sorted(STORIES_DIR.glob("*.md")):
        if f.name == "intro.md":
            continue

        text = f.read_text(encoding="utf-8")

        # ---------- YAML 提取 ----------
        try:
            yaml_data, content_md = extract_yaml_and_text(text)
        except Exception as e:
            print(f"❌ YAML 解析失败：{f.name} → {e}")
            missing_yaml_files.append(f.name)   # ← 收集
            continue

        # ---------- 插入故事 ----------
        try:
            insert_story(cur, yaml_data, content_md)
            print(f"✔ 导入成功：{yaml_data['story_uid']}")
        except Exception as e:
            print(f"❌ 导入失败：{yaml_data['story_uid']} → {e}")
            continue

    conn.commit()
    cur.close()
    conn.close()

    # ---------- 集中打印 YAML 缺失 ----------
    if missing_yaml_files:
        print("\n⚠ 以下文件未找到 YAML fenced block：")
        for name in missing_yaml_files:
            print("  -", name)
    else:
        print("\n✔ 所有文件均包含 YAML fenced block")

    print("\n🎉 故事导入完成\n")


if __name__ == "__main__":
    import_stories()
