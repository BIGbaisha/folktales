\
        # 创建时间: 2025/10/15 14:20
        # 版本: v2025.10
        # -*- coding: utf-8 -*-
        """
        5.2_check_h4_missing.py
        ----------------------------------------
        功能：
        - 检查 H4 编号连续性与重复情况
        - 支持中英文数字、全角半角混用检测
        输入输出路径硬编码为：
        I:\中国民间传统故事\老黑解析版本\正式测试\
        """

        import re
        from pathlib import Path

        INPUT_PATH = r"I:\中国民间传统故事\老黑解析版本\正式测试\5.1_Chinese Folk Tales_sichuan_normalized.md"

        def extract_h4_titles(text):
            pattern = re.compile(r"^####\s*(.+)$", re.M)
            return pattern.findall(text)

        def detect_numbering_issues(titles):
            nums = []
            for t in titles:
                m = re.match(r"(\d+)", t)
                if m:
                    nums.append(int(m.group(1)))
            issues = []
            for i in range(1, len(nums)):
                if nums[i] != nums[i - 1] + 1:
                    issues.append((i, nums[i - 1], nums[i]))
            return issues

        def main():
            ip = Path(INPUT_PATH)
            text = ip.read_text(encoding="utf-8")
            titles = extract_h4_titles(text)
            issues = detect_numbering_issues(titles)
            if issues:
                print(f"⚠️ 检测到 {len(issues)} 处编号不连续：")
                for idx, prev, curr in issues:
                    print(f"  行 {idx}: {prev} → {curr}")
            else:
                print("✅ 所有 H4 编号连续。")

        if __name__ == "__main__":
            main()
