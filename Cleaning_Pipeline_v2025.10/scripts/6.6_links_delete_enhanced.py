\
        # 创建时间: 2025/10/15 14:20
        # 版本: v2025.10
        # -*- coding: utf-8 -*-
        """
        6.6_links_delete_enhanced.py
        ----------------------------------------
        功能：
        - 清除 Markdown 链接 + 空行规范化
        新增部分：
        - 检查标题层级跳跃
        - 检查连续标题无正文
        - 输出 structure_warnings.csv
        """

        import re, csv
        from pathlib import Path

        INPUT_PATH  = r"I:\中国民间传统故事\老黑解析版本\正式测试\6.5_Chinese Folk Tales_sichuan_cleaned.md"
        OUTPUT_PATH = r"I:\中国民间传统故事\老黑解析版本\正式测试\6.6_Chinese Folk Tales_sichuan_cleaned.md"
        WARN_CSV    = r"I:\中国民间传统故事\老黑解析版本\正式测试\6.6_structure_warnings.csv"

        RE_HEADING = re.compile(r"^(#{1,6})\s+.*$")
        RE_EMPTY = re.compile(r"^[\s\u200b\u200c\u200d\uFEFF]*$")
        RE_LINK_MD = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
        RE_LINK_ANGLE = re.compile(r"<(https?://[^>]+)>")
        RE_LINK_BARE = re.compile(r"https?://[^\s)\]]+")

        def remove_links(text):
            text = RE_LINK_MD.sub(r"\\1", text)
            text = RE_LINK_ANGLE.sub("", text)
            text = RE_LINK_BARE.sub("", text)
            return text

        # ===== 新增部分：结构检测 =====
        def detect_structure_issues(lines):
            issues, prev_h, prev_was_heading = [], None, False
            for i, line in enumerate(lines, start=1):
                m = RE_HEADING.match(line)
                if m:
                    level = len(m.group(1))
                    if prev_h and level - prev_h > 1:
                        issues.append((i, f"H{prev_h}->H{level}", line.strip()))
                    if prev_was_heading:
                        issues.append((i, "连续标题无正文", line.strip()))
                    prev_h, prev_was_heading = level, True
                elif not RE_EMPTY.match(line):
                    prev_was_heading = False
            return issues

        def export_warnings(issues):
            if not issues:
                print("✅ 未检测到结构异常。")
                return
            with open(WARN_CSV, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["行号", "问题", "内容"])
                for row in issues:
                    w.writerow(row)
            print(f"⚠️ 已检测到 {len(issues)} 条结构异常。")

        def main():
            text = Path(INPUT_PATH).read_text(encoding="utf-8")
            text = remove_links(text)
            lines = text.splitlines(True)
            issues = detect_structure_issues(lines)
            export_warnings(issues)
            Path(OUTPUT_PATH).write_text("".join(lines), encoding="utf-8")
            print(f"✅ 输出文件：{OUTPUT_PATH}")

        if __name__ == "__main__":
            main()
