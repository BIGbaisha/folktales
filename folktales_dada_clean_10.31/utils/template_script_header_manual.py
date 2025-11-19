# 创建时间: 2025/10/31 9:33
# -*- coding: utf-8 -*-
# ==========================================================
# 通用脚本头模板（人工复核版）
# Version: v2025.11
# ==========================================================
import os
from pathlib import Path
from datetime import datetime
from utils.text_normalizer import normalize_chinese_text

ENCODING = "utf-8"

def load_text(path: Path) -> str:
    """读取文件并执行 normalize_chinese_text()"""
    if not path.exists():
        raise FileNotFoundError(f"❌ 未找到输入文件: {path}")
    print(f"\n📂 读取文件: {path}")
    text = path.read_text(encoding=ENCODING, errors="ignore")
    text = normalize_chinese_text(text)
    print(f"✅ 已加载并标准化文本（长度 {len(text):,} 字符）")
    return text


def save_text(path: Path, text: str):
    """保存文本并自动创建目录"""
    os.makedirs(path.parent, exist_ok=True)
    path.write_text(text, encoding=ENCODING)
    print(f"💾 已输出文件: {path}")
    print(f"📏 文件长度: {len(text):,} 字符")


def log_stage(title: str):
    print(f"\n🚀 {title}\n{'-' * (len(title) + 6)}")


def log_info(msg: str):
    print(f"🟢 {msg}")


def log_warning(msg: str):
    print(f"⚠️ {msg}")


def log_summary(stage_name: str, in_path: Path, out_path: Path):
    print("\n" + "=" * 60)
    print(f"📘 阶段完成: {stage_name}")
    print(f"🕒 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 输入: {in_path}")
    print(f"📄 输出: {out_path}")
    print("=" * 60 + "\n")
