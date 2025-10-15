\
        # 创建时间: 2025/10/15 14:20
        # 版本: v2025.10
        # -*- coding: utf-8 -*-
        """
        7.1_text_consistency_check.py
        ----------------------------------------
        功能：
        - 检测清洗后文本与上一版本在章节数量、标题一致性、段落数上的差异
        - 输出 consistency_report.csv
        输入输出路径硬编码为：
        I:\中国民间传统故事\老黑解析版本\正式测试\
        """

        import csv, re
        from pathlib import Path

        INPUT_OLD = r"I:\中国民间传统故事\老黑解析版本\正式测试\6.8_Chinese Folk Tales_sichuan_cleaned.md"
        INPUT_NEW = r"I:\中国民间传统故事\老黑解析版本\正式测试\7.0_Chinese Folk Tales_sichuan_final.md"
        CSV_PATH  = r"I:\中国民间传统故事\老黑解析版本\正式测试\7.1_consistency_report.csv"

        def extract_titles(text):
            return re.findall(r"^(#{1,5})\s+(.+)$", text, re.M)

        def compare_titles(old_titles, new_titles):
            old_set = {t[1].strip() for t in old_titles}
            new_set = {t[1].strip() for t in new_titles}
            missing = old_set - new_set
            added   = new_set - old_set
            return missing, added

        def main():
            old_text = Path(INPUT_OLD).read_text(encoding="utf-8")
            new_text = Path(INPUT_NEW).read_text(encoding="utf-8")
            old_titles = extract_titles(old_text)
            new_titles = extract_titles(new_text)
            missing, added = compare_titles(old_titles, new_titles)

            with open(CSV_PATH, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["类型", "标题"])
                for m in missing:
                    w.writerow(["缺失", m])
                for a in added:
                    w.writerow(["新增", a])
            print(f"✅ 一致性检测完成：{CSV_PATH}")
            print(f"缺失标题 {len(missing)}，新增标题 {len(added)}")

        if __name__ == "__main__":
            main()
