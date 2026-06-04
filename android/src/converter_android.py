"""
Android 版文档转换器 - 核心模块
移除 pandoc 依赖，改用纯 Python 库实现输出
支持: PDF/DOCX/TXT/EPUB/HTML → MD → PDF/DOCX/TXT/EPUB/HTML
"""

import sys
import os
import io
import re
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

# ─── 动态安装依赖（Android 环境） ──────────────────────────────────────────────

def _ensure_package(pkg, import_name=None, pip_extra=None):
    """确保包已安装，失败则尝试安装"""
    import_name = import_name or pkg.split("[")[0]
    try:
        __import__(import_name)
        return True
    except ImportError:
        pass
    try:
        import subprocess
        extra = f"[{pip_extra}]" if pip_extra else ""
        subprocess.run(
            [sys.executable, "-m", "pip", "install", f"{pkg}{extra}"],
            capture_output=True, timeout=120
        )
        __import__(import_name)
        return True
    except Exception:
        return False


# ─── 支持的文件扩展名 ─────────────────────────────────────────────────────────

INPUT_EXTS = {"pdf", "docx", "pptx", "xlsx", "txt", "epub", "html", "md"}
PANDOC_FORMATS = {"pdf", "docx", "epub", "txt", "html", "odt", "rtf", "md"}


# ─── 统计计数器 ────────────────────────────────────────────────────────────────

@dataclass
class Stats:
    total: int = 0
    success: int = 0
    failed: int = 0
    skipped: int = 0

    def print_summary(self):
        print(f"\n{'='*50}")
        print(f"📊 批处理统计")
        print(f"{'='*50}")
        print(f"  总数:    {self.total}")
        print(f"  成功:    {self.success} ✅")
        print(f"  失败:    {self.failed} ❌")
        print(f"  跳过:    {self.skipped} ⏭️")
        if self.failed > 0:
            print(f"\n  失败率:  {self.failed/self.total*100:.1f}%")
        print(f"{'='*50}")


# ─── MarkItDown 单例 ──────────────────────────────────────────────────────────

_md_converter = None

def _get_converter():
    global _md_converter
    if _md_converter is None:
        # 延迟导入，失败则尝试安装
        try:
            from markitdown import MarkItDown
            _md_converter = MarkItDown()
        except ImportError:
            _ensure_package("markitdown[all]")
            from markitdown import MarkItDown
            _md_converter = MarkItDown()
    return _md_converter


# ═══════════════════════════════════════════════════════════════════════
# 第一阶段：任意格式 → Markdown
# ═══════════════════════════════════════════════════════════════════════

def to_markdown(input_path: str, output_md: str = None) -> str:
    """
    使用 markitdown 将任意文档转为标准 Markdown。
    """
    input_path = Path(input_path).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"文件不存在: {input_path}")

    if output_md is None:
        output_md = str(input_path.with_suffix(".md"))

    result = _get_converter().convert(str(input_path))
    content = result.text_content

    Path(output_md).write_text(content, encoding="utf-8")
    return output_md


# ═══════════════════════════════════════════════════════════════════════
# 第二阶段：Markdown → 任意格式（纯 Python 实现，无 pandoc）
# ═══════════════════════════════════════════════════════════════════════

PANDOC_FORMATS = {"pdf", "docx", "epub", "txt", "html", "md"}


