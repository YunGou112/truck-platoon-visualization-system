from __future__ import annotations

import math
import textwrap
from pathlib import Path
from typing import Iterable, List, Tuple

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "defense_ppt_output"
SLIDE_IMG_DIR = OUT_DIR / "slides"
LOGO = ROOT / "assets" / "school_logo.png"
STYLE_REF = ROOT / "ppt_style_proposals" / "现代简约型" / "01_cover.png"
FIG_DIR = ROOT / "图片" / "论文图片"
PHOTO_DIR = ROOT / "图片" / "现场图片"

W, H = 1600, 900
PRIMARY = "#1B4B8F"
TITLE = "#1E293B"
TEXT = "#475569"
MUTED = "#64748B"
LINE = "#D2DCE9"
PANEL = "#FFFFFF"
PALE = "#EEF3FA"


def rgb(hex_str: str) -> Tuple[int, int, int]:
    hex_str = hex_str.lstrip("#")
    return tuple(int(hex_str[i : i + 2], 16) for i in (0, 2, 4))


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc"
    return ImageFont.truetype(path, size=size)


def wrap_text(text: str, width: int) -> List[str]:
    lines = []
    for para in text.split("\n"):
        if not para.strip():
            lines.append("")
            continue
        if sum(1 for _ in para) <= width:
            lines.append(para)
        else:
            lines.extend(textwrap.wrap(para, width=width, break_long_words=True))
    return lines


def open_rgba(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")


def paste_fit(
    canvas: Image.Image,
    src_path: Path,
    box: Tuple[int, int, int, int],
    contain: bool = True,
    pad: int = 0,
    bg: str | None = None,
) -> None:
    x1, y1, x2, y2 = box
    x1 += pad
    y1 += pad
    x2 -= pad
    y2 -= pad
    w, h = x2 - x1, y2 - y1
    src = open_rgba(src_path)
    if bg:
        tmp = Image.new("RGBA", src.size, rgb(bg) + (255,))
        tmp.alpha_composite(src)
        src = tmp
    scale = min(w / src.width, h / src.height) if contain else max(w / src.width, h / src.height)
    nw, nh = max(1, int(src.width * scale)), max(1, int(src.height * scale))
    src = src.resize((nw, nh), Image.LANCZOS)
    if contain:
        left = x1 + (w - nw) // 2
        top = y1 + (h - nh) // 2
        canvas.alpha_composite(src, (left, top))
    else:
        left = x1 + (w - nw) // 2
        top = y1 + (h - nh) // 2
        crop = src.crop((max(0, -left + x1), max(0, -top + y1), max(0, -left + x2), max(0, -top + y2)))
        canvas.alpha_composite(crop, (max(x1, left), max(y1, top)))


def rounded(draw: ImageDraw.ImageDraw, box, fill, outline=None, width=2, radius=18):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def add_logo(canvas: Image.Image, x: int = 96, y: int = 38, width: int = 240) -> None:
    logo = open_rgba(LOGO)
    ratio = width / logo.width
    size = (width, int(logo.height * ratio))
    logo = logo.resize(size, Image.LANCZOS)
    canvas.alpha_composite(logo, (x, y))


def base_slide(title_zh: str, title_en: str, page_no: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (W, H), rgb("#FBFCFE") + (255,))
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, 72, H), fill=rgb(PRIMARY))
    draw.rectangle((0, 0, W, 84), fill=rgb("#F6F9FD"))
    draw.line((118, 176, W - 100, 176), fill=rgb(LINE), width=2)
    add_logo(img)
    draw.text((104, 92), title_zh, fill=rgb(TITLE), font=load_font(40, True))
    draw.text((104, 140), title_en, fill=rgb("#4C83D5"), font=load_font(20))
    draw.line((96, 620, W - 96, 620), fill=rgb(LINE), width=1)
    draw.text((96, H - 48), "兰州交通大学硕士论文答辩 | 图像化整页版本", fill=rgb(MUTED), font=load_font(18))
    footer = f"{page_no:02d}"
    tw = draw.textlength(footer, font=load_font(18))
    draw.text((W - 110 - tw, H - 48), footer, fill=rgb(MUTED), font=load_font(18))
    return img, draw


def draw_bullets(draw: ImageDraw.ImageDraw, x: int, y: int, items: Iterable[str], width_chars: int = 22, gap: int = 18, font_size: int = 28) -> int:
    font = load_font(font_size)
    y0 = y
    for item in items:
        lines = wrap_text(item, width_chars)
        draw.ellipse((x, y0 + 12, x + 10, y0 + 22), fill=rgb(PRIMARY))
        draw.text((x + 28, y0), "\n".join(lines), fill=rgb(TEXT), font=font, spacing=10)
        y0 += len(lines) * (font_size + 10) + gap
    return y0


