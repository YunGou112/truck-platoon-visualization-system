from __future__ import annotations

import math
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd
from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT / "projects" / "truck_platoon_bachelor_defense_ppt169_20260509"
EXPORT_DIR = PROJECT_DIR / "exports"
NOTES_DIR = PROJECT_DIR / "notes"
SLIDE_DIR = PROJECT_DIR / "rendered_refstyle_slides"
ASSET_DIR = PROJECT_DIR / "refstyle_assets"

LOGO = ROOT / "assets" / "school_logo.png"
FIELD_PHOTO = PROJECT_DIR / "images" / "field_photo.jpg"
UI_FULL = PROJECT_DIR / "images" / "image_024.jpg"
UI_GRID = PROJECT_DIR / "images" / "image_022.jpg"

FIG_ARCH = ROOT / "图片" / "论文图片" / "图2.1.drawio.png"
FIG_INTERACT = ROOT / "图片" / "论文图片" / "图2.3.drawio.png"
FIG_CLEAN = ROOT / "图片" / "论文图片" / "图3.1.drawio.png"
FIG_ALIGN = ROOT / "图片" / "论文图片" / "图3.2.drawio.png"
FIG_METRIC = ROOT / "图片" / "论文图片" / "图3.4.drawio.png"
FIG_COORD = ROOT / "图片" / "论文图片" / "图3.3.drawio.png"
FIG_RENDER = ROOT / "图片" / "论文图片" / "图4.1.drawio.png"

DATA_CSV = ROOT / "truck_platoon_viz" / "编队行驶数据" / "14mins_4trucks" / "platoon_data.csv"

OUT_PPT = EXPORT_DIR / "truck_platoon_bachelor_defense_refstyle_v2.pptx"
OUT_NOTES = NOTES_DIR / "refstyle_total.md"

W, H = 1600, 900
BG = "#F7F9FB"
WHITE = "#FFFFFF"
TEXT = "#243447"
MUTED = "#617181"
BORDER = "#D7E2EA"
TURQ = "#18AEC1"
TURQ_DARK = "#0C91A4"
NAV_DARK = "#134C65"
ACCENT = "#F59E0B"
RED = "#E75A5A"
GREEN = "#45B97C"
BLUE = "#4D7CFE"
PURPLE = "#8B5CF6"
INK = "#122235"


def rgb(hex_str: str) -> tuple[int, int, int]:
    hex_str = hex_str.lstrip("#")
    return tuple(int(hex_str[i : i + 2], 16) for i in (0, 2, 4))


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    font_path = r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc"
    return ImageFont.truetype(font_path, size=size)


def wrap_text(text: str, width: int) -> list[str]:
    lines: list[str] = []
    for para in text.split("\n"):
        if not para.strip():
            lines.append("")
        else:
            lines.extend(textwrap.wrap(para, width=width, break_long_words=True))
    return lines


