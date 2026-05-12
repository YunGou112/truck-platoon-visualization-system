from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "ppt_style_proposals"
LOGO_PATH = ROOT / "assets" / "school_logo.png"
W, H = 1600, 900


def rgb(hex_str: str) -> Tuple[int, int, int]:
    hex_str = hex_str.lstrip("#")
    return tuple(int(hex_str[i : i + 2], 16) for i in (0, 2, 4))


def alpha(color, a: int) -> Tuple[int, int, int, int]:
    if isinstance(color, str):
        base = rgb(color)
    else:
        base = tuple(color[:3])
    return (*base, a)


def load_font(size: int, bold: bool = False, serif: bool = False) -> ImageFont.FreeTypeFont:
    if serif:
        path = r"C:\Windows\Fonts\simsun.ttc"
    elif bold:
        path = r"C:\Windows\Fonts\msyhbd.ttc"
    else:
        path = r"C:\Windows\Fonts\msyh.ttc"
    return ImageFont.truetype(path, size=size)


def paste_logo(canvas: Image.Image, box_w: int) -> None:
    logo = Image.open(LOGO_PATH).convert("RGBA")
    ratio = box_w / logo.width
    size = (box_w, int(logo.height * ratio))
    logo = logo.resize(size, Image.LANCZOS)
    canvas.alpha_composite(logo, (96, 64))


def draw_text(
    draw: ImageDraw.ImageDraw,
    xy: Tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill,
    anchor: str | None = None,
    spacing: int = 6,
) -> None:
    draw.multiline_text(xy, text, font=font, fill=fill, anchor=anchor, spacing=spacing)


def rounded_panel(draw: ImageDraw.ImageDraw, box, fill, outline=None, width: int = 2, radius: int = 18):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def add_footer(draw: ImageDraw.ImageDraw, style: Dict, page_name: str, num: int) -> None:
    f = load_font(22)
    draw.line((92, H - 78, W - 92, H - 78), fill=style["line"], width=2)
    draw_text(draw, (96, H - 58), "兰州交通大学硕士论文答辩 | 视觉方案示意", f, style["muted"])
    draw_text(draw, (W - 96, H - 58), f"{page_name}  {num:02d}", f, style["muted"], anchor="ra")


def cover_page(style: Dict) -> Image.Image:
    img = Image.new("RGBA", (W, H), style["bg"])
    draw = ImageDraw.Draw(img)
    style["cover_bg"](draw, img, style)
    paste_logo(img, 420 if style["name"] != "科技理性型" else 360)

    draw_text(draw, (110, 250), "数据驱动的卡车队列可视化系统", load_font(54, bold=True), style["title"])
    draw_text(
        draw,
        (110, 328),
        "Master Thesis Defense Presentation",
        load_font(26),
        style["accent"],
    )
    draw_text(
        draw,
        (110, 410),
        "答辩人：张同学\n专业：交通运输工程\n导师：王建强 教授\n学院：交通运输学院\n答辩时间：2026 年 6 月",
        load_font(28),
        style["text"],
        spacing=18,
    )
    if style["name"] == "稳重学术型":
        draw.line((1080, 180, 1080, 730), fill=style["accent"], width=3)
        rounded_panel(draw, (1130, 210, 1470, 690), fill=alpha(style["primary"], 22), outline=alpha(style["primary"], 70), width=2)
        draw_text(draw, (1170, 260), "关键词", load_font(28, bold=True), style["primary"])
        draw_text(draw, (1170, 320), "数据驱动\n可视化系统\n卡车队列\n异常预警", load_font(34, bold=True), style["title"], spacing=28)
    elif style["name"] == "现代简约型":
        draw.rectangle((1210, 0, 1600, 900), fill=alpha(style["primary"], 20))
        for y in range(180, 741, 140):
            draw.line((1250, y, 1480, y), fill=style["primary"], width=2)
        draw_text(draw, (1250, 760), "FORMAL\nMINIMAL\nCLEAR", load_font(30, bold=True), style["primary"], spacing=18)
    elif style["name"] == "科技理性型":
        draw.rectangle((960, 120, 1490, 720), fill=alpha(style["panel"], 255), outline=alpha(style["accent"], 170), width=2)
        for x in range(980, 1490, 64):
            draw.line((x, 120, x, 720), fill=alpha(style["line"], 80), width=1)
        for y in range(140, 721, 64):
            draw.line((960, y, 1490, y), fill=alpha(style["line"], 80), width=1)
        draw_text(draw, (1000, 180), "Defense Deck\nVisual System", load_font(42, bold=True), style["title"], spacing=12)
        draw_text(draw, (1000, 340), "结构化布局\n数据化表达\n审稿式阅读体验", load_font(28), style["text"], spacing=18)
    else:
        rounded_panel(draw, (1020, 180, 1490, 720), fill=alpha(style["primary"], 18), outline=alpha(style["primary"], 60), width=2, radius=28)
        draw_text(draw, (1080, 250), "清爽学术感", load_font(40, bold=True), style["primary"])
        draw_text(draw, (1080, 350), "轻边框\n大留白\n柔和分区\n便于套版", load_font(28), style["text"], spacing=18)

    add_footer(draw, style, "封面页", 1)
    return img


