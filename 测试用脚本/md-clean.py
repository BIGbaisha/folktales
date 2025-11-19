import re

# 中文编号列表（你要更多我可以继续扩展）
nums = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十","十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十"]

def add_number_to_lines(input_path: str, output_path: str):
    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    result = []
    index = 0  # 当前编号序号（从 0 开始，对应 "一"）

    for line in lines:
        stripped = line.lstrip()
        # 判断是否为 # 你说：
        if re.match(r"^#\s*你说：", stripped):
            num = nums[index]
            new_line = re.sub(r"^#\s*", f"# {num}、", stripped)
            result.append(new_line + ("\n" if not new_line.endswith("\n") else ""))
            index += 1
            continue

        # 判断是否为 # ChatGPT 说：
        if re.match(r"^#\s*ChatGPT 说：", stripped):
            num = nums[index-1] if index > 0 else nums[0]
            new_line = re.sub(r"^#\s*", f"# {num}、", stripped)
            result.append(new_line + ("\n" if not new_line.endswith("\n") else ""))
            continue

        # 非目标行保持不动
        result.append(line)

    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(result)

    print("处理完成！结果保存在:", output_path)


if __name__ == "__main__":
    input_md = r"I:\中国民间传统故事\哲学对话_cleaned.md"
    output_md = r"I:\中国民间传统故事\哲学对话_cleaned_1.md"
    add_number_to_lines(input_md, output_md)



