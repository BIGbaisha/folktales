import re
import os

# ========== 硬编码输入输出路径 ==========
INPUT_MD_FILE = r"I:\obsidian\重庆市医疗净化工程及高校科研院所实验室工程2025年调研报告（完整版）-f8ae8ddf55.md"  # 输入的 Markdown 文件路径
OUTPUT_MD_FILE = "I:\obsidian\重庆市医疗净化工程及高校科研院所实验室工程2025年调研报告（完整版）.md"  # 输出的 Markdown 文件路径
# =====================================

# 关键词列表
KEYWORDS = ['会议纪要', '调研纪要']


def split_into_sentences(text):
    """粗略按中文句号、英文句号、问号、感叹号切分句子"""
    return re.split(r'([。！？.?!])', text)


def find_last_period_before_keyword(paragraph, keyword_pos):
    """找到关键词之前最近的一个句号位置"""
    last_period = -1
    for match in re.finditer(r'[。.]', paragraph[:keyword_pos]):
        last_period = match.end()  # 句号后的位置
    return last_period if last_period != -1 else 0  # 若无句号，则从头开始


def process_paragraph(paragraph):
    """处理一个段落：查找关键词并包裹对应句子"""
    result_parts = []
    processed_until = 0

    while True:
        # 找到下一个关键词
        keyword_match = None
        for kw in KEYWORDS:
            match = re.search(re.escape(kw), paragraph[processed_until:])
            if match:
                keyword_match = match
                break
        if not keyword_match:
            break  # 没有更多关键词

        start_offset = processed_until
        kw_start_in_para = start_offset + keyword_match.start()

        # 找到前一个句号的位置（作为当前句子的起始）
        sentence_start = find_last_period_before_keyword(paragraph, kw_start_in_para)
        sentence_start = max(sentence_start, processed_until)  # 避免回退

        # 找到当前句子的结尾（下一个句号或段落结尾）
        end_match = re.search(r'[。！？.?!]', paragraph[kw_start_in_para:])
        if end_match:
            sentence_end = kw_start_in_para + end_match.end()
        else:
            sentence_end = len(paragraph)

        # 提取要包裹的句子文本
        quoted_text = paragraph[sentence_start:sentence_end].strip()

        # 添加前面未处理的内容
        before_text = paragraph[processed_until:sentence_start]
        result_parts.append(before_text)

        # 添加围栏包裹的内容
        result_parts.append(f"\n\n```text\n{quoted_text}\n```\n\n")

        # 更新已处理位置
        processed_until = sentence_end

    # 添加剩余部分
    result_parts.append(paragraph[processed_until:])
    return ''.join(result_parts)


def main():
    # 检查输入文件是否存在
    if not os.path.exists(INPUT_MD_FILE):
        print(f"❌ 错误：输入文件不存在：{INPUT_MD_FILE}")
        return

    with open(INPUT_MD_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # 分段处理（以空行分隔为段落）
    paragraphs = re.split(r'(\n\s*\n)', content)  # 保留分隔符
    output_parts = []

    for para in paragraphs:
        if re.match(r'\s*\n\s*', para):  # 空行/分段符
            output_parts.append(para)
        else:
            processed_para = process_paragraph(para)
            output_parts.append(processed_para)

    final_output = ''.join(output_parts)

    # 写入输出文件
    with open(OUTPUT_MD_FILE, 'w', encoding='utf-8') as f:
        f.write(final_output)

    print(f"✅ 处理完成！已保存至：{OUTPUT_MD_FILE}")


if __name__ == "__main__":
    main()
# 创建时间: 2025/10/13 11:33