def to_format(input_md: str, output_path: str = None, fmt: str = None):
    """
    使用纯 Python 库将 Markdown 转为目标格式。
    fmt: pdf, docx, epub, txt, html 等
    """
    input_md = Path(input_md).resolve()
    if not input_md.exists():
        raise FileNotFoundError(f"Markdown 文件不存在: {input_md}")

    if fmt is None and output_path is None:
        raise ValueError("必须指定 --fmt 或 --output")

    if fmt is None:
        fmt = Path(output_path).suffix.lstrip(".")

    fmt = fmt.lower()
    if fmt not in PANDOC_FORMATS:
        raise ValueError(f"不支持的格式: {fmt}，支持的格式: {PANDOC_FORMATS}")

    if output_path is None:
        output_path = str(input_md.with_suffix(f".{fmt}"))

    output_path = Path(output_path)

    # ── 加载 markdown 内容 ──────────────────────────────────────────────
    md_content = input_md.read_text(encoding="utf-8")

    # ── TXT ─────────────────────────────────────────────────────────────
    if fmt == "txt":
        # 去掉 markdown 语法，保留纯文本
        text = _md_to_plain_text(md_content)
        output_path.write_text(text, encoding="utf-8")
        print(f"    ✓ → TXT")
        return str(output_path)

    # ── HTML ────────────────────────────────────────────────────────────
    if fmt == "html":
        html = _md_to_html(md_content)
        output_path.write_text(html, encoding="utf-8")
        print(f"    ✓ → HTML")
        return str(output_path)

    # ── PDF ─────────────────────────────────────────────────────────────
    if fmt == "pdf":
        _ensure_package("fpdf2", "fpdf2")
        from fpdf import FPDF
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        _add_md_to_pdf(pdf, md_content)
        pdf.output(str(output_path))
        print(f"    ✓ → PDF")
        return str(output_path)

    # ── DOCX ────────────────────────────────────────────────────────────
    if fmt == "docx":
        _ensure_package("python-docx", "docx")
        from docx import Document
        doc = Document()
        _add_md_to_docx(doc, md_content)
        doc.save(str(output_path))
        print(f"    ✓ → DOCX")
        return str(output_path)

    # ── EPUB ────────────────────────────────────────────────────────────
    if fmt == "epub":
        _ensure_package("ebook-tools", "ebooklib")
        from ebooklib import epub
        book = epub.EpubBook()
        book.set_identifier("converted-doc")
        book.set_title(output_path.stem)
        book.add_author("DocConverter Android")
        chapter = epub.EpubHtml(title="Content", file_name="content.html",
                                lang="zh")
        chapter.content = f"<html><body><pre>{md_content}</pre></body></html>"
        book.add_item(chapter)
        book.spine = ["nav", chapter]
        epub.write_epub(str(output_path), book)
        print(f"    ✓ → EPUB")
        return str(output_path)

    # ── MD ──────────────────────────────────────────────────────────────
    if fmt == "md":
        import shutil
        shutil.copy(str(input_md), str(output_path))
        print(f"    ✓ → MD")
        return str(output_path)

    raise ValueError(f"未实现的格式: {fmt}")


# ═══════════════════════════════════════════════════════════════════════
# Markdown → 明文（去除格式）
# ═══════════════════════════════════════════════════════════════════════

def _md_to_plain_text(md: str) -> str:
    """移除 Markdown 语法，保留纯文本"""
    lines = md.split("\n")
    result = []
    in_code = False

    for raw in lines:
        line = raw.strip()

        # 代码块
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            result.append(line)
            continue

        # 标题
        m = re.match(r"^(#{1,6})\s+(.*)", line)
        if m:
            result.append(m.group(2))
            continue

        # 引用
        if line.startswith(">"):
            result.append(line.lstrip("> ").lstrip(">"))
            continue

        # 列表
        if re.match(r"^[\-\*\+]\s+", line) or re.match(r"^\d+\.\s+", line):
            result.append(re.sub(r"^[\-\*\+]\s+", "", line))
            continue

        # 图片/链接，只留文字
        line = re.sub(r"!\[([^\]]*)\]\([^\)]+\)", r"\1", line)
        line = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", line)
        line = re.sub(r"\*\*([^*]+)\*\*", r"\1", line)
        line = re.sub(r"\*([^*]+)\*", r"\1", line)
        line = re.sub(r"__([^_]+)__", r"\1", line)
        line = re.sub(r"_([^_]+)_", r"\1", line)
        line = re.sub(r"`([^`]+)`", r"\1", line)

        if line:
            result.append(line)

    return "\n".join(result)


# ═══════════════════════════════════════════════════════════════════════
# Markdown → HTML
# ═══════════════════════════════════════════════════════════════════════