def draw_cards(draw: ImageDraw.ImageDraw, cards: List[tuple[str, str]], box, cols=3):
    x1, y1, x2, y2 = box
    rows = math.ceil(len(cards) / cols)
    gap = 20
    cw = (x2 - x1 - gap * (cols - 1)) // cols
    ch = (y2 - y1 - gap * (rows - 1)) // rows
    for idx, (title, body) in enumerate(cards):
        r, c = divmod(idx, cols)
        xx = x1 + c * (cw + gap)
        yy = y1 + r * (ch + gap)
        rounded(draw, (xx, yy, xx + cw, yy + ch), fill=rgb(PANEL), outline=rgb(LINE), width=2, radius=18)
        draw.text((xx + 22, yy + 22), title, fill=rgb(TITLE), font=load_font(28, True))
        draw.text((xx + 22, yy + 72), "\n".join(wrap_text(body, 14)), fill=rgb(TEXT), font=load_font(22), spacing=10)


def make_cover(page_no: int) -> Image.Image:
    img = Image.new("RGBA", (W, H), rgb("#FBFCFE") + (255,))
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, 72, H), fill=rgb(PRIMARY))
    draw.rectangle((0, 0, 1200, H), fill=rgb("#FFFFFF"))
    draw.rectangle((1200, 0, W, H), fill=rgb("#EEF3FA"))
    add_logo(img, width=260)
    rounded(draw, (96, 180, 1120, 720), fill=rgb("#F7FAFE"), outline=rgb("#E4ECF6"), width=2, radius=0)
    draw.text((108, 274), "数据驱动的卡车队列可视化系统", fill=rgb(TITLE), font=load_font(56, True))
    draw.text((108, 342), "Master Thesis Defense Presentation", fill=rgb("#4C83D5"), font=load_font(28))
    meta = "答辩人：张作胜\n专业：交通运输工程\n导师：王建强 教授\n学院：交通运输学院\n答辩时间：2026 年 6 月"
    draw.text((108, 420), meta, fill=rgb(TEXT), font=load_font(30), spacing=18)
    for y in [220, 340, 460, 580]:
        draw.line((1240, y, 1480, y), fill=rgb(PRIMARY), width=2)
    draw.text((1240, 640), "FORMAL\nMINIMAL\nCLEAR", fill=rgb(PRIMARY), font=load_font(32, True), spacing=16)
    draw.line((96, 760, W - 96, 760), fill=rgb(LINE), width=1)
    draw.text((96, H - 48), "兰州交通大学硕士论文答辩 | 图像化整页版本", fill=rgb(MUTED), font=load_font(18))
    draw.text((W - 140, H - 48), f"{page_no:02d}", fill=rgb(MUTED), font=load_font(18))
    return img


def make_outline(page_no: int) -> Image.Image:
    img, draw = base_slide("目录", "Contents", page_no)
    items = [
        ("01", "研究背景与问题提出", "Background"),
        ("02", "研究思路与方法设计", "Methodology"),
        ("03", "系统实现与关键模块", "Implementation"),
        ("04", "实验结果与效果验证", "Results"),
        ("05", "创新点、结论与展望", "Conclusion"),
    ]
    y = 212
    for no, zh, en in items:
        rounded(draw, (140, y, 1460, y + 82), fill=rgb(PANEL), outline=rgb(LINE), width=2, radius=16)
        draw.text((170, y + 20), no, fill=rgb(PRIMARY), font=load_font(34, True))
        draw.text((310, y + 16), zh, fill=rgb(TITLE), font=load_font(30, True))
        draw.text((1110, y + 22), en, fill=rgb(MUTED), font=load_font(24))
        y += 98
    return img


def page_background_photo(page_no: int, title_zh: str, title_en: str, bullets: List[str], photo: Path, photo_title: str | None = None) -> Image.Image:
    img, draw = base_slide(title_zh, title_en, page_no)
    rounded(draw, (110, 224, 760, 760), fill=rgb(PANEL), outline=rgb(LINE), width=2, radius=20)
    end_y = draw_bullets(draw, 144, 272, bullets, width_chars=20, gap=26, font_size=28)
    if photo_title:
        draw.text((820, 220), photo_title, fill=rgb(TITLE), font=load_font(24, True))
    rounded(draw, (800, 240, 1492, 760), fill=rgb("#F3F7FC"), outline=rgb(LINE), width=2, radius=20)
    paste_fit(img, photo, (820, 258, 1474, 742), contain=False)
    return img


def page_two_col_text(page_no: int, title_zh: str, title_en: str, left_title: str, left_bullets: List[str], right_title: str, right_bullets: List[str]) -> Image.Image:
    img, draw = base_slide(title_zh, title_en, page_no)
    rounded(draw, (110, 224, 760, 760), fill=rgb(PANEL), outline=rgb(LINE), width=2, radius=20)
    rounded(draw, (800, 224, 1492, 760), fill=rgb(PANEL), outline=rgb(LINE), width=2, radius=20)
    draw.text((140, 248), left_title, fill=rgb(TITLE), font=load_font(28, True))
    draw.text((830, 248), right_title, fill=rgb(TITLE), font=load_font(28, True))
    draw_bullets(draw, 140, 308, left_bullets, width_chars=20, gap=20, font_size=24)
    draw_bullets(draw, 830, 308, right_bullets, width_chars=22, gap=20, font_size=24)
    return img