def open_rgba(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")


def rounded(draw: ImageDraw.ImageDraw, box, fill, outline=None, width=2, radius=18):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def paste_cover(canvas: Image.Image, src_path: Path, box: tuple[int, int, int, int], bg: str | None = None) -> None:
    x1, y1, x2, y2 = box
    src = open_rgba(src_path)
    if bg:
        base = Image.new("RGBA", src.size, rgb(bg) + (255,))
        base.alpha_composite(src)
        src = base
    scale = max((x2 - x1) / src.width, (y2 - y1) / src.height)
    nw, nh = int(src.width * scale), int(src.height * scale)
    src = src.resize((nw, nh), Image.LANCZOS)
    left = x1 + ((x2 - x1) - nw) // 2
    top = y1 + ((y2 - y1) - nh) // 2
    canvas.alpha_composite(src, (left, top))


def paste_contain(canvas: Image.Image, src_path: Path, box: tuple[int, int, int, int], bg: str | None = None, pad: int = 0) -> None:
    x1, y1, x2, y2 = box
    x1 += pad
    y1 += pad
    x2 -= pad
    y2 -= pad
    src = open_rgba(src_path)
    if bg:
        base = Image.new("RGBA", src.size, rgb(bg) + (255,))
        base.alpha_composite(src)
        src = base
    src = ImageOps.contain(src, (x2 - x1, y2 - y1), Image.LANCZOS)
    left = x1 + ((x2 - x1) - src.width) // 2
    top = y1 + ((y2 - y1) - src.height) // 2
    canvas.alpha_composite(src, (left, top))


def crop_box(src_path: Path, box: tuple[float, float, float, float], out_path: Path) -> Path:
    img = Image.open(src_path).convert("RGB")
    x1 = int(img.width * box[0])
    y1 = int(img.height * box[1])
    x2 = int(img.width * box[2])
    y2 = int(img.height * box[3])
    img.crop((x1, y1, x2, y2)).save(out_path)
    return out_path


def draw_multiline(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font: ImageFont.FreeTypeFont, fill: str, spacing: int = 8) -> None:
    draw.multiline_text(xy, text, font=font, fill=rgb(fill), spacing=spacing)


def draw_bullets(draw: ImageDraw.ImageDraw, x: int, y: int, items: Iterable[str], width_chars: int = 20, font_size: int = 25, gap: int = 20) -> int:
    font = load_font(font_size)
    cy = y
    for item in items:
        lines = wrap_text(item, width_chars)
        draw.ellipse((x, cy + 11, x + 10, cy + 21), fill=rgb(TURQ_DARK))
        draw_multiline(draw, (x + 24, cy), "\n".join(lines), font, TEXT, spacing=10)
        cy += len(lines) * (font_size + 8) + gap
    return cy


@dataclass
class SlideDef:
    title: str
    section: str
    note: str


SECTIONS = ["研究背景", "方法设计", "系统实现", "实验结果", "结论总结"]


SLIDES: list[SlideDef] = [
    SlideDef("封面", "封面", "各位老师好，我的毕业设计题目是《数据驱动的卡车队列可视化系统》。本次汇报会重点说明研究场景、方法设计、系统实现、实验结果以及最后的结论与不足。"),
    SlideDef("目录", "目录", "整套汇报不按论文章节逐段复述，而是按照答辩更容易理解的顺序展开：先说明为什么做，再说明怎么做，最后说明做成了什么、还有什么不足。"),
    SlideDef("研究背景", "研究背景", "卡车编队是智能物流和车路协同中的典型场景。它会持续产生高频、多车、多维度的轨迹和状态数据，这些数据既有研究价值，也对展示与复盘提出了更高要求。"),
    SlideDef("研究问题", "研究背景", "现有相关工作更关注控制策略、仿真验证和局部算法分析，而对真实运行过程的动态回放、异常定位和交互复盘支持相对不足。我的工作就是补上这部分。"),
    SlideDef("技术路线", "方法设计", "围绕这个问题，本文形成了一条完整路线：原始数据进入系统后，先做清洗与对齐，再计算关键指标，随后构建预警逻辑，最终在界面中完成动态可视化和结果输出。"),
    SlideDef("系统总体架构", "方法设计", "系统采用分层设计，包含数据层、逻辑层、可视化渲染层和交互层。这样的结构便于把数据处理、状态判断和前端展示拆开，实现更清晰。"),
    SlideDef("数据预处理", "方法设计", "原始数据不能直接用于展示，必须先处理异常点、时间戳不齐、坐标不统一和缺失值等问题。预处理质量决定了后续回放和指标计算是否稳定。"),
    SlideDef("指标与预警", "方法设计", "在清洗后的数据基础上，系统重点关注车距、时距、相对速度等指标，并通过规则阈值和连续帧确认完成预警判定。这一步把数据分析和可视化真正连了起来。"),
    SlideDef("渲染与坐标映射", "系统实现", "为了把真实轨迹展示在屏幕上，系统完成了坐标转换、缩放和平移映射，并与轨迹渲染和车辆绘制模块联动。这样既保证了可读性，也支持后续交互。"),
    SlideDef("交互功能设计", "系统实现", "系统不只是播放画面，还支持暂停、调速、快进、事件定位、缩放和平移等操作。它服务的不是单次展示，而是观察、定位、复盘这一整套研究流程。"),
    SlideDef("系统界面展示", "系统实现", "从界面布局上看，系统把主视图、控制与指标区、预警事件区和底部车辆卡片整合到同一页面，方便研究者在一个视图里完成观察和判断。"),
    SlideDef("实验设计", "实验结果", "实验部分更关注系统是否能稳定运行、是否能支撑多车回放，以及是否能对关键事件进行定位和解释。这里的重点是可用性和分析支撑能力。"),
    SlideDef("速度与轨迹结果", "实验结果", "从轨迹和速度曲线可以看到，多车数据在统一时间轴下能够稳定联动，车辆之间的运动关系也能比较直观地呈现出来，说明回放链路是完整的。"),
    SlideDef("车距与预警结果", "实验结果", "进一步看车距和预警统计，当跟车距离缩短到阈值附近时，系统能够在界面和事件流中同步给出提示，这说明指标计算和预警机制是有效联动的。"),
    SlideDef("典型场景分析", "实验结果", "这一页用同一场景下的连续界面来说明系统的分析价值。研究者不仅能看到异常发生，还能沿着事件前后过程做回看和解释。"),
    SlideDef("应用价值", "结论总结", "系统的意义不只是完成了一套展示界面，更在于把真实数据处理、动态回放、预警提示和导出复盘连成了一个可用工具，适合本科毕设场景。"),
    SlideDef("创新点与不足", "结论总结", "本文的创新主要体现在完整链路实现、可视化与预警联动、以及面向复盘的交互界面三个方面。同时，当前预警规则仍偏经验化，平台形态也还有扩展空间。"),
    SlideDef("结论与答谢", "结论总结", "总体来看，本文完成了一套数据驱动的卡车队列可视化系统，基本达成了回放、预警、交互分析和结果导出的目标。我的汇报到这里结束，感谢各位老师聆听。"),
]


def build_charts() -> dict[str, Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
    plt.rcParams["axes.unicode_minus"] = False

    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(DATA_CSV)
    df = df.copy()
    t0 = df["timestamp_ms"].min()
    df["sec"] = (df["timestamp_ms"] - t0) / 1000.0
    df = df[df["sec"] <= 120]
    vehicles = list(df["vehicle_id"].drop_duplicates())
    short_names = {vid: f"车{str(vid)[-4:]}" for vid in vehicles}
    colors = [TURQ_DARK, ACCENT, PURPLE, RED]

    def base_axes(title: str, ylabel: str):
        fig, ax = plt.subplots(figsize=(8.5, 4.8), dpi=180)
        fig.patch.set_facecolor("white")
        ax.set_facecolor("white")
        for side in ["top", "right"]:
            ax.spines[side].set_visible(False)
        ax.spines["left"].set_color("#C8D4DF")
        ax.spines["bottom"].set_color("#C8D4DF")
        ax.grid(True, axis="y", color="#E7EEF5", linewidth=0.8)
        ax.set_title(title, loc="left", fontsize=13, fontname="Microsoft YaHei", color=INK, pad=10)
        ax.set_xlabel("时间 / s", fontname="Microsoft YaHei", fontsize=10, color=TEXT)
        ax.set_ylabel(ylabel, fontname="Microsoft YaHei", fontsize=10, color=TEXT)
        return fig, ax

    speed_path = ASSET_DIR / "speed_lines.png"
    fig, ax = base_axes("多车速度变化", "速度 / km/h")
    for idx, vid in enumerate(vehicles):
        part = df[df["vehicle_id"] == vid].sort_values("sec")
        ax.plot(part["sec"], part["speed"], linewidth=2.2, color=colors[idx % len(colors)], label=short_names[vid])
    ax.legend(frameon=False, ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.12), prop={"family": "Microsoft YaHei", "size": 9})
    fig.tight_layout()
    fig.savefig(speed_path, bbox_inches="tight")
    plt.close(fig)

    headway_path = ASSET_DIR / "headway_lines.png"
    fig, ax = base_axes("关键跟驰车距变化", "车距 / m")
    for idx, vid in enumerate(vehicles[1:]):
        part = df[df["vehicle_id"] == vid].sort_values("sec")
        ax.plot(part["sec"], part["headway_distance"], linewidth=2.2, color=colors[(idx + 1) % len(colors)], label=short_names[vid])
    ax.axhline(20, linestyle="--", linewidth=1.5, color=RED, label="20m预警阈值")
    ax.legend(frameon=False, ncol=2, loc="upper right", prop={"family": "Microsoft YaHei", "size": 9})
    fig.tight_layout()
    fig.savefig(headway_path, bbox_inches="tight")
    plt.close(fig)

    warning_path = ASSET_DIR / "warning_bar.png"
    warning_df = (
        df.assign(warn=lambda x: ((x["headway_distance"] < 20) | (x["headway_time"] < 1.0)).astype(int))
        .groupby("vehicle_id", as_index=False)["warn"]
        .sum()
    )
    fig, ax = plt.subplots(figsize=(5.2, 4.1), dpi=180)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    bars = ax.bar([short_names[v] for v in warning_df["vehicle_id"]], warning_df["warn"], color=[TURQ, ACCENT, PURPLE, RED][: len(warning_df)])
    for side in ["top", "right"]:
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color("#C8D4DF")
    ax.spines["bottom"].set_color("#C8D4DF")
    ax.grid(True, axis="y", color="#E7EEF5", linewidth=0.8)
    ax.set_title("预警触发次数", loc="left", fontsize=13, fontname="Microsoft YaHei", color=INK, pad=10)
    ax.set_ylabel("次数", fontname="Microsoft YaHei", fontsize=10)
    ax.bar_label(bars, padding=3, fontsize=9)
    fig.tight_layout()
    fig.savefig(warning_path, bbox_inches="tight")
    plt.close(fig)

    traj_path = ASSET_DIR / "trajectory.png"
    fig, ax = plt.subplots(figsize=(6.4, 4.8), dpi=180)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    for idx, vid in enumerate(vehicles):
        part = df[df["vehicle_id"] == vid].sort_values("sec")
        ax.plot(part["lon_wgs84"], part["lat_wgs84"], linewidth=2.2, color=colors[idx % len(colors)], label=short_names[vid])
        ax.scatter(part["lon_wgs84"].iloc[0], part["lat_wgs84"].iloc[0], s=18, color=colors[idx % len(colors)])
    for side in ["top", "right"]:
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color("#C8D4DF")
    ax.spines["bottom"].set_color("#C8D4DF")
    ax.set_title("编队轨迹回放路径", loc="left", fontsize=13, fontname="Microsoft YaHei", color=INK, pad=10)
    ax.set_xlabel("经度", fontname="Microsoft YaHei", fontsize=10)
    ax.set_ylabel("纬度", fontname="Microsoft YaHei", fontsize=10)
    ax.legend(frameon=False, loc="best", prop={"family": "Microsoft YaHei", "size": 9})
    fig.tight_layout()
    fig.savefig(traj_path, bbox_inches="tight")
    plt.close(fig)

    crop_center = crop_box(UI_FULL, (0.36, 0.18, 0.77, 0.66), ASSET_DIR / "ui_center.png")
    crop_left = crop_box(UI_FULL, (0.00, 0.04, 0.18, 0.86), ASSET_DIR / "ui_left.png")
    crop_right = crop_box(UI_FULL, (0.84, 0.02, 1.00, 0.33), ASSET_DIR / "ui_right.png")

    return {
        "speed": speed_path,
        "headway": headway_path,
        "warning": warning_path,
        "trajectory": traj_path,
        "ui_center": crop_center,
        "ui_left": crop_left,
        "ui_right": crop_right,
    }


def add_logo(canvas: Image.Image, x: int = 18, y: int = 12, height: int = 44) -> None:
    logo = open_rgba(LOGO)
    ratio = height / logo.height
    logo = logo.resize((int(logo.width * ratio), height), Image.LANCZOS)
    canvas.alpha_composite(logo, (x, y))


def page_shell(title: str, active_section: str, page_no: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (W, H), rgb(BG) + (255,))
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, W, 70), fill=rgb(TURQ))
    draw.rectangle((0, 70, W, 118), fill=rgb(WHITE))
    add_logo(img)

    nav_x = 315
    nav_gap = 180
    for idx, label in enumerate(SECTIONS):
        x = nav_x + idx * nav_gap
        if label == active_section:
            rounded(draw, (x - 8, 18, x + 102, 52), fill=rgb(WHITE), radius=8)
            draw.text((x + 14, 23), label, font=load_font(22, True), fill=rgb(TURQ_DARK))
        else:
            draw.text((x, 24), label, font=load_font(20, True), fill=rgb(WHITE))

    draw.ellipse((52, 96, 64, 108), fill=rgb(TURQ))
    rounded(draw, (118, 92, 478, 130), fill=rgb(TURQ), radius=0)
    draw.text((136, 96), title, font=load_font(28, True), fill=rgb(WHITE))
    draw.text((W - 72, H - 44), f"{page_no:02d}", font=load_font(18), fill=rgb(MUTED))
    return img, draw


