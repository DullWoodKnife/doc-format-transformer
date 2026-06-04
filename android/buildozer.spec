[app]

title = DocConverter
package.name = docconverter
package.domain = com.docconverter

# 源码入口
source.dir = .
mainfile = main.py

# 版本
version = 0.1.0

# 依赖 - kivy 不指定版本，使用 kivy recipe 编译
requirements = python3,kivy,markitdown[all],beautifulsoup4,mammoth,pdfminer.six,pdfplumber,fpdf2,python-docx,ebooklib==0.18,chardet,charset-normalizer,defusedxml,markdownify,magika

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
# 使用 kivy 官方 stable tag v2024.01.21（避免 master 分支的 Python 3.14.2）
p4a.url = https://github.com/kivy/python-for-android.git
p4a.branch = v2024.01.21

log_level = 2