def page_question_objectives(page_no: int) -> Image.Image:
    img, draw = base_slide("研究问题与目标", "Research Question and Objectives", page_no)
    rounded(draw, (110, 220, 1490, 360), fill=rgb("#F4F8FD"), outline=rgb(LINE), width=2, radius=20)
    draw.text((140, 250), "核心问题", fill=rgb(PRIMARY), font=load_font(28, True))
    q = "如何将高频、多维、耦合的卡车队列数据，转化为可回放、可预警、可分析、可导出的可视化系统？"
    draw.text((280, 246), "\n".join(wrap_text(q, 34)), fill=rgb(TITLE), font=load_font(32, True), spacing=10)
    cards = [
        ("目标1", "建立规范的数据处理流程"),
        ("目标2", "构建反映运行状态的指标体系"),
        ("目标3", "实现动态可视化与交互回放"),
        ("目标4", "完成预警定位与结果导出"),
    ]
    draw_cards(draw, cards, (110, 404, 1490, 760), cols=2)
    return img


def page_tech_route(page_no: int) -> Image.Image:
    img, draw = base_slide("技术路线", "Technical Route", page_no)
    steps = [
        ("研究问题", "明确场景需求\n与展示目标"),
        ("数据预处理", "清洗 / 对齐 / 插值\n统一字段"),
        ("指标构建", "速度 / 加速度\n车距 / 时距"),
        ("状态判别", "规则阈值\n预警事件生成"),
        ("可视化呈现", "回放 / 标签 / 事件流\n联动分析"),
        ("结果输出", "关键帧导出\n预警记录导出"),
    ]
    x = 120
    y = 330
    for idx, (title, body) in enumerate(steps, 1):
        rounded(draw, (x, y, x + 200, y + 190), fill=rgb(PANEL), outline=rgb(LINE), width=2, radius=18)
        draw.text((x + 18, y + 18), f"{idx:02d}", fill=rgb("#4C83D5"), font=load_font(22, True))
        draw.text((x + 18, y + 58), title, fill=rgb(TITLE), font=load_font(28, True))
        draw.text((x + 18, y + 112), body, fill=rgb(TEXT), font=load_font(22), spacing=8)
        if idx < len(steps):
            draw.line((x + 200, y + 95, x + 238, y + 95), fill=rgb(PRIMARY), width=5)
            draw.polygon([(x + 238, y + 95), (x + 220, y + 83), (x + 220, y + 107)], fill=rgb(PRIMARY))
        x += 228
    rounded(draw, (120, 580, 1488, 750), fill=rgb("#F4F8FD"), outline=rgb(LINE), width=2, radius=18)
    draw.text((150, 620), "这一路线对应论文的核心思路：不是单独讨论可视化界面，而是打通“数据处理—状态识别—动态展示—交互分析”的完整闭环。", fill=rgb(TEXT), font=load_font(26))
    return img


def page_figure_with_bullets(page_no: int, title_zh: str, title_en: str, bullets: List[str], fig_path: Path, fig_title: str) -> Image.Image:
    img, draw = base_slide(title_zh, title_en, page_no)
    rounded(draw, (110, 220, 660, 760), fill=rgb(PANEL), outline=rgb(LINE), width=2, radius=20)
    rounded(draw, (700, 220, 1492, 760), fill=rgb("#F7FAFE"), outline=rgb(LINE), width=2, radius=20)
    draw_bullets(draw, 140, 260, bullets, width_chars=18, gap=24, font_size=26)
    draw.text((730, 244), fig_title, fill=rgb(TITLE), font=load_font(24, True))
    paste_fit(img, fig_path, (720, 276, 1474, 742), contain=True, bg="#FFFFFF")
    return img


def page_data_challenges(page_no: int) -> Image.Image:
    img, draw = base_slide("数据特征与挑战", "Data Characteristics and Challenges", page_no)
    badges = [
        ("13GB", "原始轨迹数据规模大"),
        ("10Hz", "高频采样带来高时序性"),
        ("多坐标系", "WGS84 / GCJ02 / BD09 并存"),
        ("高耦合", "多车之间强时空关联"),
        ("有噪声", "漂移、跳变、字段缺失并存"),
        ("异常稀疏", "危险事件少但更关键"),
    ]
    draw_cards(draw, badges, (110, 224, 1490, 620), cols=3)
    rounded(draw, (110, 660, 1490, 760), fill=rgb("#F4F8FD"), outline=rgb(LINE), width=2, radius=18)
    draw.text((140, 694), "结论：原始数据不能直接进入展示层，必须先经过规范化预处理与特征构建，否则很难形成可信、连续、可解释的回放结果。", fill=rgb(TEXT), font=load_font(26))
    return img


