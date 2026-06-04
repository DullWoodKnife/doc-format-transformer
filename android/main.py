"""
Buildozer 入口点 - 桥接到 android_main.py
"""
import os
import sys

# 将 android_main.py 所在的目录加入 path
main_dir = os.path.dirname(os.path.abspath(__file__))
if main_dir not in sys.path:
    sys.path.insert(0, main_dir)

# 桥接到实际的 android_main 入口
from android_main import DocConverterApp

if __name__ == "__main__":
    DocConverterApp().run()