def render_cover(page_no: int) -> Image.Image:
    img = Image.new("RGBA", (W, H), rgb(WHITE) + (255,))
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, W, 220), fill=rgb(TURQ))
    draw.rectangle((0, 220, W, H), fill=rgb("#F2F5F8"))
    add_logo(img, x=48, y=52, height=78)
    rounded(draw, (60, 280, 760, 760), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=0)
    draw.text((100, 338), "数据驱动的卡车队列", font=load_font(52, True), fill=rgb(TEXT))
    draw.text((100, 408), "可视化系统", font=load_font(52, True), fill=rgb(TEXT))
    draw.text((100, 492), "本科毕业答辩", font=load_font(28), fill=rgb(TURQ_DARK))
    meta = [
        "答辩人：张作胜",
        "专业：信息管理与信息系统",
        "指导教师：王建强 教授",
        "学院：交通运输学院",
        "学校：兰州交通大学",
        "时间：2026 年 5 月",
    ]
    draw_bullets(draw, 104, 560, meta, width_chars=19, font_size=24, gap=16)
    rounded(draw, (840, 160, 1540, 760), fill=rgb("#EAF3F6"), outline=rgb(BORDER), width=2, radius=0)
    paste_cover(img, FIELD_PHOTO, (860, 180, 1520, 740))
    draw.text((W - 72, H - 44), f"{page_no:02d}", font=load_font(18), fill=rgb(MUTED))
    return img