def toc_page(style: Dict) -> Image.Image:
    img = Image.new("RGBA", (W, H), style["bg"])
    draw = ImageDraw.Draw(img)
    style["inner_bg"](draw, img, style)
    draw_text(draw, (104, 88), "目录", load_font(42, bold=True), style["title"])
    draw_text(draw, (104, 142), "Contents", load_font(20), style["accent"])

    items = [
        ("01", "研究背景与问题提出", "Background"),
        ("02", "研究思路与方法设计", "Methodology"),
        ("03", "系统实现与关键模块", "Implementation"),
        ("04", "实验结果与效果验证", "Results"),
        ("05", "结论、创新点与展望", "Conclusion"),
    ]
    y = 240
    for no, zh, en in items:
        rounded_panel(draw, (118, y - 20, 1480, y + 80), fill=style["panel"], outline=style["line"], width=2, radius=18)
        draw_text(draw, (155, y), no, load_font(34, bold=True), style["primary"])
        draw_text(draw, (300, y - 2), zh, load_font(30, bold=True), style["title"])
        draw_text(draw, (1120, y + 2), en, load_font(24), style["muted"])
        y += 112

    if style["name"] == "现代简约型":
        draw.rectangle((94, 214, 100, 786), fill=style["primary"])
    elif style["name"] == "科技理性型":
        for x in range(100, 1500, 140):
            draw.line((x, 184, x, 786), fill=alpha(style["line"], 70), width=1)
    add_footer(draw, style, "目录页", 2)
    return img


def chapter_page(style: Dict) -> Image.Image:
    img = Image.new("RGBA", (W, H), style["bg"])
    draw = ImageDraw.Draw(img)
    style["chapter_bg"](draw, img, style)
    draw_text(draw, (140, 235), "02", load_font(130, bold=True), alpha(style["primary"], 70))
    draw_text(draw, (140, 390), "研究思路与方法设计", load_font(52, bold=True), style["title"])
    draw_text(draw, (140, 468), "Methodology and System Design", load_font(26), style["accent"])
    draw_text(draw, (140, 590), "从数据处理、状态识别到可视化交互，\n构建可解释、可复盘、可验证的分析闭环。", load_font(30), style["text"], spacing=18)
    add_footer(draw, style, "章节页", 3)
    return img


