# run_pipeline.py
# 创建时间: 2025/10/17 12:40

"""
# ============================================================
# 文件名称: run_pipeline.py
# 版本日期: 2025-10-17
# ============================================================
# 【功能说明】
# ------------------------------------------------------------
# 本脚本用于统一调度与执行“中国民间传统故事”文本清洗
# 流水线中 6.x 系列的处理脚本（如正则清洗、格式校验、
# 链接删除等），并在每一步修改性操作完成后，自动调用
# “text_consistency_check.py” 对比前后版本差异，
# 输出章节标题一致性报告。
#
# 【核心功能】
# 1️⃣ 顺序执行 6.1 ~ 6.7 脚本；
# 2️⃣ 每一步执行后，若前一步存在输出文件，则调用
#     text_consistency_check.py 进行一致性检测；
# 3️⃣ 自动生成运行日志（含脚本执行结果、时间戳、
#     检测报告调用记录等）；
# 4️⃣ 支持按地区变量 REGION 自动调整路径；
# 5️⃣ 可兼容不同分卷地区（如四川卷、云南卷、宁夏卷）；
# 6️⃣ 所有输入输出路径均基于 BASE_DIR 自动拼接。
#
# 【路径规则】
# ------------------------------------------------------------
# BASE_DIR = I:\中国民间传统故事\分卷清洗\<REGION>\
# 每个清洗脚本命名格式：
#   6.x_Chinese Folk Tales_<REGION>.py
# 每个 Markdown 文件命名格式：
#   6.x_Chinese Folk Tales_<REGION>.md
#
# 【日志与输出】
# ------------------------------------------------------------
# - 自动生成日志文件 pipeline_run_log_日期时间.txt；
# - 一致性检测报告由 text_consistency_check.py 生成；
# - 日志内容包括：
#     - 各脚本执行时间与结果；
#     - 一致性检测的输入输出文件；
#     - 错误与警告信息。
#
# 【兼容性说明】
# ------------------------------------------------------------
# - 与新版 text_consistency_check.py 完全兼容；
# - 通过命令行参数传递 input_old、input_new、region；
# - 若检测脚本未存在，则跳过检测步骤；
# - 可安全运行于不同省份目录。
#
# 【使用示例】
# ------------------------------------------------------------
#   在当前地区目录下运行：
#     > python run_pipeline.py
#
#   示例路径结构：
#     I:\中国民间传统故事\分卷清洗\yuzhongqu\
#         ├── 6.1_pre_clean_check.py
#         ├── 6.2_regex_clean_enhanced.py
#         ├── ...
#         ├── text_consistency_check.py
#         └── run_pipeline.py
#
# ============================================================

"""

import subprocess
from pathlib import Path
from datetime import datetime

# === 基础配置 ===
REGION = "yuzhongqu"
BASE_DIR = Path(r"I:\中国民间传统故事\分卷清洗") / REGION
LOG_FILE = BASE_DIR / f"pipeline_run_log_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"

# 要执行的脚本序列（按顺序）
SCRIPTS = [
    "6.1_pre_clean_check.py",
    "6.2_regex_clean_enhanced.py",
    "6.3_mathplaceholder_clean.py",
    "6.4_blanks_digits_check.py",
    "6.5_detect_remove_narrator_blocks.py",
    "5.3_links_delete.py",
    "6.6.1_add_location_quote.py",
]

# 一致性检测脚本路径
CHECK_SCRIPT = Path(BASE_DIR) / "text_consistency_check.py"


def log(message: str):
    """写入日志"""
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{timestamp} {message}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run_script(script_path: Path):
    """执行单个脚本"""
    log(f"🚀 开始执行：{script_path.name}")
    result = subprocess.run(["python", str(script_path)], capture_output=True, text=True)
    log(result.stdout)
    if result.stderr.strip():
        log(f"⚠️ 脚本警告/错误：\n{result.stderr}")
    log(f"✅ 完成：{script_path.name}\n")


def run_consistency_check(old_step: str, new_step: str):
    """调用一致性检测脚本"""
    input_old = BASE_DIR / f"{old_step}_Chinese Folk Tales_{REGION}.md"
    input_new = BASE_DIR / f"{new_step}_Chinese Folk Tales_{REGION}.md"

    log(f"🔍 调用一致性检测：{input_old.name} → {input_new.name}")
    subprocess.run([
        "python", str(CHECK_SCRIPT),
        "--input_old", str(input_old),
        "--input_new", str(input_new),
        "--region", REGION
    ], check=False)
    log(f"📊 一致性检测完成 ({old_step} → {new_step})\n")


def main():
    log(f"📂 工作目录: {BASE_DIR}")
    log(f"🏷️ 当前地区: {REGION}")
    log(f"📜 执行脚本序列: {', '.join(SCRIPTS)}\n")

    prev_step = None
    for script_name in SCRIPTS:
        script_path = BASE_DIR / script_name

        if not script_path.exists():
            log(f"⚠️ 找不到脚本：{script_name}，跳过。\n")
            continue

        # 执行脚本
        run_script(script_path)

        # 若上一步存在且当前为修改类脚本，则调用一致性检测
        if prev_step:
            run_consistency_check(prev_step, script_name.split("_")[0])

        prev_step = script_name.split("_")[0]

    log("🎯 全部脚本执行完毕。")


if __name__ == "__main__":
    main()
