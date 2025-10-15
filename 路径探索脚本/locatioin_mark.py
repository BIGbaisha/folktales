import re
import os

# ===== 硬编码输入 =====
INPUT_FILE = r"I:\中国民间传统故事\老黑解析版本\Chinese Folk Tales_sichuan_a.content.classified.md"
base, ext = os.path.splitext(INPUT_FILE)
OUTPUT_FILE = f"{base}.location_mark.md"  # 与输入同目录输出

# 四级编号标题：#### 002. 标题
re_heading = re.compile(r'^(####)\s+(\d+)\.\s*(.+?)\s*$', re.UNICODE)

# 括号地名行（半/全角）：(重庆市) / （重庆市）
re_location_paren = re.compile(r'^\s*[（(]\s*([^\s()（）]+?)\s*[)）]\s*$', re.UNICODE)

# 目标格式（已规范化的可视化行）：> 地点：重庆市（或空）
re_location_line = re.compile(r'^\s*>\s*地点[:：]\s*(.*)\s*$', re.UNICODE)


def transform(md: str) -> str:
    lines = md.splitlines()
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re_heading.match(line)

        if not m:
            out.append(line)
            i += 1
            continue

        # 命中标题
        out.append(line)
        j = i + 1

        # 允许穿透一行空行（常见排版）
        empty_buf = []
        if j < len(lines) and lines[j].strip() == "":
            empty_buf.append(lines[j])
            j += 1

        # 如果下一行已是“> 地点：xxx”，幂等：原样保留
        if j < len(lines):
            mm = re_location_line.match(lines[j])
            if mm:
                out.extend(empty_buf)
                out.append(lines[j])
                i = j + 1
                continue

        # 如果下一行是括号地名 → 转换为“> 地点：xxx”
        wrote = False
        if j < len(lines):
            lm = re_location_paren.match(lines[j])
            if lm:
                location = lm.group(1).strip()
                out.append("> 地点：" + location)
                out.append("")  # 保持标题与正文之间空一行
                i = j + 1
                wrote = True

        # 否则插入空占位
        if not wrote:
            out.append("> 地点：")
            if empty_buf:
                out.append("")  # 若原有空行，则保留一行
            i += 1

    return "\n".join(out)


if __name__ == "__main__":
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    result = transform(content)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(result)

    print(f"处理完成！已生成：{OUTPUT_FILE}")