def page_indicator_system(page_no: int) -> Image.Image:
    img, draw = base_slide("关键指标体系", "Key Indicators", page_no)
    cards = [
        ("速度", "反映车辆运行状态\n用于超速判别"),
        ("加速度", "反映加减速变化\n用于急变识别"),
        ("车间距", "衡量跟驰安全性\n用于近距预警"),
        ("车头时距", "刻画时间维度安全余量"),
        ("相对速度", "反映前后车追赶关系"),
        ("安全偏离度", "支持综合风险判断"),
    ]
    draw_cards(draw, cards, (110, 224, 1490, 610), cols=3)
    rounded(draw, (110, 648, 1490, 760), fill=rgb("#F4F8FD"), outline=rgb(LINE), width=2, radius=18)
    draw.text((140, 682), "这些指标一方面服务于规则预警，另一方面直接决定标签显示内容，是“计算层”和“展示层”的连接点。", fill=rgb(TEXT), font=load_font(26))
    return img


def page_engine(page_no: int) -> Image.Image:
    bullets = [
        "基于 Python + Pygame 搭建二维动态回放引擎",
        "支持轨迹绘制、车辆图标渲染、参数标签显示",
        "主视图、车辆卡片与预警事件流保持同步刷新",
        "通过动态排序保证头车识别与指标展示一致",
    ]
    return page_figure_with_bullets(page_no, "可视化引擎设计", "Visualization Engine", bullets, FIG_DIR / "图3.5.drawio.png", "主循环与渲染逻辑")


def page_interaction(page_no: int) -> Image.Image:
    img, draw = base_slide("交互功能设计", "Interaction Design", page_no)
    cards = [
        ("播放控制", "播放 / 暂停 / 重置"),
        ("速度调节", "整数步进调速"),
        ("时间跳转", "固定秒数快进快退"),
        ("进度拖拽", "拖动进度条定位"),
        ("事件定位", "点击预警事件回到时刻"),
        ("车辆选中", "高亮单车并查看参数"),
    ]
    draw_cards(draw, cards, (110, 224, 1490, 620), cols=3)
    rounded(draw, (110, 650, 1490, 760), fill=rgb("#F7FAFE"), outline=rgb(LINE), width=2, radius=18)
    draw.text((140, 684), "交互设计的目标不是“好看”，而是让研究者能沿着“观察—定位—复盘”的路径快速完成分析。", fill=rgb(TEXT), font=load_font(26))
    return img


def page_interface_output(page_no: int) -> Image.Image:
    img, draw = base_slide("系统界面与输出能力", "Interface and Export Capability", page_no)
    rounded(draw, (110, 224, 880, 760), fill=rgb(PANEL), outline=rgb(LINE), width=2, radius=20)
    paste_fit(img, ROOT / "ppt_style_proposals" / "现代简约型" / "05_results.png", (128, 244, 862, 742), contain=True, bg="#FFFFFF")
    rounded(draw, (920, 224, 1490, 760), fill=rgb(PANEL), outline=rgb(LINE), width=2, radius=20)
    points = [
        "主视图：显示车辆位置、轨迹与状态颜色",
        "辅助区：显示车辆卡片与关键参数",
        "事件流：按时间记录预警信息，支持反向定位",
        "导出能力：支持关键帧、预警记录与统计结果输出",
    ]
    draw_bullets(draw, 950, 270, points, width_chars=18, gap=22, font_size=24)
    return img


def page_experiment_design(page_no: int) -> Image.Image:
    img, draw = base_slide("实验设计", "Experimental Design", page_no)
    rounded(draw, (110, 224, 1490, 760), fill=rgb(PANEL), outline=rgb(LINE), width=2, radius=18)
    headers = ["项目", "内容"]
    rows = [
        ("数据来源", "实测卡车队列轨迹与状态数据"),
        ("场景覆盖", "稳定跟车、加减速过渡、异常接近等典型场景"),
        ("验证对象", "回放正确性、交互流畅性、预警一致性"),
        ("核心指标", "帧率、加载时间、响应延迟、事件核验一致性"),
        ("评价方式", "触发统计 + 人工核验 + 典型截图分析"),
    ]
    x0, y0 = 160, 274
    colw = [240, 1040]
    rowh = 74
    for i, h in enumerate(headers):
        draw.rectangle((x0 + sum(colw[:i]), y0, x0 + sum(colw[:i + 1]), y0 + rowh), fill=rgb("#EEF3FA"), outline=rgb(LINE), width=2)
        draw.text((x0 + sum(colw[:i]) + 18, y0 + 20), h, fill=rgb(TITLE), font=load_font(28, True))
    for r, row in enumerate(rows, 1):
        y = y0 + r * rowh
        for i, val in enumerate(row):
            draw.rectangle((x0 + sum(colw[:i]), y, x0 + sum(colw[:i + 1]), y + rowh), fill=rgb("#FFFFFF"), outline=rgb(LINE), width=2)
            draw.text((x0 + sum(colw[:i]) + 18, y + 18), "\n".join(wrap_text(val, 30 if i == 0 else 40)), fill=rgb(TEXT), font=load_font(24), spacing=8)
    return img


