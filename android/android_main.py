"""
doc_converter Android App - Kivy UI
万能文档转换器 Android 版
"""

import sys
import os
import threading
import time
import re
from pathlib import Path
from datetime import datetime

# 添加 src 目录到 path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.spinner import Spinner
from kivy.core.text import TextBase
from kivy.utils import platform
from kivy.clock import Clock

# 全局进度回调
_progress_callback = None

def set_progress(cb):
    global _progress_callback
    _progress_callback = cb

def progress(report):
    if _progress_callback:
        _progress_callback(report)


# ─── 格式选项 ────────────────────────────────────────────────────────────────

INPUT_FORMATS = ["pdf", "docx", "pptx", "xlsx", "txt", "epub", "html", "md"]
OUTPUT_FORMATS = ["md", "txt", "docx", "pdf", "epub", "html"]


# ─── 主界面 ────────────────────────────────────────────────────────────────────

class ConverterUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = 16
        self.spacing = 12
        self._build_ui()

    def _build_ui(self):
        # 标题
        self.add_widget(Label(
            text="📄 万能文档转换器",
            font_size="20sp",
            size_hint_y=None,
            height=50,
            color=(0.2, 0.6, 1.0, 1),
        ))

        # 输入文件选择区
        file_box = BoxLayout(size_hint_y=None, height=80, spacing=8)
        self.file_label = Label(
            text="未选择文件",
            halign="left",
            valign="middle",
            text_size=(self.width - 180, 80),
            color=(0.8, 0.8, 0.8, 1),
        )
        self.file_label.bind(size=lambda *x: setattr(
            self.file_label, 'text_size',
            (self.file_label.width, self.file_label.height)
        ))
        file_box.add_widget(self.file_label)

        select_btn = Button(
            text="选择文件",
            size_hint_x=None,
            width=130,
            on_press=self._select_file,
        )
        file_box.add_widget(select_btn)
        self.add_widget(file_box)

        # 输出格式选择
        format_box = BoxLayout(size_hint_y=None, height=50, spacing=8)
        format_box.add_widget(Label(text="输出格式:", size_hint_x=None, width=90))

        self.format_spinner = Spinner(
            text="md",
            values=[f for f in OUTPUT_FORMATS],
            size_hint_x=None,
            width=120,
        )
        format_box.add_widget(self.format_spinner)
        format_box.add_widget(Label(text=""))  # spacer
        self.add_widget(format_box)

        # 进度条
        self.progress_bar = ProgressBar(
            max=100,
            value=0,
            size_hint_y=None,
            height=8,
        )
        self.add_widget(self.progress_bar)

        # 状态标签
        self.status_label = Label(
            text="",
            font_size="13sp",
            size_hint_y=None,
            height=30,
            color=(0.6, 0.9, 0.6, 1),
        )
        self.add_widget(self.status_label)

        # 日志区
        self.log_input = TextInput(
            readonly=True,
            multiline=True,
            font_size="11sp",
            size_hint_y=1.0,
            background_color=(0.15, 0.15, 0.2, 1),
            foreground_color=(0.8, 0.8, 0.8, 1),
        )
        self.add_widget(self.log_input)

        # 转换按钮
        self.convert_btn = Button(
            text="开始转换",
            size_hint_y=None,
            height=56,
            on_press=self._on_convert,
            background_color=(0.2, 0.6, 1.0, 1),
        )
        self.add_widget(self.convert_btn)

        # 成员变量
        self.selected_file = None

    def _select_file(self, *args):
        # 动态导入避免在非 Android 也加载
        try:
            from plyer import filechooser
            path = filechooser.open_file(
                title="选择文档",
                filters=[("文档文件", [f"*.{ext}" for ext in INPUT_FORMATS])],
            )
            if path:
                self.selected_file = path[0]
                self.file_label.text = os.path.basename(self.selected_file)
                self.file_label.color = (1, 1, 1, 1)
        except Exception as e:
            # 兜底：直接让用户输入路径（调试用）
            self.log(f"⚠ 文件选择器不可用，请手动输入路径")

    def _on_convert(self, *args):
        if not self.selected_file:
            self.log("⚠ 请先选择文件")
            return

        if not os.path.exists(self.selected_file):
            self.log(f"❌ 文件不存在: {self.selected_file}")
            return

        target_fmt = self.format_spinner.text
        self.convert_btn.disabled = True
        self.convert_btn.text = "转换中..."
        self.progress_bar.value = 0

        # 后台线程执行转换
        thread = threading.Thread(target=self._convert_async, args=(target_fmt,))
        thread.daemon = True
        thread.start()

    def _convert_async(self, target_fmt):
        try:
            from converter_android import convert as do_convert

            def progress_callback(pct, msg):
                Clock.add_callback(self._update_progress, pct, msg)

            set_progress(progress_callback)

            progress(10, "正在读取文件...")
            input_path = self.selected_file
            output_dir = os.path.dirname(input_path) or "/storage/emulated/0/Download"
            output_name = Path(input_path).stem + f".{target_fmt}"
            output_path = os.path.join(output_dir, output_name)

            progress(30, "正在转换...")
            result = do_convert(input_path, output_path, target_fmt)

            progress(90, "完成!")
            Clock.add_callback(self._update_finish, result)
        except Exception as e:
            import traceback
            Clock.add_callback(self._update_error, str(e), traceback.format_exc())

    def _update_progress(self, pct, msg):
        self.progress_bar.value = pct
        self.status_label.text = msg
        self.log(f"  {msg}")

    def _update_finish(self, result):
        self.progress_bar.value = 100
        self.status_label.text = f"✅ 转换完成"
        self.log(f"✅ 输出: {result}")
        self.convert_btn.disabled = False
        self.convert_btn.text = "开始转换"

    def _update_error(self, err, tb):
        self.progress_bar.value = 0
        self.status_label.text = "❌ 转换失败"
        self.log(f"❌ 错误: {err}\n{tb}")
        self.convert_btn.disabled = False
        self.convert_btn.text = "开始转换"

    def log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_input.text += f"[{ts}] {msg}\n"
        self.log_input.cursor = self.log_input.get_cursor_from_index(len(self.log_input.text))


class DocConverterApp(App):
    def build(self):
        return ConverterUI()


# ─── 入口点（Buildozer 需要） ─────────────────────────────────────────────────

if __name__ == "__main__":
    DocConverterApp().run()
