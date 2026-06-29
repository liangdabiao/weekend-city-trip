#!/usr/bin/env python3
"""Markdown 转 HTML 转换器(为城市调查报告优化)

特性:
- GFM 表格、代码块、图片、引用块
- 中文友好字体(苹方/微软雅黑/思源黑体)
- 响应式布局(手机/平板/桌面)
- 内嵌 CSS(单文件可分享,无外部依赖)
- 图片 lazy loading
- 自动提取首屏 H1 作为页面标题

依赖(任一即可,按优先级尝试):
1. markdown + pymdown-extensions  → pip install markdown pymdown-extensions
2. markdown2                       → pip install markdown2
3. 兜底内置极简转换器(无需任何外部库,仅基础样式)

用法:
    python md_to_html.py <input.md> [output.html]
    python md_to_html.py report.md              # 输出 report.html
    python md_to_html.py report.md out.html     # 输出 out.html
"""

import sys
import re
from pathlib import Path


# ============================================================
# HTML 模板
# ============================================================

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
{css}
</style>
</head>
<body>
<article class="container">
{content}
</article>
</body>
</html>
"""


CSS = """
* { box-sizing: border-box; }
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
                 "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei",
                 "Source Han Sans CN", "Helvetica Neue", sans-serif;
    line-height: 1.75;
    color: #24292e;
    background: #f6f8fa;
    margin: 0;
    padding: 24px;
}
.container {
    max-width: 920px;
    margin: 0 auto;
    background: white;
    padding: 48px 56px;
    border-radius: 10px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}
