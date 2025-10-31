# -*- coding: utf-8 -*-
"""
通用文本标准化模块（基础正则环境统一）
Version: v2025.11
功能：
- 全角 → 半角
- 清除零宽符与 BOM
- 换行符标准化
- 保证文件以换行结尾
"""
import re

def normalize_chinese_text(text: str) -> str:
    """统一中英文符号、空格、换行的标准化预处理"""
    fw2hw_map = {
        ord('＃'): ord('#'),
        ord('　'): ord(' '),
        **{ord(f): ord('0') + i for i, f in enumerate('０１２３４５６７８９')},
        **{ord(f): ord('A') + i for i, f in enumerate('ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ')},
        **{ord(f): ord('a') + i for i, f in enumerate('ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ')},
        ord('，'): ord(','),
        ord('。'): ord('.'),
        ord('；'): ord(';'),
        ord('：'): ord(':'),
        ord('！'): ord('!'),
        ord('？'): ord('?'),
        ord('（'): ord('('),
        ord('）'): ord(')'),
        ord('【'): ord('['),
        ord('】'): ord(']'),
        ord('“'): ord('"'),
        ord('”'): ord('"'),
        ord('‘'): ord("'"),
        ord('’'): ord("'"),
    }

    text = text.translate(fw2hw_map)
    text = re.sub(r'[\u200b\u200c\u200d\uFEFF]', '', text)  # 零宽字符
    text = text.replace('\r\n', '\n').replace('\r', '\n')    # 换行标准化
    if not text.endswith('\n'):
        text += '\n'
    return text
# 创建时间: 2025/10/31 9:33
