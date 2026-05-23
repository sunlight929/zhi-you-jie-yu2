"""
生成微信推广用的二维码海报（两个版本）
====================================
- assets/posters/poster_minimal.png    极简粉色版（适合朋友圈 / 班级群）
- assets/posters/poster_professional.png  专业医学风（适合老师 / 家长 / 严肃群）

依赖：qrcode、Pillow（已在 venv 安装）
"""

from __future__ import annotations
from pathlib import Path
import qrcode
from qrcode.image.pil import PilImage
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets" / "posters"
ASSETS.mkdir(parents=True, exist_ok=True)

TEST_URL = "https://zhi-you-jie-yu.streamlit.app/?mode=test"

# macOS 中文字体路径（兼容大多数 Mac）
FONTS_TO_TRY = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
]


def get_font(size: int) -> ImageFont.FreeTypeFont:
    """优先用系统中文字体，找不到就用 PIL 默认字体。"""
    for fp in FONTS_TO_TRY:
        if Path(fp).exists():
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return ImageFont.load_default()


def make_qr(url: str, box_size: int = 12, fill: str = "#000000",
            back: str = "#FFFFFF") -> Image.Image:
    """生成二维码图片。"""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=box_size,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color=fill, back_color=back).convert("RGB")
    return img


# ============================================================
# 海报 1：极简粉色版（朋友圈 / 班级群风格）
# ============================================================
def make_minimal_poster():
    W, H = 1080, 1440  # 标准海报比例 3:4
    img = Image.new("RGB", (W, H), "#FFF5F7")  # 极浅粉底
    draw = ImageDraw.Draw(img)

    # 顶部柔和粉紫渐变装饰
    for y in range(0, 180):
        ratio = y / 180
        r = int(255 - 30 * ratio)
        g = int(200 - 40 * ratio)
        b = int(220 + 20 * ratio)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # 主标题
    title_font = get_font(96)
    title = "知忧·解郁"
    bbox = draw.textbbox((0, 0), title, font=title_font)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) / 2, 260), title, fill="#7C5CFF", font=title_font)

    # 副标题
    sub_font = get_font(36)
    subtitle = "心理健康自评 · 5 分钟看见自己的情绪"
    bbox = draw.textbbox((0, 0), subtitle, font=sub_font)
    sw = bbox[2] - bbox[0]
    draw.text(((W - sw) / 2, 400), subtitle, fill="#6B7280", font=sub_font)

    # 二维码（黑码白底，微信扫码识别最稳定）
    qr_img = make_qr(TEST_URL, box_size=12, fill="#1F1B3D", back="#FFFFFF")
    qr_size = 560
    qr_img = qr_img.resize((qr_size, qr_size), Image.LANCZOS)
    qr_x = (W - qr_size) // 2
    qr_y = 500
    # 先画白色背景框（确保二维码识别区域纯白）
    draw.rectangle(
        [qr_x - 10, qr_y - 10, qr_x + qr_size + 10, qr_y + qr_size + 10],
        fill="#FFFFFF",
    )
    img.paste(qr_img, (qr_x, qr_y))
    # 装饰边框（粉色）
    draw.rectangle(
        [qr_x - 20, qr_y - 20, qr_x + qr_size + 20, qr_y + qr_size + 20],
        outline="#FBA4C4", width=4,
    )

    # 扫码提示
    scan_font = get_font(40)
    scan_text = "微信长按识别 / 扫码"
    bbox = draw.textbbox((0, 0), scan_text, font=scan_font)
    sw = bbox[2] - bbox[0]
    draw.text(((W - sw) / 2, qr_y + qr_size + 50), scan_text,
              fill="#7C5CFF", font=scan_font)

    # 卖点 3 行
    pt_font = get_font(30)
    pt_y = qr_y + qr_size + 160
    points = [
        "◆  PHQ-9 国际通用抑郁量表",
        "◆  AI 心理助手实时陪聊",
        "◆  完全匿名,不收集身份信息",
    ]
    for i, pt in enumerate(points):
        bbox = draw.textbbox((0, 0), pt, font=pt_font)
        pw = bbox[2] - bbox[0]
        draw.text(((W - pw) / 2, pt_y + i * 56), pt,
                  fill="#4B5563", font=pt_font)

    # 底部署名
    foot_font = get_font(22)
    foot = "天津大学医学院 · 临床医学专业 · 学生研究项目"
    bbox = draw.textbbox((0, 0), foot, font=foot_font)
    fw = bbox[2] - bbox[0]
    draw.text(((W - fw) / 2, H - 80), foot, fill="#9CA3AF", font=foot_font)

    out = ASSETS / "poster_minimal.png"
    img.save(out, "PNG", quality=95)
    print(f"✓ 极简版海报 -> {out}")