def _md_to_html(md: str) -> str:
    """将 Markdown 转换为 HTML"""
    lines = md.split("\n")
    html_lines = []
    in_code_block = False
    in_list = False

    def _escape(s):
        s = s.replace("&", "&amp;")
        s = s.replace("<", "&lt;")
        s = s.replace(">", "&gt;")
        return s

    def _parse_inline(line):
        """转换行内 markdown 元素"""
        line = _escape(line)
        # 图片
        line = re.sub(r"!\[([^\]]*)\]\([^\)]+\)",
                      r'<img alt="\1" src="\2"/>', line)
        # 链接
        line = re.sub(r"\[([^\]]+)\]\([^\)]+\)",
                      r'<a href="\2">\1</a>', line)
        # 粗体
        line = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", line)
        line = re.sub(r"__([^_]+)__", r"<b>\1</b>", line)
        # 斜体
        line = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", line)
        line = re.sub(r"_([^_]+)_", r"<i>\1</i>", line)
        # 行内代码
        line = re.sub(r"`([^`]+)`", r"<code>\1</code>", line)
        return line

    for raw in lines:
        line = raw.rstrip()

        # 代码块
        if line.startswith("```"):
            if in_code_block:
                html_lines.append("</code></pre>")
                in_code_block = False
            else:
                lang = line[3:].strip() or ""
                html_lines.append(f'<pre><code class="{lang}">')
                in_code_block = True
            continue
        if in_code_block:
            html_lines.append(_escape(line))
            continue

        # 标题
        m = re.match(r"^(#{1,6})\s+(.*)", line)
        if m:
            level = len(m.group(1))
            html_lines.append(f"<h{level}>{_parse_inline(m.group(2))}</h{level}>")
            continue

        # 水平线
        if re.match(r"^[\-\*_]{3,}$", line):
            html_lines.append("<hr/>")
            continue

        # 引用块
        if line.startswith(">"):
            content = line.lstrip("> ").lstrip(">")
            html_lines.append(f"<blockquote>{_parse_inline(content)}</blockquote>")
            continue

        # 无序列表
        if re.match(r"^[\-\*\+]\s+", line):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            cleaned = re.sub(r"^[\-\*\+]\s+", "", line)
            html_lines.append("<li>" + _parse_inline(cleaned) + "</li>")
            continue

        # 有序列表
        if re.match(r"^\d+\.\s+", line):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            cleaned = re.sub(r"^\d+\.\s+", "", line)
            html_lines.append("<li>" + _parse_inline(cleaned) + "</li>")
            continue
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False

        # 段落（空行分隔）
        if line.strip():
            html_lines.append(f"<p>{_parse_inline(line)}</p>")
        else:
            html_lines.append("")

    if in_list:
        html_lines.append("</ul>")

    body = "\n".join(html_lines)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Converted Document</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
      max-width:800px;margin:0 auto;padding:20px;line-height:1.6}}
