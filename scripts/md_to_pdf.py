"""
Markdown → PDF 批量转换（Playwright + 自定义 CSS）
================================================
把 4 个 .md 文档转成印刷级 PDF，使用系统中文字体。
"""

import asyncio
from pathlib import Path
import markdown
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT.parent  # /Users/hejingqing/Desktop/比赛/计算机设计大赛/

DOCS = [
    (ROOT / "report" / "研究报告.md", "知忧解郁_研究报告_v1.0.pdf"),
    (ROOT / "docs" / "用户手册.md",   "知忧解郁_用户手册_v1.0.pdf"),
    (ROOT / "docs" / "技术文档.md",   "知忧解郁_技术文档_v1.0.pdf"),
    (ROOT / "README.md",              "知忧解郁_README_v1.0.pdf"),
]

CSS = """
<style>
@page { size: A4; margin: 22mm 18mm; }
body {
    font-family: "PingFang SC", "Microsoft YaHei", "STHeiti", "SimSun", sans-serif;
    font-size: 11pt;
    line-height: 1.7;
    color: #2E2E3A;
    max-width: 100%;
    margin: 0;
}
h1 {
    font-size: 22pt; color: #5B7FFF;
    border-bottom: 3px solid #5B7FFF;
    padding-bottom: 8px;
    margin-top: 18pt; margin-bottom: 14pt;
    page-break-after: avoid;
}
h2 {
    font-size: 17pt; color: #2E2E3A;
    border-left: 5px solid #5B7FFF;
    padding-left: 12px;
    margin-top: 20pt; margin-bottom: 10pt;
    page-break-after: avoid;
}
h3 {
    font-size: 14pt; color: #5B7FFF;
    margin-top: 14pt; margin-bottom: 8pt;
    page-break-after: avoid;
}
h4 { font-size: 12pt; color: #2E2E3A; margin-top: 10pt;}
p { margin: 6pt 0; text-align: justify; }
a { color: #5B7FFF; text-decoration: none; }
ul, ol { margin: 6pt 0; padding-left: 22pt; }
li { margin: 3pt 0; }
strong, b { color: #2E2E3A; font-weight: 700; }
em, i { color: #5B7FFF; font-style: italic; }
code {
    background: rgba(91,127,255,0.08);
    color: #C53030;
    padding: 1pt 5pt;
    border-radius: 3px;
    font-family: "SF Mono", "Monaco", "Consolas", monospace;
    font-size: 9.5pt;
}
pre {
    background: #F8F9FC;
    border-left: 3px solid #5B7FFF;
    padding: 10pt 14pt;
    border-radius: 4px;
    overflow-x: auto;
    page-break-inside: avoid;
    font-size: 9pt;
}
pre code {
    background: transparent;
    color: #2E2E3A;
    padding: 0;
}
table {
    border-collapse: collapse;
    width: 100%;
    margin: 10pt 0;
    page-break-inside: avoid;
}
th {
    background: rgba(91,127,255,0.12);
    color: #5B7FFF;
    padding: 6pt 8pt;
    border: 1px solid #DDD;
    font-weight: 700;
    text-align: left;
}
td {
    padding: 5pt 8pt;
    border: 1px solid #DDD;
}
tr:nth-child(even) { background: #FAFBFD; }
blockquote {
    border-left: 4px solid #5B7FFF;
    background: rgba(91,127,255,0.05);
    margin: 10pt 0;
    padding: 8pt 14pt;
    color: #555;
}
hr {
    border: none;
    border-top: 1px solid #DDD;
    margin: 20pt 0;
}
img { max-width: 100%; height: auto; }
.cover {
    text-align: center;
    page-break-after: always;
    padding-top: 100pt;
}
.cover h1 { border: none; font-size: 30pt; margin-bottom: 24pt; }
.cover .sub { font-size: 14pt; color: #5B7FFF; margin-bottom: 60pt; }
.cover .meta { font-size: 11pt; color: #777; line-height: 2; }
</style>
"""


async def md_to_pdf(browser, md_path: Path, pdf_name: str):
    print(f"  📄 {md_path.name}", end=" ... ", flush=True)
    md_text = md_path.read_text(encoding="utf-8")
    html_body = markdown.markdown(
        md_text,
        extensions=["extra", "codehilite", "tables", "toc", "fenced_code"],
    )
    html_full = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>{md_path.stem}</title>
{CSS}
</head>
<body>
{html_body}
</body>
</html>
"""
    page = await browser.new_page()
    await page.set_content(html_full, wait_until="networkidle")
    pdf_path = OUT_DIR / pdf_name
    await page.pdf(
        path=str(pdf_path),
        format="A4",
        margin={"top": "22mm", "bottom": "22mm", "left": "18mm", "right": "18mm"},
        print_background=True,
    )
    await page.close()
    sz_kb = pdf_path.stat().st_size // 1024
    print(f"OK ({sz_kb} KB)")


async def main():
    print("=" * 60)
    print("Markdown → PDF 批量转换")
    print("=" * 60)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        for md, pdf in DOCS:
            if md.exists():
                await md_to_pdf(browser, md, pdf)
            else:
                print(f"  ⚠️ 跳过（不存在）: {md}")
        await browser.close()
    print()
    print(f"✅ 全部 PDF 已保存到 {OUT_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