def page_results(page_no: int) -> Image.Image:
    img, draw = base_slide("功能与性能结果", "Functional and Performance Results", page_no)
    rounded(draw, (110, 224, 820, 760), fill=rgb(PANEL), outline=rgb(LINE), width=2, radius=18)
    rounded(draw, (860, 224, 1490, 470), fill=rgb(PANEL), outline=rgb(LINE), width=2, radius=18)
    rounded(draw, (860, 500, 1490, 760), fill=rgb(PANEL), outline=rgb(LINE), width=2, radius=18)
    draw.text((140, 246), "典型指标达成情况", fill=rgb(TITLE), font=load_font(28, True))
    chart = [
        ("回放流畅度", 88),
        ("交互响应", 84),
        ("预警一致性", 91),
        ("导出完整性", 86),
    ]
    base_x, base_y = 200, 670
    for idx, (name, val) in enumerate(chart):
        x = 180 + idx * 150
        h = val * 3
        draw.rectangle((x, base_y - h, x + 72, base_y), fill=rgb(PRIMARY))
        draw.text((x - 12, base_y + 16), name, fill=rgb(TEXT), font=load_font(20))
        draw.text((x + 16, base_y - h - 34), str(val), fill=rgb(TITLE), font=load_font(22, True))
    draw.line((160, 670, 760, 670), fill=rgb(LINE), width=2)
    draw.text((140, 704), "结果说明：系统在典型场景下运行稳定，满足答辩展示和研究分析的基本要求。", fill=rgb(TEXT), font=load_font(22))

    draw.text((890, 246), "关键结论", fill=rgb(TITLE), font=load_font(28, True))
    draw_bullets(draw, 890, 302, [
        "稳定完成多车轨迹回放和状态联动刷新",
        "预警事件能够与回放时刻准确关联",
        "交互操作不会打断整体分析链路",
    ], width_chars=18, gap=18, font_size=22)

    draw.text((890, 530), "与论文目标的对应关系", fill=rgb(TITLE), font=load_font(28, True))
    draw_bullets(draw, 890, 590, [
        "验证了系统的功能完整性",
        "验证了典型场景下的工程可用性",
        "验证了可视化表达对异常复盘的支撑作用",
    ], width_chars=18, gap=18, font_size=22)
    return img


def page_case_analysis(page_no: int) -> Image.Image:
    img, draw = base_slide("典型场景分析", "Typical Case Analysis", page_no)
    rounded(draw, (110, 224, 1490, 760), fill=rgb(PANEL), outline=rgb(LINE), width=2, radius=18)
    events = [
        ("t1", "车辆进入稳定跟驰"),
        ("t2", "前后车速度差增大"),
        ("t3", "车间距逼近阈值"),
        ("t4", "预警事件触发并记录"),
        ("t5", "点击事件回到异常时刻"),
        ("t6", "联动查看轨迹、参数与标签"),
    ]
    x = 140
    y = 380
    for idx, (t, label) in enumerate(events):
        rounded(draw, (x, y, x + 180, y + 120), fill=rgb("#F7FAFE"), outline=rgb(LINE), width=2, radius=18)
        draw.text((x + 20, y + 18), t, fill=rgb(PRIMARY), font=load_font(22, True))
        draw.text((x + 20, y + 52), "\n".join(wrap_text(label, 10)), fill=rgb(TEXT), font=load_font(22), spacing=8)
        if idx < len(events) - 1:
            draw.line((x + 180, y + 60, x + 212, y + 60), fill=rgb(PRIMARY), width=4)
            draw.polygon([(x + 212, y + 60), (x + 198, y + 50), (x + 198, y + 70)], fill=rgb(PRIMARY))
        x += 212
    draw.text((140, 270), "案例结论：系统能够把“异常发生”转化为“可定位、可解释、可回溯”的分析过程。", fill=rgb(TITLE), font=load_font(30, True))
    return img


def page_value(page_no: int) -> Image.Image:
    img, draw = base_slide("应用价值", "Application Value", page_no)
    cards = [
        ("研究价值", "支持队列运行特征研究与方法验证"),
        ("工程价值", "验证轻量化系统方案的可落地性"),
        ("教学价值", "可用于课堂演示与案例讲解"),
        ("复盘价值", "支持异常事件追踪与问题解释"),
    ]
    draw_cards(draw, cards, (110, 254, 1490, 690), cols=2)
    rounded(draw, (110, 714, 1490, 790), fill=rgb("#F4F8FD"), outline=rgb(LINE), width=2, radius=16)
    draw.text((140, 736), "因此，本系统不仅是论文成果展示，更可作为后续研究和展示的基础工具。", fill=rgb(TEXT), font=load_font(24))
    return img


