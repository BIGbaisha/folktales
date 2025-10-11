# 创建时间: 2025/10/9 10:12
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re, sys, unicodedata
from pathlib import Path
from typing import Iterable, List, Tuple

# ========== 硬编码路径 & 参数 ==========
INPUT_PATH  = Path(r"I:\中国民间传统故事\老黑解析版本\v-Chinese Folk Tales_sichuan_shang.text.yaml.md")
OUTPUT_PATH = Path(r"I:\中国民间传统故事\老黑解析版本\v-Chinese Folk Tales_sichuan_shang.text.yaml.regex.md")

ENCODING    = "utf-8"

# 每阶段打印的示例数（每文件）
PRINT_SAMPLES_PER_FILE = 5
# =====================================

CJK = r'\u4e00-\u9fff'

# ---------- 基础：围栏与行内代码保护 ----------
RE_FENCE = re.compile(r'^(\s*)(`{3,}|~{3,})')
def _flag_fences(lines: List[str]) -> List[Tuple[str, bool]]:
    out, in_block, fence_ch = [], False, None
    for ln in lines:
        m = RE_FENCE.match(ln)
        if m:
            token = m.group(2)[0]
            if not in_block:
                in_block, fence_ch = True, token
            else:
                if token == fence_ch:
                    in_block, fence_ch = False, None
            out.append((ln, True))
        else:
            out.append((ln, in_block))
    return out

def _split_inline_code(s: str) -> List[Tuple[str, bool]]:
    parts, buf, in_code = [], [], False
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == '`':
            if buf:
                parts.append((''.join(buf), in_code)); buf=[]
            in_code = not in_code
            parts.append(('`', True))
            i += 1; continue
        buf.append(ch); i += 1
    if buf: parts.append((''.join(buf), in_code))
    # 合并相邻同类
    out, cur, flag = [], [], None
    for seg, is_code in parts:
        if flag is None: flag, cur = is_code, [seg]
        elif is_code == flag: cur.append(seg)
        else: out.append((''.join(cur), flag)); flag, cur = is_code, [seg]
    if cur: out.append((''.join(cur), flag))
    return out

# ---------- Phase 1：标题末尾冒号删除 ----------
# 允许 # 后无空格；捕获原始间距与结尾 #####
RE_ATX_P1 = re.compile(r'^(\s{0,3})(#{1,6})([ \t]*)(.*?)([ \t]+(#+)[ \t]*)?$')

def phase1_delete_heading_trailing_colon(lines: List[str]) -> Tuple[List[str], List[Tuple[int, str, str]]]:
    changed = []
    out = []
    for idx, line in enumerate(lines, 1):
        m = RE_ATX_P1.match(line.rstrip("\n"))
        if not m:
            out.append(line); continue
        lead_ws, hashes, sep, content, closing, _ = m.groups()
        closing = closing or ""
        new_content = re.sub(r'[:：]\s*$', '', content)
        new_line = f"{lead_ws}{hashes}{sep}{new_content}{closing}\n"
        if new_line != line:
            changed.append((idx, line.rstrip("\n"), new_line.rstrip("\n")))
        out.append(new_line)
    return out, changed

# ---------- Phase 2：标题正则清洗（不动 Markdown 符号） ----------
RE_ATX_P2 = re.compile(r'^(\s{0,3})(#{1,6})([ \t]+)?(.*?)([ \t]+(#+)[ \t]*)?$')
CN_PUNCT = r'，。、；：！？（）【】《》「」『』”“‘’—…｛｝'

def _map_ascii_punct_to_fullwidth_safe(s: str) -> str:
    # 扩展半角标点转换范围
    s = re.sub(rf'(?<=[{CJK}]),', '，', s)
    s = re.sub(rf'(?<=[{CJK}])\.', '。', s)
    s = re.sub(rf'(?<=[{CJK}])\?', '？', s)
    s = re.sub(rf'(?<=[{CJK}])!', '！', s)
    s = re.sub(rf'(?<=[{CJK}])"', '”', s)
    s = re.sub(rf"(?<=[{CJK}])'", "’", s)
    s = re.sub(rf'(?<=[{CJK}])[:;]', '：', s)  # 新增：冒号与分号处理
    s = re.sub(rf'(?<=[{CJK}])\(', '（', s)  # 新增：括号处理
    s = re.sub(rf'(?<=[{CJK}])\)', '）', s)  # 新增：括号处理
    return s

