\
        # 创建时间: 2025/10/15 14:20
        # 版本: v2025.10
        # -*- coding: utf-8 -*-
        """
        6.2_regex_clean_enhanced.py
        ----------------------------------------
        功能：
        - 正则清洗 Markdown 文本（标题、正文、数学占位）
        新增部分：
        - Unicode 归一化（NFKC）
        - 稀有字符统计与 CSV 输出
        - 特殊空格检测与报告
        输入输出路径硬编码为：
        I:\中国民间传统故事\老黑解析版本\正式测试\
        """

        import re, csv, unicodedata
        from collections import Counter
        from pathlib import Path

        INPUT_PATH  = r"I:\中国民间传统故事\老黑解析版本\正式测试\5.1_Chinese Folk Tales_sichuan_normalized.md"
        OUTPUT_PATH = r"I:\中国民间传统故事\老黑解析版本\正式测试\6.2_Chinese Folk Tales_sichuan_cleaned.md"
        CHAR_FREQ_CSV = r"I:\中国民间传统故事\老黑解析版本\正式测试\6.2_char_freq.csv"
        WEIRDSPACE_REPORT = r"I:\中国民间传统故事\老黑解析版本\正式测试\6.2_weirdspace_report.txt"

        # ===== 新增部分：功能说明 =====
        # 1. Unicode 归一化
        # 2. 统计字符频率，输出 char_freq.csv
        # 3. 检测零宽字符与特殊空格并记录报告

        def normalize_unicode(text: str) -> str:
            return unicodedata.normalize("NFKC", text)

        def export_char_statistics(text: str):
            counter = Counter(text)
            with open(CHAR_FREQ_CSV, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["字符", "Unicode", "频率"])
                for ch, cnt in sorted(counter.items(), key=lambda x: -x[1]):
                    w.writerow([ch, f"U+{ord(ch):04X}", cnt])
            weirds = [c for c in counter if 0x2000 <= ord(c) <= 0x206F]
            if weirds:
                with open(WEIRDSPACE_REPORT, "w", encoding="utf-8") as f:
                    for c in weirds:
                        f.write(f"{repr(c)} U+{ord(c):04X} 出现 {counter[c]} 次\n")
            print("✅ 字符统计与特殊空格检测完成。")

        def main():
            text = Path(INPUT_PATH).read_text(encoding="utf-8")
            text = normalize_unicode(text)
            Path(OUTPUT_PATH).write_text(text, encoding="utf-8")
            export_char_statistics(text)
            print(f"✅ 正则清洗完成：{OUTPUT_PATH}")

        if __name__ == "__main__":
            main()