def render_contents(page_no: int) -> Image.Image:
    img, draw = page_shell("目录", "研究背景", page_no)
    items = [
        ("一", "研究背景与研究问题"),
        ("二", "方法设计与系统架构"),
        ("三", "系统实现与界面展示"),
        ("四", "实验结果与场景分析"),
        ("五", "创新点、结论与不足"),
    ]
    y = 210
    for idx, (no, text) in enumerate(items):
        x1 = 160 if idx % 2 == 0 else 840
        x2 = 740 if idx % 2 == 0 else 1420
        rounded(draw, (x1, y, x2, y + 90), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=14)
        draw.text((x1 + 28, y + 22), no, font=load_font(34, True), fill=rgb(TURQ_DARK))
        draw.text((x1 + 102, y + 28), text, font=load_font(28, True), fill=rgb(TEXT))
        if idx % 2 == 1:
            y += 120
    return img


def render_background(page_no: int) -> Image.Image:
    img, draw = page_shell("研究背景", "研究背景", page_no)
    rounded(draw, (110, 180, 660, 780), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=14)
    draw.text((140, 214), "为什么要做这个系统？", font=load_font(28, True), fill=rgb(TEXT))
    bullets = [
        "卡车编队是智能物流与车路协同中的真实应用场景。",
        "运行过程中会持续产生高频轨迹、速度、车距等多维数据。",
        "仅靠静态表格很难直观看到队列演化与异常发生过程。",
    ]
    draw_bullets(draw, 142, 280, bullets, width_chars=17, font_size=25, gap=24)
    rounded(draw, (720, 180, 1490, 780), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=14)
    paste_cover(img, FIELD_PHOTO, (740, 200, 1470, 760))
    draw.text((744, 726), "实车编队测试场景", font=load_font(22, True), fill=rgb(WHITE))
    return img


