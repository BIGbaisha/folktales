# Chinese Folk Tales Cleaning Pipeline v2025.10

## 🧭 目的
本流水线用于将 OCR 扫描的《中国民间传统故事》PDF 转换的 Markdown 文本进行系统化清洗，
为后续关系数据库、向量数据库及数字人文研究提供标准化文本基础。

## 📁 目录结构
```
Chinese_FolkTales_Cleaning_Pipeline_v2025.10/
├─ README.md
├─ input/
├─ output/
├─ logs/
└─ scripts/
```

## ⚙️ 执行顺序
5.1 → 5.2 → 6.1 → 6.2 → 6.3 → 6.4 → 6.5 → 6.6 → 6.7 → 6.8 → 7.1 → 7.2 → 7.3

## 🧱 脚本说明
- 5.x 系列：标题与编号结构清理
- 6.x 系列：正文清洗、符号规范化与结构优化
- 7.x 系列：一致性检测与清洗日志
