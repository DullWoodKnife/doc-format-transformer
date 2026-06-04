[app]

title = DocConverter
package.name = docconverter
package.domain = com.docconverter

# 源码入口
source.dir = .
mainfile = main.py

# 版本
version = 0.1.0

# 依赖 - 纯 Python 库（指定兼容版本）
requirements = python3,kivy==2.2.0,markitdown[all],beautifulsoup4,mammoth,pdfminer.six,pdfplumber,fpdf2,python-docx,ebooklib==0.18,chardet,charset-normalizer,defusedxml,markdownify,magika

# Android 配置
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.api = 34
android.minapi = 24
android.archs = arm64-v8a,armeabi-v7a
android.ndk_version = 28c
android.sdk_version = 34
android.build_tools = 34.0.0

# 构建模式：debug 不需要签名
mode = debug

[buildozer]

log_level = 2