# ============================================================
# 海报 2：专业医学风（深色系，适合老师 / 家长 / 严肃群）
# ============================================================
def make_professional_poster():
    W, H = 1080, 1440
    img = Image.new("RGB", (W, H), "#0A0B1E")  # 深蓝底，与平台同色调
    draw = ImageDraw.Draw(img)

    # 顶部品牌色条
    for y in range(0, 120):
        ratio = y / 120
        r = int(91 + 36 * ratio)
        g = int(127 + 60 * ratio)
        b = int(255 - 95 * ratio)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Logo / 主标题
    title_font = get_font(88)
    title = "知忧·解郁"
    bbox = draw.textbbox((0, 0), title, font=title_font)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) / 2, 220), title, fill="#5BC8FF", font=title_font)

    # 副标题（产品定位）
    sub_font = get_font(32)
    subtitle = "多源数据驱动的抑郁症风险识别与决策支持平台"
    bbox = draw.textbbox((0, 0), subtitle, font=sub_font)
    sw = bbox[2] - bbox[0]
    draw.text(((W - sw) / 2, 350), subtitle, fill="#B8C5E0", font=sub_font)

    # 用户测试招募 标语
    cta_font = get_font(48)
    cta = "用户体验测试 · 诚邀参与"
    bbox = draw.textbbox((0, 0), cta, font=cta_font)
    cw = bbox[2] - bbox[0]
    draw.text(((W - cw) / 2, 420), cta, fill="#FFFFFF", font=cta_font)

    # 二维码（黑码白底，微信识别最稳定）
    qr_img = make_qr(TEST_URL, box_size=12, fill="#000000", back="#FFFFFF")
    qr_size = 540
    qr_img = qr_img.resize((qr_size, qr_size), Image.LANCZOS)
    qr_x = (W - qr_size) // 2
    qr_y = 540

    # 二维码外框：浅蓝霓虹效果（多层）
    for offset in [12, 8, 4]:
        draw.rectangle(
            [qr_x - 24 - offset, qr_y - 24 - offset,
             qr_x + qr_size + 24 + offset, qr_y + qr_size + 24 + offset],
            outline="#3B82F6", width=1,
        )
    # 白色填充背景给二维码
    draw.rectangle(
        [qr_x - 16, qr_y - 16, qr_x + qr_size + 16, qr_y + qr_size + 16],
        fill="#FFFFFF",
    )
    img.paste(qr_img, (qr_x, qr_y))

    # 扫码提示
    scan_font = get_font(36)
    scan_text = "微信长按二维码 / 扫码体验"
    bbox = draw.textbbox((0, 0), scan_text, font=scan_font)
    sw = bbox[2] - bbox[0]
    draw.text(((W - sw) / 2, qr_y + qr_size + 50), scan_text,
              fill="#5BC8FF", font=scan_font)

    # 4 个卖点 2x2 网格（用符号代替 emoji）
    pt_font = get_font(26)
    pt_y = qr_y + qr_size + 130
    points = [
        ("◆", "PHQ-9 / CES-D 国际通用量表"),
        ("◆", "DeepSeek 大模型心理助手"),
        ("◆", "机器学习风险预测模型"),
        ("◆", "完全匿名 · 隐私保护"),
    ]
    for i, (icon, txt) in enumerate(points):
        col = i % 2
        row = i // 2
        x = 140 + col * 480
        y = pt_y + row * 64
        line = f"{icon}  {txt}"
        draw.text((x, y), line, fill="#E8F0FF", font=pt_font)

    # 分隔线
    div_y = H - 140
    draw.line([(120, div_y), (W - 120, div_y)],
              fill="#3B4659", width=1)

    # 底部署名
    foot_font = get_font(22)
    foot_lines = [
        "天津大学医学院 · 临床医学专业本科生研究项目",
        "指导教师：天津大学医学院 张小臣 副研究员（医学方向）",
        "　　　　　电气自动化与信息工程学院 张淑芳 副教授（AI 方向）",
    ]
    for i, line in enumerate(foot_lines):
        bbox = draw.textbbox((0, 0), line, font=foot_font)
        fw = bbox[2] - bbox[0]
        draw.text(((W - fw) / 2, div_y + 25 + i * 32), line,
                  fill="#9CA3AF", font=foot_font)

    out = ASSETS / "poster_professional.png"
    img.save(out, "PNG", quality=95)
    print(f"✓ 专业版海报 -> {out}")


if __name__ == "__main__":
    make_minimal_poster()
    make_professional_poster()
    print(f"\n📂 海报已保存到: {ASSETS}")
    print(f"🔗 二维码指向: {TEST_URL}")