def render_problem(page_no: int, charts: dict[str, Path]) -> Image.Image:
    img, draw = page_shell("研究问题", "研究背景", page_no)
    rounded(draw, (110, 180, 780, 430), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=14)
    draw.text((140, 214), "现有工作的不足", font=load_font(28, True), fill=rgb(TEXT))
    draw_bullets(draw, 142, 274, [
        "更关注控制策略和仿真验证。",
        "缺少面向真实数据的动态回放界面。",
        "异常定位和交互复盘支持不够直接。",
    ], width_chars=18, font_size=24, gap=18)
    rounded(draw, (810, 180, 1490, 430), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=14)
    draw.text((840, 214), "本文回答的问题", font=load_font(28, True), fill=rgb(TURQ_DARK))
    question = "如何把高频、多车、强关联的卡车编队数据，转化为可回放、可预警、可分析、可导出的可视化系统？"
    draw_multiline(draw, (840, 280), "\n".join(wrap_text(question, 17)), load_font(32, True), TEXT, spacing=10)
    rounded(draw, (110, 470, 620, 780), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=14)
    rounded(draw, (650, 470, 1120, 780), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=14)
    rounded(draw, (1150, 470, 1490, 780), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=14)
    paste_cover(img, charts["trajectory"], (130, 500, 600, 750))
    paste_cover(img, charts["ui_center"], (670, 500, 1100, 750))
    paste_cover(img, charts["warning"], (1170, 500, 1470, 750))
    return img


def render_route(page_no: int) -> Image.Image:
    img, draw = page_shell("技术路线", "方法设计", page_no)
    steps = [
        ("问题提出", "明确场景与目标"),
        ("数据清洗", "去异常 / 补缺失"),
        ("时间对齐", "统一帧索引"),
        ("指标计算", "速度 / 车距 / 时距"),
        ("预警判定", "阈值规则 + 连续帧"),
        ("可视化输出", "回放 / 分析 / 导出"),
    ]
    x = 100
    y = 300
    for idx, (title, body) in enumerate(steps, 1):
        rounded(draw, (x, y, x + 220, y + 180), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=14)
        draw.text((x + 20, y + 18), f"{idx:02d}", font=load_font(22, True), fill=rgb(TURQ_DARK))
        draw.text((x + 20, y + 64), title, font=load_font(28, True), fill=rgb(TEXT))
        draw_multiline(draw, (x + 20, y + 118), body, load_font(22), MUTED)
        if idx < len(steps):
            draw.line((x + 220, y + 90, x + 250, y + 90), fill=rgb(TURQ_DARK), width=5)
            draw.polygon([(x + 252, y + 90), (x + 236, y + 78), (x + 236, y + 102)], fill=rgb(TURQ_DARK))
        x += 240
    rounded(draw, (130, 560, 1470, 760), fill=rgb("#EDF7F8"), outline=rgb(BORDER), width=2, radius=14)
    draw_multiline(
        draw,
        (160, 616),
        "这条路线的重点不是单独做一个界面，而是把“数据处理—指标分析—预警联动—动态展示”串成一个完整闭环。",
        load_font(30, True),
        TEXT,
        spacing=10,
    )
    return img


def render_arch(page_no: int) -> Image.Image:
    img, draw = page_shell("系统总体架构", "方法设计", page_no)
    rounded(draw, (110, 180, 540, 780), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=14)
    draw.text((140, 214), "分层设计思路", font=load_font(28, True), fill=rgb(TEXT))
    draw_bullets(draw, 142, 274, [
        "数据层负责原始数据与标准化结果。",
        "逻辑层负责时间调度、指标计算和预警判定。",
        "渲染层负责轨迹、车辆、标签与事件流显示。",
        "交互层负责键盘鼠标输入与分析操作。",
    ], width_chars=15, font_size=24, gap=18)
    rounded(draw, (580, 180, 1490, 780), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=14)
    paste_contain(img, FIG_ARCH, (610, 210, 1460, 750), bg=WHITE)
    return img