def _clean_heading_text(s: str) -> str:
    # 破折号/省略号
    s = re.sub(r'[—–―−]+', '—', s)
    s = re.sub(r'…{2,}', '……', s)
    s = re.sub(r'\.{3,}', '…', s)
    s = _map_ascii_punct_to_fullwidth_safe(s)
    # 标题内冒号放宽（避开 ://；支持 右侧中文/行尾）
    s = re.sub(rf'(?<=[{CJK}])\s*:(?!//)\s*', '：', s)
    s = re.sub(rf'(?<=[0-9A-Za-z])\s*:\s*(?=[{CJK}])', '：', s)
    s = re.sub(rf'(?<=[{CJK}])\s*:\s*(?=[{CJK}])', '：', s)
    # 空格收敛 & CJK 间距
    s = re.sub(r'[ \t]+', ' ', s)
    s = re.sub(rf'(?<=[{CJK}])\s+(?=[{CJK}])', '', s)
    # 标点前/开引后
    s = re.sub(rf'\s+([{CN_PUNCT}])', r'\1', s)
    s = re.sub(rf'([“‘（《【「『])\s+', r'\1', s)
    # 标点后
    s = re.sub(r'([，、。；：！？…])\s+', r'\1', s)
    # 中西夹缝
    s = re.sub(rf'(?<=[A-Za-z0-9])\s+(?=[{CJK}])', '', s)
    s = re.sub(rf'(?<=[{CJK}])\s+(?=[A-Za-z0-9])', '', s)
    # 括号/书名号贴合
    s = re.sub(r'\s+（', '（', s); s = re.sub(r'）\s+', '）', s)
    s = re.sub(r'\s+《', '《', s); s = re.sub(r'》\s+', '》', s)
    return s.strip()

def phase2_clean_headings(lines: List[str]) -> Tuple[List[str], List[Tuple[int, str, str]]]:
    changed = []; out = []
    for idx, line in enumerate(lines, 1):
        m = RE_ATX_P2.match(line.rstrip("\n"))
        if not m:
            out.append(line); continue
        lead_ws, hashes, sep, content, closing, _ = m.groups()
        sep = sep or ""  # 保留原 # 后是否有空格
        closing = closing or ""
        # 行内代码保护
        segs = _split_inline_code(content)
        cleaned = ''.join(seg if is_code else _clean_heading_text(seg) for seg, is_code in segs)
        new_line = f"{lead_ws}{hashes}{sep}{cleaned}{closing}\n"
        if new_line != line:
            changed.append((idx, line.rstrip("\n"), new_line.rstrip("\n")))
        out.append(new_line)
    return out, changed

# ---------- Phase 3：正文清洗（保守，不动 Markdown 符号） ----------
RE_TABLE = re.compile(r'^\s*\|.*\|\s*$')
RE_HR    = re.compile(r'^\s{0,3}([-*_]\s*){3,}$')
RE_HEADING_ANY = re.compile(r'^\s{0,3}#{1,6}(\s+|$)')

def _clean_body_text(s: str) -> str:
    s = re.sub(r'[—–―−]+', '—', s)
    s = re.sub(r'…{2,}', '……', s)
    s = re.sub(r'\.{3,}', '…', s)
    s = _map_ascii_punct_to_fullwidth_safe(s)  # 不放宽冒号
    s = re.sub(r'[ \t]+', ' ', s)
    s = re.sub(rf'(?<=[{CJK}])\s+(?=[{CJK}])', '', s)
    s = re.sub(rf'\s+([{CN_PUNCT}])', r'\1', s)
    s = re.sub(rf'([“‘（《【「『])\s+', r'\1', s)
    s = re.sub(r'([，、。；：！？…])\s+', r'\1', s)
    s = re.sub(rf'(?<=[A-Za-z0-9])\s+(?=[{CJK}])', '', s)
    s = re.sub(rf'(?<=[{CJK}])\s+(?=[A-Za-z0-9])', '', s)
    return s