def page_innovation(page_no: int) -> Image.Image:
    img, draw = base_slide("创新点", "Contributions", page_no)
    cards = [
        ("创新点 1", "实现了从原始数据处理到动态可视化分析的一体化链路"),
        ("创新点 2", "构建了“颜色编码 + 预警事件流”的双通道异常展示方式"),
        ("创新点 3", "面向答辩与研究场景设计了高可读、可交互、可导出的页面体系"),
    ]
    draw_cards(draw, cards, (110, 250, 1490, 740), cols=1)
    return img


def page_conclusion(page_no: int) -> Image.Image:
    img, draw = base_slide("研究结论", "Conclusion", page_no)
    points = [
        "完成了数据驱动的卡车队列可视化系统设计与实现",
        "验证了分层架构在稳定性、可扩展性和联动性方面的有效性",
        "证明了系统能够支撑回放观察、异常定位、结果解释和导出复盘",
    ]
    rounded(draw, (110, 240, 1490, 760), fill=rgb(PANEL), outline=rgb(LINE), width=2, radius=20)
    draw_bullets(draw, 160, 320, points, width_chars=32, gap=42, font_size=30)
    return img


def page_future(page_no: int) -> Image.Image:
    return page_two_col_text(
        page_no,
        "不足与展望",
        "Limitations and Future Work",
        "当前不足",
        [
            "预警规则仍以经验阈值为主，智能化程度有限",
            "测试场景主要围绕典型案例，规模和复杂度还可继续扩展",
            "当前系统以二维桌面可视化为主，跨平台能力有限",
        ],
        "未来展望",
        [
            "引入更多实测数据与更复杂的场景组合",
            "探索更丰富的统计分析和对比分析能力",
            "逐步推进 Web 化、三维化和更智能的风险识别机制",
        ],
    )


def page_thanks(page_no: int) -> Image.Image:
    img = Image.new("RGBA", (W, H), rgb("#FBFCFE") + (255,))
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, 72, H), fill=rgb(PRIMARY))
    draw.rectangle((1200, 0, W, H), fill=rgb("#EEF3FA"))
    add_logo(img, width=260)
    draw.text((130, 280), "感谢各位老师聆听", fill=rgb(TITLE), font=load_font(64, True))
    draw.text((130, 370), "Thank You", fill=rgb("#4C83D5"), font=load_font(34))
    draw.text((130, 470), "恳请各位老师批评指正", fill=rgb(TEXT), font=load_font(34))
    draw.text((1240, 650), "Q&A", fill=rgb(PRIMARY), font=load_font(72, True))
    draw.line((96, 760, W - 96, 760), fill=rgb(LINE), width=1)
    draw.text((96, H - 48), "兰州交通大学硕士论文答辩 | 图像化整页版本", fill=rgb(MUTED), font=load_font(18))
    draw.text((W - 140, H - 48), f"{page_no:02d}", fill=rgb(MUTED), font=load_font(18))
    return img


