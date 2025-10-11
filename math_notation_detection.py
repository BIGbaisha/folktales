import re

def detect_math_notation_in_md(file_path):
    # Read the Markdown file content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regular expression to detect math notation wrapped in $...$
    math_pattern = r'\$.*?\$'

    # Find all math expressions in the text
    math_expressions = re.findall(math_pattern, content)

    # Return or print the math expressions found
    return math_expressions

# Example usage
file_path = r"D:\pythonprojects\folktales\中国民间故事集成 四川卷（上册） (《中国民间故事集成》全国编辑委员会,《中国民间故事集成·四川卷》编辑委员会) (Z-Library)_Part1_MinerU__20250903051058.md"
math_expressions = detect_math_notation_in_md(file_path)

# Print all the math expressions found
for idx, math_expr in enumerate(math_expressions, 1):
    print(f"Math Expression {idx}: {math_expr}")
# 创建时间: 2025/10/9 11:20
