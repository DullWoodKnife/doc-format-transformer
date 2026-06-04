[app]

title = DocConverter
package.name = docconverter
package.domain = com.docconverter

# 源码入口
source.dir = .
mainfile = main.py

# 版本
version = 0.1.0

# 依赖 - 纯 Python 库
requirements = python3,kivy,markitdown[all],beautifulsoup4,mammoth,pdfminer.six,pdfplumber,fpdf2,python-docx,ebooklib,chardet,charset-normalizer,defusedxml,markdownify,magika

# Android 配置
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.api = 24
android.minapi = 21
android.archs = arm64-v8a,armeabi-v7a

# 禁止访问网络（纯本地）
android.allow_network = False

# 完整 log（调试用）
log_level = 2

# 去除不必要的包减小体积
android.whitelist = 
android.blacklist =

# 构建模式
mode = release

[buildozer]

log_level = 2
