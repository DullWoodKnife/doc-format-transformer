# DocConverter Android

基于 Kivy + Buildozer 的离线文档转换器 APK。

## 功能

- 本地离线转换：PDF / DOCX / PPTX / XLSX / TXT / EPUB / HTML / MD
- 转换流程：任意格式 → Markdown → 目标格式
- 纯 Python 实现，无 pandoc 依赖
- 支持批量转换

## 技术栈

- **UI**: Kivy 2.x
- **核心**: markitdown（微软开源，纯 Python）
- **输出**: fpdf2（PDF）、python-docx（DOCX）、ebooklib（EPUB）
- **打包**: Buildozer → APK

## 依赖说明

| 库 | 用途 |
|----|------|
| markitdown | PDF/DOCX/HTML → Markdown |
| fpdf2 | Markdown → PDF |
| python-docx | Markdown → DOCX |
| ebooklib | Markdown → EPUB |

## 构建（本地 Linux）

```bash
# 安装系统依赖
sudo apt install -y python3-dev python3-pip git cmake unzip openjdk-17-jdk

# 安装 Python 依赖
pip install buildozer kivy

# 构建 debug APK
cd doc_converter_android
buildozer android debug

# APK 输出位置
# .buildozer/android/platform/build-*/bin/*.apk
```

## 构建（WSL2）

同本地 Linux，WSL2 支持良好。

## 文件结构

```
doc_converter_android/
├── main.py              # Kivy 应用入口
├── buildozer.spec       # Buildozer 构建配置
└── src/
    └── converter_android.py   # 核心转换模块
```

## 已知限制

- 不支持图片/音频 OCR（markitdown 的 LLM 功能在 Android 上不可用）
- PDF 输出为纯文本，不保留原始排版
- APK 包体积约 30-50MB（含 Python 运行时）