def framework_page(style: Dict) -> Image.Image:
    img = Image.new("RGBA", (W, H), style["bg"])
    draw = ImageDraw.Draw(img)
    style["inner_bg"](draw, img, style)
    draw_text(draw, (104, 88), "研究框架", load_font(42, bold=True), style["title"])
    draw_text(draw, (104, 142), "Research Framework / Technical Route", load_font(20), style["accent"])

    boxes = [
        ("研究问题", "多维时序数据\n难以直观表达"),
        ("数据处理", "清洗 / 对齐 / 补全\n特征构建"),
        ("逻辑设计", "状态判别\n预警规则"),
        ("可视化实现", "轨迹回放\n参数标注"),
        ("实验验证", "功能测试\n典型场景分析"),
    ]
    x_positions = [110, 400, 690, 980, 1270]
    for idx, ((title, body), x) in enumerate(zip(boxes, x_positions), 1):
        rounded_panel(draw, (x, 310, x + 210, 560), fill=style["panel"], outline=style["line"], width=2, radius=22)
        draw_text(draw, (x + 24, 340), f"0{idx}", load_font(22, bold=True), style["accent"])
        draw_text(draw, (x + 24, 388), title, load_font(28, bold=True), style["title"])
        draw_text(draw, (x + 24, 462), body, load_font(24), style["text"], spacing=14)
        if idx < len(boxes):
            draw.line((x + 210, 435, x + 290, 435), fill=style["primary"], width=5)
            draw.polygon([(x + 290, 435), (x + 270, 423), (x + 270, 447)], fill=style["primary"])

    rounded_panel(draw, (110, 650, 1490, 780), fill=alpha(style["primary"], 14), outline=alpha(style["primary"], 60), width=2, radius=18)
    draw_text(draw, (138, 688), "页面建议：中间可替换为技术路线图、系统流程图或方法框架图；下方摘要区用于概括研究逻辑。", load_font(24), style["text"])
    add_footer(draw, style, "研究框架页", 4)
    return img


