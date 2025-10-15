\
        # 创建时间: 2025/10/15 14:20
        # 版本: v2025.10
        # -*- coding: utf-8 -*-
        """
        5.1_titles_normalize.py
        ----------------------------------------
        功能：
        - 重新建立标题层级（H1-H5）
        - 清除无效的 # 符号
        - 输出标题层级统计 CSV
        输入输出路径硬编码为：
        I:\中国民间传统故事\老黑解析版本\正式测试\
        """

        import re, csv
        from pathlib import Path

        INPUT_PATH  = r"I:\中国民间传统故事\老黑解析版本\正式测试\5_Chinese Folk Tales_sichuan.md"
        OUTPUT_PATH = r"I:\中国民间传统故事\老黑解析版本\正式测试\5.1_Chinese Folk Tales_sichuan_normalized.md"
        CSV_PATH    = r"I:\中国民间传统故事\老黑解析版本\正式测试\5.1_titles_hierarchy.csv"

        def normalize_titles(text):
            lines = text.splitlines()
            normalized = []
            for line in lines:
                if re.match(r"^#+\s+", line):
                    line = re.sub(r"\s+", " ", line.strip())
                normalized.append(line)
            return "\n".join(normalized)

        def extract_titles(text):
            titles = []
            for line in text.splitlines():
                if re.match(r"^#+\s+", line):
                    level = len(line.split()[0])
                    titles.append((level, line.strip()))
            return titles

        def export_titles(titles):
            with open(CSV_PATH, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["层级", "标题"])
                w.writerows(titles)
            print(f"✅ 标题层级统计已输出：{CSV_PATH}")

        def main():
            ip = Path(INPUT_PATH)
            text = ip.read_text(encoding="utf-8")
            normalized = normalize_titles(text)
            Path(OUTPUT_PATH).write_text(normalized, encoding="utf-8")
            print(f"✅ 已输出标准化标题文件：{OUTPUT_PATH}")
            titles = extract_titles(normalized)
            export_titles(titles)

        if __name__ == "__main__":
            main()