def render_preprocess(page_no: int) -> Image.Image:
    img, draw = page_shell("数据预处理", "方法设计", page_no)
    rounded(draw, (110, 180, 760, 780), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=14)
    rounded(draw, (800, 180, 1490, 470), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=14)
    rounded(draw, (800, 500, 1490, 780), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=14)
    paste_contain(img, FIG_CLEAN, (130, 210, 740, 750), bg=WHITE)
    draw.text((830, 214), "预处理解决什么问题？", font=load_font(28, True), fill=rgb(TEXT))
    draw_bullets(draw, 832, 274, [
        "轨迹异常点和重复点处理",
        "时间戳统一到同一采样间隔",
        "缺失值插补，保证回放连续性",
        "为后续指标计算提供稳定输入",
    ], width_chars=17, font_size=23, gap=14)
    paste_contain(img, FIG_ALIGN, (828, 530, 1462, 752), bg=WHITE)
    return img


def render_metric(page_no: int, charts: dict[str, Path]) -> Image.Image:
    img, draw = page_shell("指标与预警逻辑", "方法设计", page_no)
    rounded(draw, (110, 180, 1490, 430), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=14)
    paste_contain(img, FIG_METRIC, (130, 206, 1470, 404), bg=WHITE)
    rounded(draw, (110, 470, 780, 780), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=14)
    draw.text((140, 506), "核心指标", font=load_font(28, True), fill=rgb(TEXT))
    draw_bullets(draw, 142, 566, [
        "速度、加速度",
        "车距、车头时距",
        "相对速度与风险提示",
        "连续帧确认，减少误报",
    ], width_chars=16, font_size=24, gap=16)
    rounded(draw, (820, 470, 1490, 780), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=14)
    paste_cover(img, charts["warning"], (848, 512, 1460, 748))
    return img


def render_mapping(page_no: int, charts: dict[str, Path]) -> Image.Image:
    img, draw = page_shell("渲染与坐标映射", "系统实现", page_no)
    rounded(draw, (110, 180, 690, 470), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=14)
    rounded(draw, (720, 180, 1490, 470), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=14)
    rounded(draw, (110, 500, 1490, 780), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=14)
    paste_contain(img, FIG_COORD, (130, 210, 670, 440), bg=WHITE)
    paste_contain(img, FIG_RENDER, (740, 210, 1470, 440), bg=WHITE)
    paste_cover(img, charts["ui_center"], (130, 528, 860, 752))
    draw.text((900, 548), "实现要点", font=load_font(28, True), fill=rgb(TEXT))
    draw_bullets(draw, 902, 608, [
        "将真实经纬度映射到屏幕像素坐标。",
        "支持缩放、平移和轨迹跟踪。",
        "与车辆标签、事件流和底部卡片联动刷新。",
    ], width_chars=18, font_size=24, gap=18)
    return img


def render_interaction(page_no: int) -> Image.Image:
    img, draw = page_shell("交互功能设计", "系统实现", page_no)
    rounded(draw, (110, 180, 760, 780), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=14)
    rounded(draw, (800, 180, 1490, 780), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=14)
    paste_contain(img, FIG_INTERACT, (130, 210, 740, 750), bg=WHITE)
    draw.text((830, 214), "答辩里最值得讲的交互", font=load_font(28, True), fill=rgb(TEXT))
    cards = [
        ("播放控制", "播放 / 暂停 / 调速 / 快进快退"),
        ("时间定位", "拖动进度条，点击事件点快速回看"),
        ("视图控制", "缩放、平移、选中车辆查看细节"),
        ("联动反馈", "轨迹、预警、参数卡片同步刷新"),
    ]
    y = 280
    for title, body in cards:
        rounded(draw, (830, y, 1460, y + 100), fill=rgb("#F2F8FB"), outline=rgb(BORDER), width=2, radius=12)
        draw.text((856, y + 18), title, font=load_font(26, True), fill=rgb(TURQ_DARK))
        draw.text((1022, y + 22), body, font=load_font(22), fill=rgb(TEXT))
        y += 116
    return img


def render_ui(page_no: int, charts: dict[str, Path]) -> Image.Image:
    img, draw = page_shell("系统界面展示", "系统实现", page_no)
    rounded(draw, (110, 180, 1490, 470), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=14)
    paste_contain(img, UI_FULL, (130, 196, 1470, 456))
    boxes = [
        (110, 540, 500, 790, charts["ui_left"], "左侧：控制与指标"),
        (550, 540, 1060, 790, charts["ui_center"], "中部：轨迹与车辆状态"),
        (1110, 540, 1490, 790, charts["ui_right"], "右侧：预警事件流"),
    ]
    for x1, y1, x2, y2, asset, caption in boxes:
        rounded(draw, (x1, y1, x2, y2), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=14)
        paste_contain(img, asset, (x1 + 20, y1 + 20, x2 - 20, y2 - 66), pad=4)
        draw.text((x1 + 24, y2 - 38), caption, font=load_font(22, True), fill=rgb(TEXT))
    return img