h1 {
    font-size: 2.1em;
    border-bottom: 3px solid #0969da;
    padding-bottom: 12px;
    color: #0969da;
    margin-top: 0;
    letter-spacing: 0.5px;
}
h2 {
    font-size: 1.55em;
    border-bottom: 1px solid #d0d7de;
    padding-bottom: 8px;
    margin-top: 2.2em;
    color: #1f2328;
}
h3 {
    font-size: 1.25em;
    margin-top: 1.6em;
    color: #1f2328;
}
h4 {
    font-size: 1.05em;
    margin-top: 1.3em;
    color: #1f2328;
}
p { margin: 12px 0; }
table {
    border-collapse: collapse;
    width: 100%;
    margin: 18px 0;
    font-size: 0.95em;
    overflow-x: auto;
    display: block;
}
th, td {
    border: 1px solid #d0d7de;
    padding: 9px 14px;
    text-align: left;
    vertical-align: top;
}
th {
    background: #f6f8fa;
    font-weight: 600;
    color: #1f2328;
}
tr:nth-child(even) { background: #fbfcfd; }
tr:hover { background: #f0f6ff; }
img {
    max-width: 100%;
    height: auto;
    border-radius: 8px;
    margin: 14px 0;
    display: block;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
}
code {
    background: #f6f8fa;
    padding: 2px 7px;
    border-radius: 4px;
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
    font-size: 0.9em;
    color: #cf222e;
}
pre {
    background: #f6f8fa;
    padding: 18px;
    border-radius: 8px;
    overflow-x: auto;
    border: 1px solid #eaecef;
}
pre code {
    background: none;
    padding: 0;
    color: #1f2328;
}
blockquote {
    border-left: 4px solid #0969da;
    padding: 10px 18px;
    margin: 16px 0;
    background: #f6f8fa;
    color: #57606a;
    border-radius: 0 6px 6px 0;
}
a { color: #0969da; text-decoration: none; }
a:hover { text-decoration: underline; }
strong { font-weight: 600; color: #1f2328; }
em { font-style: italic; color: #57606a; }
hr {
    border: none;
    border-top: 2px solid #eaecef;
    margin: 28px 0;
}
ul, ol { padding-left: 26px; }
li { margin: 5px 0; }
hr:first-child, h1:first-child { margin-top: 0; }
@media (max-width: 768px) {
    body { padding: 12px; }
    .container { padding: 24px 22px; }
    table { font-size: 0.85em; }
    th, td { padding: 6px 9px; }
    h1 { font-size: 1.7em; }
    h2 { font-size: 1.3em; }
}
@media print {
    body { background: white; padding: 0; }
    .container { box-shadow: none; padding: 0; max-width: none; }
    a { color: inherit; text-decoration: none; }
}
"""


# ============================================================
# 转换逻辑(三档优先级)
# ============================================================

def convert_with_markdown_lib(md_text):
    """优先方案:python-markdown + 扩展"""
    import markdown
    extensions = [
        'tables',
        'fenced_code',
        'nl2br',
        'sane_lists',
        'attr_list',
        'md_in_html',
    ]
    # 可选扩展(不强制)
    try:
        extensions.append('codehilite')
        extension_configs = {
            'codehilite': {'css_class': 'highlight', 'guess_lang': False, 'noclasses': True}
        }
    except Exception:
        extension_configs = {}

    md = markdown.Markdown(extensions=extensions, extension_configs=extension_configs)
    return md.convert(md_text)


def convert_with_markdown2(md_text):
    """次选方案:markdown2"""
    import markdown2
    return markdown2.markdown(md_text, extras=[
        'tables',
        'fenced-code-blocks',
        'header-ids',
        'strike',
        'task_list',
        'break-on-newline',
        'cuddled-lists',
    ])


def convert_fallback(md_text):
    """兜底方案:内置极简转换器(无外部依赖)"""

    def escape_html(text):
        return (text.replace('&', '&amp;')
                    .replace('<', '&lt;')
                    .replace('>', '&gt;'))

    def inline_format(text):
        # 图片
        text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)',
                      r'<img src="\2" alt="\1" loading="lazy">', text)
        # 链接
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)',
                      r'<a href="\2">\1</a>', text)
        # 加粗
        text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
        # 斜体
        text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', text)
        # 行内代码
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        return text

    lines = md_text.split('\n')
    html = []
    in_table = False
    in_thead = True
    in_ul = False
    in_ol = False
    in_code = False
    in_blockquote = False

    def close_table():
        nonlocal in_table, in_thead
        if in_table:
            html.append('</tbody></table>')
            in_table = False
            in_thead = True

    def close_ul():
        nonlocal in_ul
        if in_ul:
            html.append('</ul>')
            in_ul = False

    def close_ol():
        nonlocal in_ol
        if in_ol:
            html.append('</ol>')
            in_ol = False

    def close_blockquote():
        nonlocal in_blockquote
        if in_blockquote:
            html.append('</blockquote>')
            in_blockquote = False

    for line in lines:
        # 代码块
        if line.strip().startswith('```'):
            if in_code:
                html.append('</code></pre>')
                in_code = False
            else:
                close_table(); close_ul(); close_ol(); close_blockquote()
                html.append('<pre><code>')
                in_code = True
            continue
        if in_code:
            html.append(escape_html(line))
            continue

        stripped = line.strip()

        # 空行
        if not stripped:
            close_table(); close_ul(); close_ol(); close_blockquote()
            continue

        # 标题
        m = re.match(r'^(#{1,6})\s+(.+)$', line)
        if m:
            close_table(); close_ul(); close_ol(); close_blockquote()
            level = len(m.group(1))
            html.append(f'<h{level}>{inline_format(m.group(2))}</h{level}>')
            continue

        # 水平线
        if stripped in ('---', '***', '___'):
            close_table(); close_ul(); close_ol(); close_blockquote()
            html.append('<hr>')
            continue

        # 引用块
        if stripped.startswith('>'):
            close_table(); close_ul(); close_ol()
            if not in_blockquote:
                html.append('<blockquote>')
                in_blockquote = True
            html.append(f'<p>{inline_format(stripped[1:].strip())}</p>')
            continue

        # 表格
        if stripped.startswith('|'):
            close_ul(); close_ol(); close_blockquote()
            cells = [c.strip() for c in stripped.split('|')]
            if cells and cells[0] == '':
                cells = cells[1:]
            if cells and cells[-1] == '':
                cells = cells[:-1]
            # 分隔行(| --- | --- |)
            if all(re.match(r'^:?-+:?$', c) for c in cells if c):
                in_thead = False
                continue
            if not in_table:
                html.append('<table>')
                in_table = True
                in_thead = True
            if in_thead:
                html.append('<thead><tr>' +
                            ''.join(f'<th>{inline_format(c)}</th>' for c in cells) +
                            '</tr></thead><tbody>')
                in_thead = False
            else:
                html.append('<tr>' +
                            ''.join(f'<td>{inline_format(c)}</td>' for c in cells) +
                            '</tr>')
            continue

        # 无序列表
        if re.match(r'^[-*+]\s+', stripped):
            close_table(); close_ol(); close_blockquote()
            if not in_ul:
                html.append('<ul>')
                in_ul = True
            html.append(f'<li>{inline_format(re.sub(r"^[-*+]\s+", "", stripped))}</li>')
            continue

        # 有序列表
        if re.match(r'^\d+\.\s+', stripped):
            close_table(); close_ul(); close_blockquote()
            if not in_ol:
                html.append('<ol>')
                in_ol = True
            html.append(f'<li>{inline_format(re.sub(r"^\d+\.\s+", "", stripped))}</li>')
            continue

        # 普通段落
        close_table(); close_ul(); close_ol(); close_blockquote()
        html.append(f'<p>{inline_format(stripped)}</p>')

    close_table(); close_ul(); close_ol(); close_blockquote()
    if in_code:
        html.append('</code></pre>')

    return '\n'.join(html)


def convert_markdown_to_html(md_text):
    """三档优先级尝试转换"""
    errors = []

    try:
        return convert_with_markdown_lib(md_text), 'python-markdown'
    except ImportError:
        errors.append('python-markdown 未安装')
    except Exception as e:
        errors.append(f'python-markdown 异常: {e}')

    try:
        return convert_with_markdown2(md_text), 'markdown2'
    except ImportError:
        errors.append('markdown2 未安装')
    except Exception as e:
        errors.append(f'markdown2 异常: {e}')

    # 兜底
    return convert_fallback(md_text), 'fallback'


# ============================================================
# 主入口
# ============================================================

def extract_title(md_text, fallback='Document'):
    """提取第一个 # 标题作为页面 title"""
    m = re.search(r'^#\s+(.+)$', md_text, re.MULTILINE)
    return m.group(1).strip() if m else fallback


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f'错误: 输入文件不存在 → {input_path}')
        sys.exit(1)

    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2])
    else:
        output_path = input_path.with_suffix('.html')

    md_text = input_path.read_text(encoding='utf-8')
    content, engine = convert_markdown_to_html(md_text)
    title = extract_title(md_text, fallback=input_path.stem)

    html = HTML_TEMPLATE.format(
        title=title,
        css=CSS,
        content=content,
    )

    output_path.write_text(html, encoding='utf-8')

    size_kb = output_path.stat().st_size / 1024
    print(f'✓ 已生成: {output_path}')
    print(f'  源文件: {input_path}')
    print(f'  大小: {size_kb:.1f} KB')
    print(f'  引擎: {engine}')

    if engine == 'fallback':
        print('  提示: 使用了兜底转换器(无外部依赖),如需完整 GFM 支持请安装:')
        print('        pip install markdown pymdown-extensions')


if __name__ == '__main__':
    main()
