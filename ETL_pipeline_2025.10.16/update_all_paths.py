# 创建时间: 2025/10/17 12:00
# update_all_paths.py
"""
功能：
批量扫描目录下所有 .py 文件，
自动替换路径字符串中的地区名（如 sichuan → yunnan），
并同时检测并替换 REGION = "xxx" 配置语句。
支持预览模式、自动备份与 CSV 修改报告。
⚠️ 注意：
以下替换规则仅修改静态定义（如 REGION = "sichuan"），
不会修改动态定义（如 REGION = args.region）。

"""

import os
import re
import shutil
import csv
from datetime import datetime

# === 配置区 ===
BASE_DIR = r"D:\pythonprojects\folktales\ETL_pipeline_2025.10.16"
OLD_REGION = "sichuan"
NEW_REGION = "yunnan"
PREVIEW = True
REPORT_DIR = r"I:\中国民间传统故事\分卷清洗\yunnan"
REPORT_NAME = f"path_change_report_{NEW_REGION}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"

# 匹配路径定义语句
RE_PATH_LIKE = re.compile(
    r'(?P<key>\w*path\w*|\w*file\w*|\w*csv\w*|\w*out\w*)\s*=\s*r?"([^"\']+)"',
    re.IGNORECASE
)

# ✅ 新增：匹配 REGION = "xxx" 定义语句
RE_REGION_LINE = re.compile(
    r'REGION\s*=\s*["\'](?P<region>[a-zA-Z_]+)["\']'
)

changes = []


def replace_region_in_path(text: str) -> str:
    """仅替换路径中的地区名部分"""
    pattern = re.compile(OLD_REGION, re.IGNORECASE)
    return pattern.sub(NEW_REGION, text)


def process_script(file_path: str):
    """扫描并替换单个脚本中的路径和 REGION 定义"""
    with open(file_path, "r", encoding="utf-8") as f:
        original_text = f.read()

    new_text = original_text
    changed = False

    # --- 匹配路径定义 ---
    matches = RE_PATH_LIKE.findall(original_text)
    for key, path in matches:
        if OLD_REGION.lower() in path.lower():
            new_path = replace_region_in_path(path)
            changed = True
            changes.append({
                "script_name": os.path.basename(file_path),
                "path_type": key,
                "old_path": path,
                "new_path": new_path
            })
            print(f"🔹 {os.path.basename(file_path)} | {key}")
            print(f"    {path}")
            print(f" →  {new_path}\n")
            new_text = new_text.replace(path, new_path)

    # --- ✅ 新增逻辑：检测 REGION 定义并替换 ---
    region_match = RE_REGION_LINE.search(original_text)
    if region_match:
        region_value = region_match.group("region")
        if region_value.lower() == OLD_REGION.lower():
            new_text = RE_REGION_LINE.sub(f'REGION = "{NEW_REGION}"', new_text)
            changed = True
            changes.append({
                "script_name": os.path.basename(file_path),
                "path_type": "REGION",
                "old_path": region_value,
                "new_path": NEW_REGION
            })
            print(f"🔸 {os.path.basename(file_path)} | REGION")
            print(f"    {region_value}")
            print(f" →  {NEW_REGION}\n")

    # --- 写入或预览 ---
    if not changed:
        print(f"⚪ {os.path.basename(file_path)} 无需修改。\n")
        return

    if not PREVIEW:
        backup = file_path + ".bak"
        shutil.copy2(file_path, backup)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_text)
        print(f"✅ 已修改并保存：{os.path.basename(file_path)}\n")
    else:
        print(f"👁️ 预览模式：未保存修改。\n")


def export_report():
    """导出修改统计CSV"""
    if not changes:
        print("📭 无修改记录，不生成报告。")
        return

    os.makedirs(REPORT_DIR, exist_ok=True)
    report_path = os.path.join(REPORT_DIR, REPORT_NAME)

    with open(report_path, "w", newline="", encoding="utf-8-sig") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        f.write(f"# 地区替换：{OLD_REGION} → {NEW_REGION}   生成时间：{timestamp}\n")
        writer = csv.DictWriter(f, fieldnames=["script_name", "path_type", "old_path", "new_path"])
        writer.writeheader()
        writer.writerows(changes)

    print(f"\n📊 修改统计报告已生成：{report_path}")
    print(f"共记录 {len(changes)} 条修改。")


def main():
    print(f"\n📁 工作目录: {BASE_DIR}")
    print(f"🔁 替换地区: {OLD_REGION} → {NEW_REGION}")
    print(f"👁️ 模式: {'预览' if PREVIEW else '实际修改'}")
    print(f"📝 报告输出路径: {REPORT_DIR}\n")

    for root, _, files in os.walk(BASE_DIR):
        for fname in files:
            if fname.endswith(".py") and fname != os.path.basename(__file__):
                process_script(os.path.join(root, fname))

    export_report()
    print("\n🎯 批量替换完成。")


if __name__ == "__main__":
    main()