def render_experiment(page_no: int, charts: dict[str, Path]) -> Image.Image:
    img, draw = page_shell("实验设计", "实验结果", page_no)
    rounded(draw, (110, 180, 620, 780), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=14)
    draw.text((140, 214), "实验关注点", font=load_font(28, True), fill=rgb(TEXT))
    draw_bullets(draw, 142, 274, [
        "多车轨迹是否可以稳定联动回放",
        "指标计算是否与界面展示一致",
        "预警是否能在关键场景中被及时触发",
        "结果是否便于研究者做回看与导出",
    ], width_chars=15, font_size=24, gap=18)
    rounded(draw, (650, 180, 1490, 470), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=14)
    rounded(draw, (650, 500, 1490, 780), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=14)
    paste_cover(img, charts["trajectory"], (678, 204, 1460, 446))
    paste_cover(img, FIELD_PHOTO, (678, 524, 1100, 752))
    stats = [
        ("数据形式", "多车 GPS 轨迹 + 运行状态"),
        ("样例规模", "4 车编队，连续 120s 样例"),
        ("验证方式", "回放观察 + 指标联动 + 事件检查"),
    ]
    y = 542
    for title, body in stats:
        rounded(draw, (1130, y, 1460, y + 60), fill=rgb("#F2F8FB"), outline=rgb(BORDER), width=2, radius=10)
        draw.text((1148, y + 10), title, font=load_font(20, True), fill=rgb(TURQ_DARK))
        draw.text((1268, y + 12), body, font=load_font(19), fill=rgb(TEXT))
        y += 74
    return img


def render_speed(page_no: int, charts: dict[str, Path]) -> Image.Image:
    img, draw = page_shell("速度与轨迹结果", "实验结果", page_no)
    rounded(draw, (110, 180, 960, 780), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=14)
    rounded(draw, (1000, 180, 1490, 470), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=14)
    rounded(draw, (1000, 500, 1490, 780), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=14)
    paste_cover(img, charts["speed"], (130, 208, 940, 752))
    paste_cover(img, charts["trajectory"], (1022, 206, 1462, 442))
    draw.text((1030, 534), "结果观察", font=load_font(26, True), fill=rgb(TEXT))
    draw_bullets(draw, 1032, 590, [
        "多车速度曲线可同步联动展示。",
        "轨迹与速度关系能相互印证。",
        "为异常定位和过程解释提供基础。",
    ], width_chars=14, font_size=23, gap=16)
    return img


def render_headway(page_no: int, charts: dict[str, Path]) -> Image.Image:
    img, draw = page_shell("车距与预警结果", "实验结果", page_no)
    rounded(draw, (110, 180, 930, 780), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=14)
    rounded(draw, (970, 180, 1490, 470), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=14)
    rounded(draw, (970, 500, 1490, 780), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=14)
    paste_cover(img, charts["headway"], (130, 208, 910, 752))
    paste_cover(img, charts["warning"], (992, 206, 1462, 442))
    paste_cover(img, charts["ui_right"], (992, 526, 1462, 752))
    return img


def render_scene(page_no: int) -> Image.Image:
    img, draw = page_shell("典型场景分析", "实验结果", page_no)
    rounded(draw, (110, 180, 1490, 780), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=14)
    paste_cover(img, UI_GRID, (140, 220, 980, 740))
    notes = [
        ("阶段 1", "正常编队行驶"),
        ("阶段 2", "局部车距缩短"),
        ("阶段 3", "预警信息持续出现"),
        ("阶段 4", "研究者回看并定位问题"),
    ]
    y = 240
    for title, body in notes:
        rounded(draw, (1040, y, 1450, y + 95), fill=rgb("#F2F8FB"), outline=rgb(BORDER), width=2, radius=12)
        draw.text((1066, y + 18), title, font=load_font(25, True), fill=rgb(TURQ_DARK))
        draw.text((1190, y + 22), body, font=load_font(22), fill=rgb(TEXT))
        y += 118
    return img


def render_value(page_no: int, charts: dict[str, Path]) -> Image.Image:
    img, draw = page_shell("应用价值", "结论总结", page_no)
    cards = [
        ("研究支撑", "把原始数据变成可以看、可以讲、可以复盘的分析对象。", FIELD_PHOTO),
        ("系统落地", "将数据处理、回放、预警、导出整合为一套可运行工具。", charts["ui_center"]),
        ("答辩表达", "更适合本科答辩用图说话，而不是照搬论文长段落。", charts["speed"]),
    ]
    x = 120
    for title, body, asset in cards:
        rounded(draw, (x, 220, x + 420, 760), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=14)
        paste_cover(img, asset, (x + 20, 240, x + 400, 470))
        draw.text((x + 24, 500), title, font=load_font(30, True), fill=rgb(TEXT))
        draw_multiline(draw, (x + 24, 558), "\n".join(wrap_text(body, 13)), load_font(24), MUTED, spacing=10)
        x += 460
    return img