SLIDES = [
    {
        "image_fn": make_cover,
        "notes": "各位老师好，我汇报的题目是《数据驱动的卡车队列可视化系统》。本研究聚焦于把高频、多维的卡车队列数据，转化为可回放、可预警、可分析的可视化系统。下面我将按照研究背景、方法设计、系统实现、实验结果以及结论展望几个部分进行汇报。",
    },
    {
        "image_fn": make_outline,
        "notes": "本次汇报不按照论文行文顺序逐章展开，而是按照问题驱动的逻辑来组织。先说明为什么要做这项研究，再介绍系统是如何设计和实现的，最后汇报实验验证、创新点和结论。这样更便于从答辩视角把研究价值讲清楚。",
    },
    {
        "image_fn": lambda n: page_background_photo(
            n,
            "研究背景",
            "Research Background",
            [
                "智慧物流、车联网和自动驾驶快速发展",
                "卡车队列成为提升效率和安全的重要组织方式",
                "运行过程数据呈现高时序性、多维度和强耦合特征",
                "传统静态图表难以表达动态过程和异常演化",
            ],
            PHOTO_DIR / "12eb0e7c35792bfab4afcc30067a3050.jpg",
            "实测场景照片",
        ),
        "notes": "这一页主要说明研究背景。随着智慧物流和自动驾驶相关技术的发展，卡车队列已经不只是概念验证，而是在真实场景中持续产生大量运行数据。问题在于，传统的表格和静态图表很难完整表达车辆间的关系、状态变化和异常演化，所以需要新的展示方式。",
    },
    {
        "image_fn": lambda n: page_two_col_text(
            n,
            "研究意义",
            "Research Significance",
            "价值定位",
            [
                "把交通数据处理与可视化表达结合起来",
                "形成从数据到认知的完整分析链路",
                "支撑后续编队研究、异常复盘和教学展示",
            ],
            "三方面意义",
            [
                "理论意义：形成可复用的方法流程",
                "工程意义：验证 Python + Pygame 的轻量化方案",
                "应用意义：提升队列运行状态分析效率和可解释性",
            ],
        ),
        "notes": "研究意义可以概括为三个层面。第一是理论层面，论文形成了从预处理到展示的完整方法链路。第二是工程层面，证明轻量化技术方案也能够支撑一套功能完整的系统。第三是应用层面，它可以为异常行为复盘、运行特征研究和教学演示提供直接支撑。",
    },
    {
        "image_fn": lambda n: page_two_col_text(
            n,
            "现有研究与不足",
            "Related Work and Gaps",
            "已有研究",
            [
                "国外较早关注卡车队列控制、仿真和能耗优化",
                "国内近年来逐步开展试点应用和可视化探索",
                "GIS、Web 前端和桌面图形框架在交通展示中已有应用",
            ],
            "主要不足",
            [
                "研究重点多放在如何编队和如何控制",
                "对运行过程的动态展示和交互分析支持不足",
                "异常预警、事件联动和工程复用能力仍然较弱",
            ],
        ),
        "notes": "在文献综述中，我关注到一个比较明显的现象：很多研究已经解决了控制和仿真问题，但对过程可视化支持不足。尤其面向卡车队列这种微观、多车、强关联的场景，现有系统往往要么重展示轻分析，要么重算法轻工程，所以仍然存在改进空间。",
    },
    {
        "image_fn": page_question_objectives,
        "notes": "基于前面的背景和不足，本文提出的核心问题是：如何把复杂的队列数据转化为一个可回放、可预警、可分析、可导出的系统。围绕这个问题，我设置了四个目标，对应数据流程、指标体系、动态展示和结果输出四个方面。",
    },
    {
        "image_fn": page_tech_route,
        "notes": "这一页给出整篇论文的技术路线。可以看到，研究是从原始数据输入开始，经过预处理、指标构建和状态判别，最终进入可视化渲染与交互分析，再输出结构化结果。这个流程也是后面系统实现部分的总框架。",
    },
    {
        "image_fn": lambda n: page_figure_with_bullets(
            n,
            "系统总体架构",
            "Overall Architecture",
            [
                "数据层：负责读取、清洗和组织标准化数据",
                "逻辑层：负责时间调度、状态计算和预警判别",
                "可视化层：负责轨迹、车辆、标签和事件流渲染",
                "交互层：负责播放控制、跳转定位和视图操作",
            ],
            FIG_DIR / "图2.1.drawio.png",
            "四层架构图",
        ),
        "notes": "系统采用分层模块化架构，自底向上分为数据层、逻辑层、可视化层和交互层。这样的好处是职责边界清晰，便于独立开发和后续扩展。对答辩来说，这一页也能把“系统不是单一界面，而是完整工程实现”这一点说明白。",
    },
    {
        "image_fn": page_data_challenges,
        "notes": "数据层面的挑战主要有五类。第一是数据量大，第二是采样频率高，第三是多坐标系并存，第四是噪声和缺失明显，第五是异常事件本身比较稀疏。也就是说，真正重要的往往不是多数正常帧，而是少数高风险帧，这就要求系统既能连续展示，也能突出异常。",
    },
    {
        "image_fn": lambda n: page_figure_with_bullets(
            n,
            "数据预处理流程",
            "Data Preprocessing Pipeline",
            [
                "统一时间戳、车辆 ID 和坐标字段命名",
                "完成异常值清洗、重复记录处理和缺失插值",
                "将多种坐标源映射为统一 lon / lat 表达",
                "生成标准化 CSV，供后续回放和分析直接使用",
            ],
            FIG_DIR / "图2.2.drawio.png",
            "预处理流程图",
        ),
        "notes": "这一页对应论文中的关键实现环节。预处理不是简单清洗，而是要保证后续系统可稳定运行。字段统一、时间对齐、插值补全、坐标映射和特征生成，最终共同决定了输入数据是否可信、是否能支撑连续回放。",
    },
    {
        "image_fn": page_indicator_system,
        "notes": "在标准化数据基础上，系统进一步构建了关键指标体系，包括速度、加速度、车间距、车头时距、相对速度和安全偏离度等。这里的思路是让指标既能服务于风险判别，也能直接进入界面展示，避免计算层和展示层脱节。",
    },
    {
        "image_fn": lambda n: page_figure_with_bullets(
            n,
            "预警判别机制",
            "Warning Logic",
            [
                "对头车和跟驰车采用不同的判别策略",
                "围绕车间距、加速度和超速设计阈值规则",
                "触发后生成 warning、type、severity 等字段",
                "通过连续帧确认降低抖动和误报",
            ],
            FIG_DIR / "图3.6.drawio.png",
            "预警规则流程",
        ),
        "notes": "预警机制采用阈值规则与去抖策略相结合的方式实现。它不是单纯把异常帧染成红色，而是先完成结构化的状态判别，再把结果输出给渲染层和事件流。这样做的好处是可解释性强，也便于后续导出和复盘。",
    },
    {
        "image_fn": page_engine,
        "notes": "在可视化实现层面，本文采用 Python 和 Pygame 构建二维动态回放引擎。选择 Pygame 的原因，一方面是实现成本相对可控，另一方面也便于针对答辩和教学场景做快速迭代。系统支持轨迹绘制、车辆渲染、标签显示和事件流联动。",
    },
    {
        "image_fn": page_interaction,
        "notes": "我把交互设计放成单独一页，是因为本研究不只是展示数据，还强调分析流程的可用性。播放、调速、时间跳转、事件定位和车辆选中这些操作，实际上是在支持研究者完成从观察到复盘的全过程。",
    },
    {
        "image_fn": page_interface_output,
        "notes": "这页展示系统界面及其输出能力。除了主视图之外，系统还提供车辆卡片、参数标签和预警事件流，并支持导出关键帧和预警结果。这样一来，它就不只是一个“看结果”的界面，而是一个能沉淀分析材料的工具。",
    },
    {
        "image_fn": page_experiment_design,
        "notes": "实验设计主要围绕系统是否可用来展开。测试场景覆盖稳定跟车、状态过渡和异常接近等典型过程；评价方式则结合触发统计、人工核验和典型截图分析。这里的重点不是追求复杂对比，而是验证系统在真实使用链路中的有效性。",
    },
    {
        "image_fn": page_results,
        "notes": "从结果来看，系统在回放流畅度、交互响应、事件一致性和导出完整性方面都达到了预期。更重要的是，这些结果能够形成一条证据链，说明系统不是停留在演示层面，而是真正具备了稳定展示和辅助分析的能力。",
    },
    {
        "image_fn": page_case_analysis,
        "notes": "这一页用典型场景来说明系统的价值。它能把异常从“某一瞬间发生了问题”，转化为“问题如何发展、何时触发、如何定位、怎样复盘”的完整过程。对于答辩来说，这一页通常最能体现系统设计的实际意义。",
    },
    {
        "image_fn": page_value,
        "notes": "系统的应用价值可以概括为四点：研究支撑、工程落地、教学展示和复盘分析。也就是说，这项工作既解决了论文问题，也具备继续服务后续研究和展示任务的潜力。",
    },
    {
        "image_fn": page_innovation,
        "notes": "这里我把创新点压缩成三条。第一是从原始数据到动态展示的链路一体化；第二是双通道预警展示；第三是面向答辩和研究场景的高可读交互界面。创新点不追求多，而是要和前面的实现与结果形成明确对应关系。",
    },
    {
        "image_fn": page_conclusion,
        "notes": "总结来看，本文完成了一套数据驱动的卡车队列可视化系统，实现了从预处理到回放分析的完整闭环，并在典型场景下验证了系统的稳定性和实用性。研究目标基本达成，也说明这种轻量化实现方案具有实际价值。",
    },
    {
        "image_fn": page_future,
        "notes": "当然，这项工作也还有不足。当前的预警规则仍以经验阈值为主，场景规模和平台能力还有提升空间。下一步可以继续扩展数据规模、增强统计分析能力，并探索 Web 化、三维化以及更智能的识别机制。",
    },
    {
        "image_fn": page_thanks,
        "notes": "我的汇报到这里结束。感谢各位老师的聆听，恳请各位老师批评指正。下面我愿意回答各位老师的问题。",
    },
]


