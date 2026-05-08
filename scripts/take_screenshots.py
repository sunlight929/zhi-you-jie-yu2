"""
自动批量截图（Playwright）
========================
为参赛作品报名材料的「作品效果图」字段生成高清截图。

特点：
- 视口 1920×1080，2x 视网膜分辨率（输出实际 3840×2160）
- 整页截图（full_page=True），包含完整滚动内容
- 自动等待 ECharts 中国地图加载完成
- 智能评估页面自动填写并提交，捕获高 / 低风险结果

输出目录：assets/screenshots/
"""

import asyncio
import time
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "assets" / "screenshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BASE = "http://localhost:8501"

PAGES = [
    ("01_首页",            f"{BASE}/",              4),
    ("02_数据驾驶舱",      f"{BASE}/数据驾驶舱",    8),  # 等待中国地图加载
    ("03_数据全景",        f"{BASE}/数据全景",      4),
    ("04_风险因素分析",    f"{BASE}/风险因素分析",  4),
    ("05_天津决策支持",    f"{BASE}/天津决策支持",  4),
    ("06_关于项目",        f"{BASE}/关于项目",      3),
    ("07_智能评估_表单",   f"{BASE}/智能评估",      3),
]


async def screenshot_page(page, name: str, url: str, wait_seconds: int = 4):
    """打开页面，等待加载，按实际内容高度调整 viewport 后再截图。"""
    print(f"  📸 {name} ...", end=" ", flush=True)
    await page.goto(url, wait_until="networkidle", timeout=30000)
    # 折叠侧边栏让大屏更纯粹
    try:
        await page.evaluate("""() => {
            const btn = document.querySelector('[data-testid=\"stSidebarCollapseButton\"] button');
            if (btn) btn.click();
        }""")
    except Exception:
        pass
    # 等待图表渲染（包括 ECharts fetch GeoJSON）
    await asyncio.sleep(wait_seconds)

    # 关键：取真实滚动高度，调整 viewport，让所有内容自然展开
    real_h = await page.evaluate(
        "Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)"
    )
    real_h = int(real_h) + 100  # 留余量
    real_h = min(real_h, 6000)  # 上限避免极端情况
    await page.set_viewport_size({"width": 1920, "height": real_h})
    await asyncio.sleep(2)  # 重排重绘

    out = OUT_DIR / f"{name}.png"
    await page.screenshot(path=str(out), full_page=True, type="png")
    size_kb = out.stat().st_size // 1024
    print(f"OK ({size_kb} KB,  实际高度 {real_h}px)")

    # 还原 viewport 给下一页
    await page.set_viewport_size({"width": 1920, "height": 1080})
    return out


async def fill_phq9_and_submit(page, option_text: str):
    """填写 PHQ-9 9 道题（全选指定选项）+ 提交。"""
    labels = page.locator(f'label:has-text("{option_text}")')
    count = await labels.count()
    for j in range(min(count, 9)):
        await labels.nth(j).click(force=True)
        await asyncio.sleep(0.08)
    await asyncio.sleep(0.8)

    # 提交：用更稳健的方式找按钮
    submitted = False
    for selector in [
        'button:has-text("提交评估")',
        '[data-testid="stButton"] button',
        'button[kind="primary"]',
    ]:
        try:
            btn = page.locator(selector).first
            if await btn.count() > 0:
                await btn.scroll_into_view_if_needed()
                await btn.click(force=True, timeout=5000)
                submitted = True
                break
        except Exception:
            continue

    if not submitted:
        print("\n    ⚠️ 提交按钮未找到", end="")
        return False

    # 等待结果渲染（仪表盘 + 贡献图 + 建议）
    # Streamlit 的图表是 Plotly，需要时间 layout
    await asyncio.sleep(8)

    # 滚回顶部，从顶到底完整截图
    await page.evaluate("window.scrollTo(0, 0);")
    await asyncio.sleep(1)

    # 等待 Plotly 全部渲染完
    try:
        await page.wait_for_function(
            """() => {
                const plotly = document.querySelectorAll('.js-plotly-plot');
                return plotly.length >= 2;
            }""",
            timeout=10000,
        )
    except Exception:
        pass
    await asyncio.sleep(2)
    return True


async def screenshot_assessment_results(page):
    """智能评估页面 - 自动填表并捕获高 / 低风险结果。"""
    for case_name, option, fname in [
        ("高风险（PHQ-9 全选'几乎每天'）", "几乎每天", "08_智能评估_高风险.png"),
        ("低风险（PHQ-9 全选'完全不会'）", "完全不会", "09_智能评估_低风险.png"),
    ]:
        print(f"  📸 {fname} - {case_name} ...", end=" ", flush=True)
        await page.goto(f"{BASE}/智能评估", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(4)
        # 先折叠侧边栏
        try:
            await page.evaluate("""() => {
                const btn = document.querySelector('[data-testid="stSidebarCollapseButton"] button');
                if (btn) btn.click();
            }""")
            await asyncio.sleep(0.5)
        except Exception:
            pass

        ok = await fill_phq9_and_submit(page, option)
        out = OUT_DIR / fname
        await page.screenshot(path=str(out), full_page=True, type="png")
        size_kb = out.stat().st_size // 1024
        print(f"OK ({size_kb} KB){'' if ok else ' [⚠️ 提交可能失败]'}")


async def main(only: str = "all"):
    print("=" * 60)
    print("开始批量截图（视口 1920×1080，2x DPR）")
    print("=" * 60)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=2,  # 视网膜分辨率
            locale="zh-CN",
        )
        page = await context.new_page()
        page.set_default_timeout(30000)

        # 基础 7 个页面
        if only in ("all", "pages"):
            for name, url, wait in PAGES:
                try:
                    await screenshot_page(page, name, url, wait)
                except Exception as e:
                    print(f"FAILED: {e}")

        # 智能评估高 / 低风险
        if only in ("all", "assessment"):
            try:
                await screenshot_assessment_results(page)
            except Exception as e:
                print(f"  ⚠️ 智能评估自动填表整体失败：{e}")

        await browser.close()

    print()
    print("=" * 60)
    print(f"✅ 截图全部保存到 {OUT_DIR}")
    print("=" * 60)
    files = sorted(OUT_DIR.glob("*.png"))
    for f in files:
        sz = f.stat().st_size // 1024
        print(f"   {f.name}  ({sz} KB)")


if __name__ == "__main__":
    import sys
    only = sys.argv[1] if len(sys.argv) > 1 else "all"
    asyncio.run(main(only))
