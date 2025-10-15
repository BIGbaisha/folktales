# 创建时间: 2025/10/15 14:20
# 版本: v2025.10
# -*- coding: utf-8 -*-
"""
run_pipeline.py
--------------------------------------------------
功能：
自动顺序执行所有 6.x 清洗脚本。
每执行一个脚本后自动调用 4_text_consistency_check.py，
进行前后差异检测，并记录运行日志。

新增部分：运行日志系统
- 自动创建 pipeline_run_log.txt
- 记录每个步骤执行状态、耗时、检测结果
"""

import subprocess
import time
from datetime import datetime
from pathlib import Path

# === 硬编码路径 ===
BASE_DIR = Path(r"I:\中国民间传统故事\老黑解析版本\正式测试")
LOG_FILE = BASE_DIR / "pipeline_run_log.txt"

# === 执行顺序 ===
SCRIPTS = [
    "6.2_regex_clean_enhanced.py",
    "6.3_H3marks_mathplaceholder_clean.py",
    "6.4_blanks_digits_check.py",
    "6.5_detect_remove_narrator_blocks.py",
    "6.6_links_delete_enhanced.py",
    "6.7_add_location_block.py",
    "6.8_fix_abnormal_linebreaks_enhanced.py"
]

# 一致性检测脚本
CHECK_SCRIPT = "4_text_consistency_check.py"


def log_message(message: str):
    """写入日志"""
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    entry = f"{timestamp} {message}"
    print(entry)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry + "\n")


def run_step(script_name, input_prev, output_new):
    """执行清洗脚本 + 一致性检测 + 日志记录"""
    script_path = BASE_DIR / script_name
    start_time = time.time()

    if not script_path.exists():
        log_message(f"⚠️ 未找到脚本：{script_name}，跳过。")
        return output_new

    log_message(f"▶️ 开始执行脚本：{script_name}")
    result = subprocess.run(["python", str(script_path)], capture_output=True, text=True)

    elapsed = time.time() - start_time
    if result.returncode == 0:
        log_message(f"✅ 脚本 {script_name} 执行完成，用时 {elapsed:.2f}s")
    else:
        log_message(f"❌ 脚本 {script_name} 执行失败 ({elapsed:.2f}s)\n{result.stderr}")

    # 调用一致性检测
    check_path = BASE_DIR / CHECK_SCRIPT
    if check_path.exists():
        log_message(f"🔍 进行一致性检测：{input_prev.name} → {output_new.name}")
        subprocess.run([
            "python", str(check_path),
            "--input_old", str(input_prev),
            "--input_new", str(output_new)
        ], check=False)
    else:
        log_message("⚠️ 未找到一致性检测脚本（4_text_consistency_check.py），跳过。")

    log_message(f"📄 生成输出文件：{output_new.name}\n")
    return output_new


def main():
    log_message("=== 🧩 启动清洗流水线 (run_pipeline.py) ===")

    current_input = BASE_DIR / "5.2_Chinese Folk Tales_sichuan.md"

    for script_name in SCRIPTS:
        step_no = script_name.split("_")[0]
        output_new = BASE_DIR / f"{step_no}_Chinese Folk Tales_sichuan_cleaned.md"
        current_input = run_step(script_name, current_input, output_new)

    log_message("✅ 所有清洗及一致性检测完成。请运行 7.1_post_clean_quality_check_enhanced.py 进行终检。")
    log_message("=== 🧾 流水线执行完毕 ===\n")


if __name__ == "__main__":
    main()
# 创建时间: 2025/10/15 16:03