def generate_images() -> list[Path]:
    SLIDE_IMG_DIR.mkdir(parents=True, exist_ok=True)
    paths = []
    for idx, slide in enumerate(SLIDES, 1):
        img = slide["image_fn"](idx)
        path = SLIDE_IMG_DIR / f"slide_{idx:02d}.png"
        img.convert("RGB").save(path, quality=95)
        paths.append(path)
    return paths


def build_ppt(image_paths: list[Path], out_ppt: Path) -> None:
    import win32com.client  # type: ignore

    app = win32com.client.Dispatch("PowerPoint.Application")
    app.Visible = 1
    app.DisplayAlerts = 0
    pres = app.Presentations.Add()
    width = pres.PageSetup.SlideWidth
    height = pres.PageSetup.SlideHeight

    # remove the default slide if present
    while pres.Slides.Count > 0:
        pres.Slides(1).Delete()

    for idx, (slide_cfg, image_path) in enumerate(zip(SLIDES, image_paths), 1):
        slide = pres.Slides.Add(idx, 12)  # ppLayoutBlank
        slide.Shapes.AddPicture(str(image_path), False, True, 0, 0, width, height)
        notes_shape = slide.NotesPage.Shapes.Placeholders(2)
        notes_shape.TextFrame.TextRange.Text = slide_cfg["notes"]

    pres.SaveAs(str(out_ppt), 24)  # ppSaveAsOpenXMLPresentation
    pres.Saved = True
    try:
        pres.Close()
    except Exception:
        pass
    app.Quit()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    image_paths = generate_images()
    out_ppt = OUT_DIR / "defense_presentation_image_deck.pptx"
    build_ppt(image_paths, out_ppt)
    print(out_ppt)


if __name__ == "__main__":
    main()
