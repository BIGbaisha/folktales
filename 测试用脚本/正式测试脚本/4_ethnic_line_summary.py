# 创建时间: 2025/10/10 13:27
import os

def count_short_lines_endwith_zu(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f"\n=== 文件: {os.path.basename(file_path)} ===")
    total = 0
    serial = 0  # 命中行的连续编号（1,2,3,...）

    for i, line in enumerate(lines, start=1):
        raw = line.rstrip('\n')           # 去掉换行符
        if "讲述者" in raw:
            continue                      # 过滤包含“讲述者”的行

        total_len = len(raw)              # 含空格/符号
        if raw.rstrip().endswith("族") and total_len <= 10:
            serial += 1
            total += 1
            # 同时打印命中编号和原文件行号，便于追溯
            print(f"{serial:>3}. 行{i:>4}: {raw}")

    print(f"共 {total} 行符合条件。")


# 示例：替换为你的 Markdown 文件路径
if __name__ == "__main__":
    input_paths = [
        r"I:\中国民间传统故事\老黑解析版本\正式测试\Chinese Folk Tales_sichuan.md",
    ]
    for path in input_paths:
        if os.path.exists(path):
            count_short_lines_endwith_zu(path)
        else:
            print(f"⚠️ 文件不存在: {path}")