def phase3_clean_body(lines: List[str]) -> Tuple[List[str], List[Tuple[int, str, str]]]:
    changed = []; out = []
    flagged = _flag_fences(lines)
    for idx, (line, in_codeblock) in enumerate(flagged, 1):
        if in_codeblock or RE_TABLE.match(line) or RE_HR.match(line) or RE_HEADING_ANY.match(line):
            out.append(line); continue
        # 行内代码保护
        segs = _split_inline_code(line.rstrip("\n"))
        cleaned_line = ''.join(seg if is_code else _clean_body_text(seg) for seg, is_code in segs) + "\n"
        if cleaned_line != line:
            changed.append((idx, line.rstrip("\n"), cleaned_line.rstrip("\n")))
        out.append(cleaned_line)
    return out, changed

# ---------- I/O ----------
def iter_md_files(root: Path) -> Iterable[Path]:
    if root.is_file():
        yield root; return
    for p in root.rglob("*.md"):
        if p.is_file(): yield p

def run_pipeline_on_text(text: str) -> Tuple[str, dict, dict, dict]:
    # 统一换行与轻量规范化
    text = unicodedata.normalize('NFKC', text)
    lines = text.splitlines(True)

    # Phase 1
    p1_out, p1_changes = phase1_delete_heading_trailing_colon(lines)

    # Phase 2
    p2_out, p2_changes = phase2_clean_headings(p1_out)

    # Phase 3
    p3_out, p3_changes = phase3_clean_body(p2_out)

    return ''.join(p3_out), \
           {"count": len(p1_changes), "samples": p1_changes[:PRINT_SAMPLES_PER_FILE]}, \
           {"count": len(p2_changes), "samples": p2_changes[:PRINT_SAMPLES_PER_FILE]}, \
           {"count": len(p3_changes), "samples": p3_changes[:PRINT_SAMPLES_PER_FILE]}

def process_file(src: Path, dst_root: Path, src_root: Path | None = None):
    raw = src.read_text(encoding=ENCODING, errors="ignore")
    cleaned, p1, p2, p3 = run_pipeline_on_text(raw)
    # 输出
    if dst_root.suffix or dst_root.name.endswith('.md'):  # 如果路径带有扩展名（尤其是 .md），视为文件
        out_path = dst_root  # 输出文件路径
    else:
        # 如果是目录，使用输入文件名拼接输出路径
        rel = src.name if src_root is None or not src_root.is_dir() else src.relative_to(src_root)
        out_path = dst_root.joinpath(rel)
        out_path.parent.mkdir(parents=True, exist_ok=True)  # 确保父目录存在

    out_path.write_text(cleaned, encoding=ENCODING, newline="\n")

    # 打印统计
    print(f"\n== {src} ==")
    print(f"[Phase1] 删除标题尾冒号：{p1['count']} 处")
    for ln, before, after in p1["samples"]:
        print(f"  L{ln}: {before}  ->  {after}")
    print(f"[Phase2] 标题清洗（不动Markdown符号）：{p2['count']} 处")
    for ln, before, after in p2["samples"]:
        print(f"  L{ln}: {before}  ->  {after}")
    print(f"[Phase3] 正文清洗：{p3['count']} 行")
    for ln, before, after in p3["samples"]:
        print(f"  L{ln}: {before}  ->  {after}")

def main():
    src = INPUT_PATH
    dst = OUTPUT_PATH
    if not src.exists():
        print(f"[ERROR] 输入路径不存在: {src}", file=sys.stderr); sys.exit(2)

    if src.is_file():
        # 若 OUTPUT_PATH 是目录，写到该目录下同名文件；若是文件，写那一个文件
        if dst.is_dir():
            out_file = dst.joinpath(src.name)
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.touch(exist_ok=True)
            process_file(src, out_file, None)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            process_file(src, dst, None)
    else:
        # 目录镜像
        if dst.is_file():
            print("[ERROR] OUTPUT_PATH 指向文件，但 INPUT_PATH 是目录。请把 OUTPUT_PATH 设为目录。", file=sys.stderr)
            sys.exit(3)
        for fp in iter_md_files(src):
            process_file(fp, dst, src)

if __name__ == "__main__":
    main()
