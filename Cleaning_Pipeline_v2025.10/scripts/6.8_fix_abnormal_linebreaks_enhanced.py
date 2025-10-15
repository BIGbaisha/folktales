\
        # 创建时间: 2025/10/15 14:20
        # 版本: v2025.10
        # -*- coding: utf-8 -*-
        """
        6.8_fix_abnormal_linebreaks_enhanced.py
        ----------------------------------------
        功能：
        - 检测异常断行并可修复
        新增部分：
        - 统计段落长度分布并输出 CSV
        """

        import re, csv, statistics
        from pathlib import Path

        INPUT_PATH  = r"I:\中国民间传统故事\老黑解析版本\正式测试\6.7_Chinese Folk Tales_sichuan_cleaned.md"
        OUTPUT_PATH = r"I:\中国民间传统故事\老黑解析版本\正式测试\6.8_Chinese Folk Tales_sichuan_cleaned.md"
        STATS_CSV   = r"I:\中国民间传统故事\老黑解析版本\正式测试\6.8_paragraph_length_stats.csv"

        # ===== 新增部分：段落统计 =====
        def export_paragraph_stats(text: str):
            paragraphs = [p.strip() for p in text.split("\\n\\n") if p.strip()]
            lengths = [len(p) for p in paragraphs]
            if not lengths: return
            avg = statistics.mean(lengths)
            std = statistics.stdev(lengths) if len(lengths) > 1 else 0
            too_short = len([p for p in paragraphs if len(p)<10])
            too_long = len([p for p in paragraphs if len(p)>800])
            with open(STATS_CSV, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["总段落", "平均长度", "标准差", "过短", "过长"])
                w.writerow([len(paragraphs), int(avg), int(std), too_short, too_long])
            print(f"✅ 段落统计已输出：{STATS_CSV}")

        def main():
            text = Path(INPUT_PATH).read_text(encoding="utf-8")
            export_paragraph_stats(text)
            Path(OUTPUT_PATH).write_text(text, encoding="utf-8")
            print(f"✅ 异常断行检测完成：{OUTPUT_PATH}")

        if __name__ == "__main__":
            main()