def result_page(style: Dict) -> Image.Image:
    img = Image.new("RGBA", (W, H), style["bg"])
    draw = ImageDraw.Draw(img)
    style["inner_bg"](draw, img, style)
    draw_text(draw, (104, 88), "实验结果与分析", load_font(42, bold=True), style["title"])
    draw_text(draw, (104, 142), "Results / Visualization / Comparison", load_font(20), style["accent"])

    rounded_panel(draw, (104, 214, 920, 760), fill=style["panel"], outline=style["line"], width=2, radius=18)
    rounded_panel(draw, (960, 214, 1494, 470), fill=style["panel"], outline=style["line"], width=2, radius=18)
    rounded_panel(draw, (960, 504, 1494, 760), fill=style["panel"], outline=style["line"], width=2, radius=18)

    # line chart
    chart_left, chart_top, chart_right, chart_bottom = 150, 300, 870, 700
    for i in range(6):
        y = chart_top + i * ((chart_bottom - chart_top) // 5)
        draw.line((chart_left, y, chart_right, y), fill=alpha(style["line"], 110), width=1)
    for i in range(7):
        x = chart_left + i * ((chart_right - chart_left) // 6)
        draw.line((x, chart_top, x, chart_bottom), fill=alpha(style["line"], 70), width=1)
    pts = [(chart_left + i * 110, chart_bottom - int(v)) for i, v in enumerate([70, 120, 210, 180, 260, 235, 315])]
    draw.line(pts, fill=style["primary"], width=5)
    for p in pts:
        draw.ellipse((p[0] - 6, p[1] - 6, p[0] + 6, p[1] + 6), fill=style["accent"])
    draw_text(draw, (150, 240), "队列稳定性趋势", load_font(28, bold=True), style["title"])
    draw_text(draw, (150, 718), "示意：左侧适合放折线图、散点图或轨迹图。", load_font(22), style["muted"])

    # table
    draw_text(draw, (992, 244), "关键指标对比", load_font(28, bold=True), style["title"])
    cols = ["指标", "方案 A", "方案 B"]
    data = [
        ("平均车距误差", "1.84 m", "1.22 m"),
        ("预警识别率", "89.6%", "93.8%"),
        ("平均响应延迟", "0.41 s", "0.27 s"),
        ("系统帧率", "22 fps", "28 fps"),
    ]
    x0, y0 = 992, 298
    col_w = [170, 130, 130]
    row_h = 38
    for i, c in enumerate(cols):
        draw.rectangle((x0 + sum(col_w[:i]), y0, x0 + sum(col_w[: i + 1]), y0 + row_h), fill=alpha(style["primary"], 24), outline=style["line"], width=1)
        draw_text(draw, (x0 + sum(col_w[:i]) + 18, y0 + 8), c, load_font(20, bold=True), style["title"])
    for r, row in enumerate(data, 1):
        y = y0 + r * row_h
        for i, val in enumerate(row):
            draw.rectangle((x0 + sum(col_w[:i]), y, x0 + sum(col_w[: i + 1]), y + row_h), fill=(255, 255, 255, 220), outline=style["line"], width=1)
            draw_text(draw, (x0 + sum(col_w[:i]) + 18, y + 8), val, load_font(19), style["text"])

    # insights
    draw_text(draw, (992, 536), "结果解读", load_font(28, bold=True), style["title"])
    bullets = [
        "系统可稳定完成多车轨迹回放与异常定位",
        "双通道预警机制提升了问题识别效率",
        "界面联动保证了时间跳转后的状态一致性",
    ]
    yy = 592
    for b in bullets:
        draw.ellipse((996, yy + 10, 1008, yy + 22), fill=style["primary"])
        draw_text(draw, (1028, yy), b, load_font(22), style["text"])
        yy += 54

    add_footer(draw, style, "实验结果页", 5)
    return img


def summary_page(style: Dict) -> Image.Image:
    img = Image.new("RGBA", (W, H), style["bg"])
    draw = ImageDraw.Draw(img)
    style["inner_bg"](draw, img, style)
    draw_text(draw, (104, 88), "结论与展望", load_font(42, bold=True), style["title"])
    draw_text(draw, (104, 142), "Conclusion / Innovation / Future Work", load_font(20), style["accent"])

    rounded_panel(draw, (104, 220, 740, 760), fill=style["panel"], outline=style["line"], width=2, radius=18)
    rounded_panel(draw, (778, 220, 1494, 460), fill=style["panel"], outline=style["line"], width=2, radius=18)
    rounded_panel(draw, (778, 500, 1494, 760), fill=style["panel"], outline=style["line"], width=2, radius=18)

    draw_text(draw, (136, 258), "研究结论", load_font(30, bold=True), style["title"])
    conclusion = [
        "完成了从原始队列数据到动态可视化分析的闭环实现",
        "验证了分层架构在系统稳定性与可扩展性上的有效性",
        "证明了系统可服务于异常复盘、教学展示与方法验证",
    ]
    yy = 330
    for c in conclusion:
        draw.rectangle((140, yy + 12, 152, yy + 24), fill=style["accent"])
        draw_text(draw, (176, yy), c, load_font(24), style["text"])
        yy += 90

    draw_text(draw, (810, 258), "创新点", load_font(30, bold=True), style["title"])
    draw_text(draw, (810, 328), "1. 数据处理、状态判别与可视化联动的一体化实现\n2. 面向卡车队列场景的双通道预警展示机制\n3. 面向答辩与研究场景的高可读页面体系", load_font(22), style["text"], spacing=18)

    draw_text(draw, (810, 538), "未来工作", load_font(30, bold=True), style["title"])
    draw_text(draw, (810, 608), "接入更多实测场景数据\n扩展交互分析与统计对比能力\n探索 Web 化与三维化展示方式", load_font(22), style["text"], spacing=18)

    add_footer(draw, style, "总结页", 6)
    return img


def make_overview(images: List[Image.Image], style: Dict) -> Image.Image:
    gap = 40
    thumb_w, thumb_h = 900, 506
    canvas = Image.new("RGBA", (2 * thumb_w + 3 * gap, 3 * thumb_h + 4 * gap + 120), (245, 247, 250, 255))
    draw = ImageDraw.Draw(canvas)
    draw_text(draw, (gap, 30), f"{style['name']} | 6类页面总览", load_font(42, bold=True), rgb("#1C2430"))
    draw_text(draw, (gap, 82), style["tagline"], load_font(24), rgb("#5B6575"))
    labels = ["封面页", "目录页", "章节页", "研究框架页", "实验结果页", "总结页"]
    for idx, img in enumerate(images):
        r, c = divmod(idx, 2)
        x = gap + c * (thumb_w + gap)
        y = 120 + gap + r * (thumb_h + gap)
        thumb = img.resize((thumb_w, thumb_h), Image.LANCZOS)
        canvas.alpha_composite(thumb, (x, y))
        draw.rounded_rectangle((x, y, x + thumb_w, y + thumb_h), radius=18, outline=(210, 216, 224), width=2)
        draw_text(draw, (x + 20, y + 16), labels[idx], load_font(22, bold=True), rgb("#334155"))
    return canvas


def stable_cover_bg(draw, img, style):
    draw.rectangle((0, 0, W, H), fill=style["bg"])
    draw.rectangle((0, 0, W, 120), fill=style["primary"])
    draw.rectangle((0, H - 120, W, H), fill=alpha(style["primary"], 10))
    draw.line((0, 122, W, 122), fill=style["accent"], width=4)


def stable_inner_bg(draw, img, style):
    draw.rectangle((0, 0, W, H), fill=style["bg"])
    draw.rectangle((0, 0, W, 84), fill=alpha(style["primary"], 7))
    draw.line((96, 176, W - 96, 176), fill=style["line"], width=2)


def stable_chapter_bg(draw, img, style):
    stable_inner_bg(draw, img, style)
    draw.rectangle((0, 200, 86, H), fill=style["primary"])


def modern_cover_bg(draw, img, style):
    draw.rectangle((0, 0, W, H), fill=style["bg"])
    draw.rectangle((0, 0, 86, H), fill=style["primary"])
    draw.rectangle((120, 120, 1120, 740), fill=alpha(style["primary"], 6))


def modern_inner_bg(draw, img, style):
    draw.rectangle((0, 0, W, H), fill=style["bg"])
    draw.rectangle((0, 0, 72, H), fill=style["primary"])
    draw.line((118, 176, W - 100, 176), fill=style["line"], width=2)


def modern_chapter_bg(draw, img, style):
    modern_inner_bg(draw, img, style)
    draw.rectangle((1160, 0, W, H), fill=alpha(style["primary"], 10))


def tech_cover_bg(draw, img, style):
    draw.rectangle((0, 0, W, H), fill=style["bg"])
    for x in range(0, W, 48):
        draw.line((x, 0, x, H), fill=alpha(style["line"], 80), width=1)
    for y in range(0, H, 48):
        draw.line((0, y, W, y), fill=alpha(style["line"], 80), width=1)
    draw.rectangle((0, 0, W, 110), fill=alpha(style["primary"], 30))


def tech_inner_bg(draw, img, style):
    tech_cover_bg(draw, img, style)
    draw.rectangle((0, 0, W, 84), fill=alpha(style["primary"], 18))
    draw.line((96, 176, W - 96, 176), fill=style["accent"], width=2)


def tech_chapter_bg(draw, img, style):
    tech_inner_bg(draw, img, style)
    draw.rectangle((1010, 180, 1520, 760), fill=alpha(style["primary"], 12), outline=alpha(style["accent"], 110), width=2)


def airy_cover_bg(draw, img, style):
    draw.rectangle((0, 0, W, H), fill=style["bg"])
    draw.rounded_rectangle((60, 50, 1540, 850), radius=36, outline=alpha(style["primary"], 60), width=2, fill=alpha(style["primary"], 4))
    draw.rectangle((0, 0, W, 140), fill=alpha(style["primary"], 12))


def airy_inner_bg(draw, img, style):
    draw.rectangle((0, 0, W, H), fill=style["bg"])
    draw.rectangle((0, 0, W, 84), fill=alpha(style["primary"], 9))
    draw.rounded_rectangle((72, 112, 1528, 818), radius=26, outline=alpha(style["primary"], 38), width=2)


def airy_chapter_bg(draw, img, style):
    airy_inner_bg(draw, img, style)
    draw.rounded_rectangle((1080, 160, 1480, 760), radius=28, fill=alpha(style["primary"], 12), outline=alpha(style["primary"], 60), width=2)


STYLES: List[Dict] = [
    {
        "name": "稳重学术型",
        "tagline": "深蓝主导，秩序感强，适合偏传统正式的答辩场景。",
        "bg": rgb("#F6F8FB"),
        "panel": (255, 255, 255, 240),
        "primary": "#123A78",
        "title": rgb("#16315F"),
        "text": rgb("#334155"),
        "muted": rgb("#64748B"),
        "accent": rgb("#6B8FCF"),
        "line": (196, 209, 228),
        "cover_bg": stable_cover_bg,
        "inner_bg": stable_inner_bg,
        "chapter_bg": stable_chapter_bg,
    },
    {
        "name": "现代简约型",
        "tagline": "大留白与左侧识别栏结合，版面干净，最方便后续套用。",
        "bg": rgb("#FBFCFE"),
        "panel": (255, 255, 255, 248),
        "primary": "#1B4B8F",
        "title": rgb("#1E293B"),
        "text": rgb("#475569"),
        "muted": rgb("#64748B"),
        "accent": rgb("#4C83D5"),
        "line": (210, 220, 233),
        "cover_bg": modern_cover_bg,
        "inner_bg": modern_inner_bg,
        "chapter_bg": modern_chapter_bg,
    },
    {
        "name": "科技理性型",
        "tagline": "强调结构化网格和数据感，适合系统、算法、实验类答辩。",
        "bg": rgb("#F2F6FB"),
        "panel": (248, 251, 255, 238),
        "primary": "#173A6E",
        "title": rgb("#183153"),
        "text": rgb("#314256"),
        "muted": rgb("#617487"),
        "accent": rgb("#2E6CC4"),
        "line": (200, 214, 230),
        "cover_bg": tech_cover_bg,
        "inner_bg": tech_inner_bg,
        "chapter_bg": tech_chapter_bg,
    },
    {
        "name": "高级清爽型",
        "tagline": "浅底蓝灰、柔和分区，正式里带一点现代感，观感最轻盈。",
        "bg": rgb("#FAFCFF"),
        "panel": (255, 255, 255, 245),
        "primary": "#24508B",
        "title": rgb("#22324A"),
        "text": rgb("#4A5C72"),
        "muted": rgb("#6E7E92"),
        "accent": rgb("#7EA4DA"),
        "line": (214, 223, 236),
        "cover_bg": airy_cover_bg,
        "inner_bg": airy_inner_bg,
        "chapter_bg": airy_chapter_bg,
    },
]


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for style in STYLES:
        style_dir = OUT_DIR / style["name"]
        style_dir.mkdir(parents=True, exist_ok=True)
        pages = [
            cover_page(style),
            toc_page(style),
            chapter_page(style),
            framework_page(style),
            result_page(style),
            summary_page(style),
        ]
        file_names = [
            "01_cover.png",
            "02_contents.png",
            "03_chapter.png",
            "04_framework.png",
            "05_results.png",
            "06_summary.png",
        ]
        for page, fn in zip(pages, file_names):
            page.save(style_dir / fn)
        overview = make_overview(pages, style)
        overview.save(OUT_DIR / f"{style['name']}_总览.png")


if __name__ == "__main__":
    main()