def render_innovation(page_no: int) -> Image.Image:
    img, draw = page_shell("创新点与不足", "结论总结", page_no)
    rounded(draw, (110, 180, 760, 780), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=14)
    rounded(draw, (820, 180, 1490, 780), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=14)
    draw.text((140, 214), "创新点", font=load_font(30, True), fill=rgb(TURQ_DARK))
    draw_bullets(draw, 142, 286, [
        "完成“数据处理—指标分析—预警联动—动态展示”的完整链路。",
        "把预警判定和界面事件流联动起来，提升可解释性。",
        "面向答辩与复盘设计交互界面，而不是单纯做静态图表。",
    ], width_chars=15, font_size=24, gap=24)
    draw.text((850, 214), "当前不足", font=load_font(30, True), fill=rgb(RED))
    draw_bullets(draw, 852, 286, [
        "预警规则仍以经验阈值为主。",
        "样例场景还可以进一步扩展。",
        "后续可继续向 Web 化和三维化延伸。",
    ], width_chars=16, font_size=24, gap=24)
    rounded(draw, (850, 560, 1450, 724), fill=rgb("#FFF6F2"), outline=rgb("#F0D2C8"), width=2, radius=12)
    draw_multiline(draw, (886, 602), "这页答辩时建议控制在 1 分钟左右：\n先说创新，再诚实交代边界。", load_font(26, True), TEXT, spacing=10)
    return img


def render_end(page_no: int) -> Image.Image:
    img = Image.new("RGBA", (W, H), rgb(WHITE) + (255,))
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, W, 250), fill=rgb(TURQ))
    draw.rectangle((0, 250, W, H), fill=rgb("#F2F5F8"))
    add_logo(img, x=80, y=78, height=90)
    rounded(draw, (330, 320, 1280, 680), fill=rgb(WHITE), outline=rgb(BORDER), width=2, radius=0)
    draw.text((560, 398), "谢  谢", font=load_font(58, True), fill=rgb(TURQ_DARK))
    draw.text((480, 488), "敬请各位老师批评指正", font=load_font(34), fill=rgb(TEXT))
    rounded(draw, (510, 560, 1100, 608), fill=rgb(TURQ), radius=24)
    draw.text((650, 571), "Q & A", font=load_font(24, True), fill=rgb(WHITE))
    draw.text((W - 72, H - 44), f"{page_no:02d}", font=load_font(18), fill=rgb(MUTED))
    return img


def build_notes_markdown() -> str:
    parts: list[str] = []
    for idx, slide in enumerate(SLIDES, 1):
        parts.append(f"# {idx:02d}_{slide.title}\n\n{slide.note}\n")
    return "\n".join(parts)


def render_all_slides(charts: dict[str, Path]) -> list[Path]:
    SLIDE_DIR.mkdir(parents=True, exist_ok=True)
    rendered: list[Path] = []
    builders = [
        lambda i: render_cover(i),
        lambda i: render_contents(i),
        lambda i: render_background(i),
        lambda i: render_problem(i, charts),
        lambda i: render_route(i),
        lambda i: render_arch(i),
        lambda i: render_preprocess(i),
        lambda i: render_metric(i, charts),
        lambda i: render_mapping(i, charts),
        lambda i: render_interaction(i),
        lambda i: render_ui(i, charts),
        lambda i: render_experiment(i, charts),
        lambda i: render_speed(i, charts),
        lambda i: render_headway(i, charts),
        lambda i: render_scene(i),
        lambda i: render_value(i, charts),
        lambda i: render_innovation(i),
        lambda i: render_end(i),
    ]
    for idx, build in enumerate(builders, 1):
        out = SLIDE_DIR / f"slide_{idx:02d}.png"
        build(idx).convert("RGB").save(out, quality=95)
        rendered.append(out)
    return rendered


def build_ppt(slide_paths: list[Path]) -> Path:
    import win32com.client  # type: ignore

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    OUT_NOTES.write_text(build_notes_markdown(), encoding="utf-8")

    app = win32com.client.Dispatch("PowerPoint.Application")
    app.Visible = 1
    app.DisplayAlerts = 0
    pres = app.Presentations.Add()
    width = pres.PageSetup.SlideWidth
    height = pres.PageSetup.SlideHeight
    while pres.Slides.Count > 0:
        pres.Slides(1).Delete()

    for idx, (slide_path, slide_meta) in enumerate(zip(slide_paths, SLIDES), 1):
        slide = pres.Slides.Add(idx, 12)
        slide.Shapes.AddPicture(str(slide_path), False, True, 0, 0, width, height)
        notes_shape = slide.NotesPage.Shapes.Placeholders(2)
        notes_shape.TextFrame.TextRange.Text = slide_meta.note

    pres.SaveAs(str(OUT_PPT), 24)
    pres.Saved = True
    try:
        pres.Close()
    except Exception:
        pass
    app.Quit()
    return OUT_PPT


def main() -> None:
    charts = build_charts()
    slides = render_all_slides(charts)
    out_ppt = build_ppt(slides)
    print(out_ppt)


if __name__ == "__main__":
    main()
