# -*- coding: utf-8 -*-
"""
从 Markdown 抽取 H2(##) 与 H3(###) 标题，生成 CATEGORY_MAP 并直接 print。
- 保留预置映射；未知标题自动转为拼音下划线 code（无 pypinyin 时做安全降级）。
- 去重，按文档出现顺序输出；分成“一级/二级举例”两组打印。
"""

import re
import os
import unicodedata
import hashlib

# ======= 配置：你的输入 Markdown 文件路径 =======
INPUT_MD = r"I:\中国民间传统故事\老黑解析版本\v-Chinese Folk Tales_sichuan_shang.text.md"

# ======= 预置映射（你给的表，优先级最高） =======
PRESET = {
    # 一级
    "神话": "shenhua",
    "传说": "chuanshuo",
    "故事": "gushi",
    # 二级举例（可持续补充）
    "开天辟地神话": "kaitianpidishenhua",
    "自然天象神话": "ziran_tianxiang",
    "动物植物神话": "dongwu_zhiwu",
}

# ======= 可选：常见词的小字典（无 pypinyin 时的补完）=======
SMALL_CN_DICT = {
    # 常见大类
    "神话": "shenhua", "传说": "chuanshuo", "故事": "gushi",
    # 常见子类（示例）
    "开天辟地神话": "kaitianpidishenhua",
    "自然天象神话": "ziran_tianxiang",
    "动物植物神话": "dongwu_zhiwu",
    "英雄神话": "yingxiong_shenhua",
    "创世神话": "chuangshi_shenhua",
    "洪水神话": "hongshui_shenhua",
    "人生起源神话": "rensheng_qiyuan_shenhua",
    "地方传说": "difang_chuanshuo",
}

# ======= 工具：标题 → code 生成 =======
def have_pypinyin():
    try:
        import pypinyin  # type: ignore
        return True
    except Exception:
        return False

def to_pinyin_code(s: str) -> str:
    """将中文标题转为拼音下划线 code；无 pypinyin 时做降级保证可用。"""
    s = s.strip()
    # 1) 预置小词典
    if s in SMALL_CN_DICT:
        return SMALL_CN_DICT[s]

    # 2) pypinyin 路径（更优）
    try:
        from pypinyin import lazy_pinyin  # type: ignore
        pys = lazy_pinyin(s)
        joined = "".join(pys)
        code = _slug_ascii(joined)
        if code:
            return code
    except Exception:
        pass

    # 3) 降级：保留中文 → 用 unicode 编码片段兜底，确保不为空
    #   （同时把汉字之间用 _ 连接，尽量可读）
    # 3.1 把非字母数字用空格替换
    s_norm = unicodedata.normalize("NFKC", s)
    # 尝试取其中的 ASCII（如果有）
    ascii_part = _slug_ascii(s_norm)
    if ascii_part:
        return ascii_part
    # 3.2 全中文时：用每个字符的 codepoint 生成一个短码
    hex_parts = [format(ord(ch), "x") for ch in s_norm]
    return "x_" + "_".join(hex_parts)

def _slug_ascii(s: str) -> str:
    """安全 slug 化（仅保留 a-z0-9_；把分隔替换为下划线；压缩多余下划线）。"""
    s = unicodedata.normalize("NFKC", s).lower()
    s = s.replace("—", "-").replace("–", "-")
    # 替换分隔符为空格，后续统一转下划线
    for ch in ["-", "·", "／", "/", " ", "　", "・", "·"]:
        s = s.replace(ch, " ")
    # 只保留字母数字和空格
    buf = []
    for ch in s:
        if "a" <= ch <= "z" or "0" <= ch <= "9" or ch == " ":
            buf.append(ch)
        else:
            # 其它字符丢弃（中文会被丢掉）
            buf.append(" ")
    t = "".join(buf)
    # 连续空格 → 单下划线
    t = re.sub(r"\s+", "_", t).strip("_")
    # 连续下划线压缩
    t = re.sub(r"_+", "_", t)
    return t

# ======= 抽取 H2/H3 标题 =======
H_RE = re.compile(r"^(#{2,3})\s+(.+?)\s*$", re.MULTILINE)

def extract_h2_h3(md_text: str):
    levels = []   # [(level:int, title:str)]
    seen = set()
    for m in H_RE.finditer(md_text):
        level = len(m.group(1))
        title = m.group(2).strip()
        key = (level, title)
        if key in seen:
            continue
        seen.add(key)
        levels.append((level, title))
    # 按出现顺序返回
    return levels

# ======= 主逻辑：生成并打印 CATEGORY_MAP =======
def main():
    if not os.path.exists(INPUT_MD):
        raise FileNotFoundError(f"找不到文件：{INPUT_MD}")
    with open(INPUT_MD, "r", encoding="utf-8") as f:
        md = f.read()

    headers = extract_h2_h3(md)

    # 先分组
    lvl2 = []
    lvl3 = []
    for level, title in headers:
        if level == 2:
            lvl2.append(title)
        elif level == 3:
            lvl3.append(title)

    # 生成映射：预置优先
    mapping = {}
    order = []  # 记录插入顺序用于打印

    def ensure(title: str):
        if title in mapping:
            return
        if title in PRESET:
            mapping[title] = PRESET[title]
        else:
            mapping[title] = to_pinyin_code(title)
        order.append(title)

    # 先确保预置里出现过的键按顺序输出
    # （即使文档里没出现，也可以保留；如需仅输出文档出现的，可注释这段）
    for k in ["神话", "传说", "故事", "开天辟地神话", "自然天象神话", "动物植物神话"]:
        if k in PRESET:
            mapping.setdefault(k, PRESET[k])
            if k not in order:
                order.append(k)

    # 文档实际抽取到的标题
    for t in lvl2 + lvl3:
        ensure(t)

    # 打印结果：贴合你给的格式
    print("CATEGORY_MAP = {")
    print("    # 一级")
    # 一级：按出现顺序，但只打印 H2；若预置中也包含，会被覆盖为预置值
    for t in order:
        if t in lvl2 or (t in PRESET and t in ["神话", "传说", "故事"]):
            print(f'    "{t}": "{mapping[t]}",')
    print("    # 二级举例（可持续补充）")
    for t in order:
        if t in lvl3 or (t in PRESET and t not in ["神话", "传说", "故事"]):
            print(f'    "{t}": "{mapping[t]}",')
    print("}")

if __name__ == "__main__":
    main()