img{{max-width:100%;height:auto}}code{{background:#f4f4f4;padding:2px 6px;
border-radius:3px}}pre{{background:#f4f4f4;padding:16px;overflow-x:auto}}
blockquote{{border-left:4px solid #ddd;margin:0;padding-left:16px;color:#666}}
hr{{border:none;border-top:1px solid #ddd;margin:24px 0}}
</style>
</head>
<body>
{body}
</body>
</html>"""


# ═══════════════════════════════════════════════════════════════════════
# Markdown → PDF（通过 fpdf2）
# ═══════════════════════════════════════════════════════════════════════

def _add_md_to_pdf(pdf, md: str):
    """将 Markdown 内容添加到 FPDF 实例"""
    lines = md.split("\n")
    in_code = False

    for raw in lines:
        line = raw.strip()

        if not line:
            pdf.ln(4)
            continue

        # 代码块
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            pdf.set_font("Courier", size=8)
            pdf.multi_cell(0, 4, line, align="L")
            continue

        # 标题（按层级缩小字号）
        m = re.match(r"^(#{1,6})\s+(.*)", raw)
        if m:
            level = len(m.group(1))
            sizes = {1: 20, 2: 17, 3: 14, 4: 12, 5: 11, 6: 10}
            pdf.set_font("Helvetica", size=sizes.get(level, 12), bold=True)
            pdf.multi_cell(0, 6, m.group(2), align="L")
            continue

        # 引用
        if line.startswith(">"):
            pdf.set_font("Helvetica-Oblique", size=10)
            pdf.set_text_color(100, 100, 100)
            pdf.multi_cell(0, 5, line.lstrip(">").strip(), align="L")
            pdf.set_text_color(0, 0, 0)
            continue

        # 列表项
        if re.match(r"^[\-\*\+]\s+", line) or re.match(r"^\d+\.", line):
            pdf.set_font("Helvetica", size=10)
            pdf.multi_cell(0, 5, "  • " + re.sub(r"^[\-\*\+]\s+", "", line), align="L")
            continue

        # 正文
        pdf.set_font("Helvetica", size=10)
        pdf.set_text_color(0, 0, 0)
        try:
            pdf.multi_cell(0, 5, line, align="L")
        except Exception:
            # 跳过非法字符
            pdf.multi_cell(0, 5, line.encode("latin1", errors="replace").decode("latin1"), align="L")


# ═══════════════════════════════════════════════════════════════════════
# Markdown → DOCX（通过 python-docx）
# ═══════════════════════════════════════════════════════════════════════

def _add_md_to_docx(doc, md: str):
    """将 Markdown 内容添加到 python-docx Document"""
    lines = md.split("\n")
    in_code = False
    code_buf = []

    def flush_code():
        if code_buf:
            p = doc.add_paragraph()
            p.style = "Code"
            p.add_run("\n".join(code_buf))
            code_buf.clear()

    for raw in lines:
        line = raw.strip()

        # 代码块
        if line.startswith("```"):
            if in_code:
                flush_code()
            in_code = not in_code
            continue
        if in_code:
            code_buf.append(line)
            continue

        if not line:
            doc.add_paragraph()
            continue

        # 标题
        m = re.match(r"^(#{1,6})\s+(.*)", raw)
        if m:
            level = len(m.group(1))
            styles = ["Title", "Heading 1", "Heading 2",
                      "Heading 3", "Heading 4", "Heading 5"]
            doc.add_heading(m.group(2), level=min(level, 6))
            continue

        # 引用
        if line.startswith(">"):
            p = doc.add_paragraph()
            run = p.add_run(line.lstrip(">").strip())
            run.italic = True
            continue

        # 列表
        if re.match(r"^[\-\*\+]\s+", line):
            p = doc.add_paragraph(style="List Bullet")
            p.add_run(re.sub(r"^[\-\*\+]\s+", "", line))
            continue
        if re.match(r"^\d+\.\s+", line):
            p = doc.add_paragraph(style="List Number")
            p.add_run(re.sub(r"^\d+\.\s+", "", line))
            continue

        # 普通段落
        doc.add_paragraph(line)

    flush_code()


# ═══════════════════════════════════════════════════════════════════════
# 一键转换：任意格式 → 任意格式
# ═══════════════════════════════════════════════════════════════════════

def convert(input_path: str, output_path: str = None, to_fmt: str = None,
            keep_md: bool = False) -> str:
    """
    完整流程：先转 MD，再转目标格式。
    """
    input_path = Path(input_path).resolve()

    _tmp_md_path = input_path.with_suffix(".tmp.md")
    md_path = to_markdown(input_path, str(_tmp_md_path))

    try:
        result = to_format(md_path, output_path, to_fmt)
    finally:
        if not keep_md and Path(md_path).exists() and ".tmp." in str(md_path):
            Path(md_path).unlink()

    return result


# ═══════════════════════════════════════════════════════════════════════
# 批量转换
# ═══════════════════════════════════════════════════════════════════════

def batch_convert(
    input_dir: str,
    output_dir: str = None,
    to_fmt: str = None,
    pattern: str = "*",
    recursive: bool = False,
    workers: int = 4,
    keep_md: bool = False,
    overwrite: bool = False,
):
    """
    批量转换目录中的文件。
    """
    input_dir = Path(input_dir).resolve()
    if not input_dir.exists():
        raise FileNotFoundError(f"输入目录不存在: {input_dir}")

    if output_dir:
        output_dir = Path(output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = input_dir

    if recursive:
        files = sorted(input_dir.rglob(pattern))
    else:
        files = sorted(input_dir.glob(pattern))

    files = [f for f in files if f.is_file() and f.suffix.lstrip(".").lower() in INPUT_EXTS]

    if not files:
        print(f"⚠ 在 '{input_dir}' 中未找到匹配 '{pattern}' 的文件")
        return

    stats = Stats(total=len(files))
    start_time = time.time()

    print(f"\n📂 批处理开始")
    print(f"   输入目录:   {input_dir}")
    print(f"   输出目录:   {output_dir}")
    print(f"   文件模式:   {pattern}")
    print(f"   目标格式:   {to_fmt or 'MD'}")
    print(f"   并行数:     {workers}")
    print(f"   文件总数:   {len(files)}")
    print(f"{'-'*50}")

    def process_one(file: Path) -> tuple[str, bool, str]:
        try:
            rel_path = file.relative_to(input_dir)
            if output_dir != input_dir:
                stem = rel_path.stem
                parent_parts = rel_path.parts[:-1]
                if parent_parts:
                    safe_name = "_".join(parent_parts) + "_" + stem
                else:
                    safe_name = stem
                out_path = output_dir / (safe_name + f".{to_fmt}")
            else:
                out_path = file.with_suffix(f".{to_fmt}")

            if out_path.exists() and not overwrite:
                return (file.name, False, "已存在，跳过")

            convert(str(file), str(out_path), to_fmt, keep_md=keep_md)
            return (file.name, True, "")
        except Exception as e:
            return (file.name, False, str(e))

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(process_one, f): f for f in files}
        for future in as_completed(futures):
            file_name, ok, err = future.result()
            if ok:
                stats.success += 1
                mark = "✅"
            elif "已存在" in err:
                stats.skipped += 1
                mark = "⏭️"
            else:
                stats.failed += 1
                mark = "❌"
            err_str = f"  ({err})" if err else ""
            print(f"  {mark} {file_name}{err_str}")

    elapsed = time.time() - start_time
    stats.print_summary()
    print(f"  总耗时: {elapsed:.1f}s")
