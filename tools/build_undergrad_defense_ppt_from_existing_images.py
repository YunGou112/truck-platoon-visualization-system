from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IMAGE_DIR = ROOT / "defense_ppt_output" / "slides"
PROJECT_DIR = ROOT / "projects" / "truck_platoon_bachelor_defense_ppt169_20260509"
EXPORT_DIR = PROJECT_DIR / "exports"
OUT_PPT = EXPORT_DIR / "truck_platoon_bachelor_defense_image_deck_v1.pptx"
OUT_NOTES = PROJECT_DIR / "notes" / "total.md"


SLIDE_TITLES = [
    "封面",
    "目录",
    "研究背景",
    "研究意义",
    "现有研究与不足",
    "研究问题与目标",
    "技术路线",
    "系统总体架构",
    "数据特点与挑战",
    "数据预处理流程",
    "关键指标体系",
    "预警判别机制",
    "可视化引擎设计",
    "交互功能设计",
    "系统界面与输出能力",
    "实验设计",
    "功能验证结果",
    "典型场景分析",
    "实验结果总结",
    "主要工作与创新点",
    "研究结论",
    "不足、展望与致谢",
]


SLIDE_NOTES = [
    "各位老师好，我的毕业设计题目是《数据驱动的卡车队列可视化系统》。本课题主要面向卡车队列运行数据，目标是把原始数据转化为一个可回放、可预警、可分析的可视化系统。下面我将从研究背景、方法设计、系统实现、实验结果以及总结展望几个部分进行汇报。",
    "本次汇报不完全按照论文原文章节展开，而是按照答辩更容易理解的逻辑来组织。先说明为什么做这项工作，再说明怎么做、做成什么样，最后给出结果、创新点和结论。",
    "随着智慧物流、车联网和自动驾驶相关技术的发展，卡车队列已经成为智能交通中的典型研究场景。它在运行过程中会持续产生大量轨迹、速度和车间关系数据，而这些数据具有高频、多维和强关联的特点。",
    "这项工作的意义主要体现在三个方面。第一，是把数据处理和可视化表达连接起来；第二，是形成一套可落地的系统实现方案；第三，是为后续异常复盘、教学展示和运行分析提供工具支撑。",
    "从现有研究来看，很多工作已经关注了编队控制、协同策略和仿真分析。但对于运行过程的动态展示、异常定位和交互式复盘支持还不够，这也是本文重点补足的部分。",
    "因此，本文提出的核心问题是，如何把高频、多维、强关联的卡车队列数据，转化为一个可回放、可预警、可分析、可导出的可视化系统。围绕这个问题，我设置了数据处理、指标构建、动态展示和结果输出四个目标。",
    "围绕刚才的问题，本文构建了完整的技术路线。整体流程可以概括为数据输入、预处理、指标构建、状态判别、可视化呈现、交互分析以及结果输出，这也是后面系统实现部分的主线。",
    "在总体设计上，系统采用分层架构，分为数据层、逻辑层、可视化层和交互层。这样做的好处是结构清晰，职责边界明确，也方便后续维护与扩展。",
    "原始数据并不能直接拿来展示，因为它存在数据量大、采样频率高、多坐标体系并存、噪声和缺失并存等问题。另外，真正关键的异常事件往往只占很少一部分，因此必须先做规范化处理。",
    "数据预处理阶段主要完成字段统一、异常清洗、时间对齐、缺失补全和坐标映射等工作。处理后的标准化数据，才能稳定支撑后续的指标计算和连续回放。",
    "在标准化数据的基础上，本文构建了若干关键指标，包括速度、加速度、车间距、车头时距、相对速度以及安全偏离度等。这些指标一方面用于风险判断，另一方面也直接服务于界面展示。",
    "预警机制的设计并不是简单把异常点染成红色，而是先依据规则阈值完成状态判别，再把结果同步到界面与事件流中。为了减少误报，系统还加入了连续帧确认策略。",
    "在可视化实现方面，本文采用 Python 和 Pygame 构建动态回放引擎，实现了轨迹回放、车辆渲染、参数标签显示和状态联动。这个方案轻量、直接，也适合本科毕设场景下的快速实现与演示。",
    "除了展示之外，系统还强调交互可用性。它支持播放暂停、调速、快进快退、进度跳转、事件定位和车辆选中等操作，服务于观察、定位和复盘这一完整分析过程。",
    "从界面上看，系统不仅有主视图，还提供参数信息区、事件流区以及结果导出能力。这样一来，它不只是一个展示窗口，而是具备了基本分析工具的属性。",
    "实验部分主要围绕系统是否稳定、是否可用以及是否能够支持异常识别与复盘展开。这里更关注系统能不能真正完成分析任务，而不只是某一个单独数值指标。",
    "从功能验证结果来看，系统已经能够完成稳定回放、状态联动、异常提示以及结果导出等主要功能。换句话说，这套系统在本科毕业设计层面已经形成了比较完整的实现闭环。",
    "这一页通过一个典型场景说明系统的实际价值。它能够把异常事件从发生、触发到回看分析串起来，让研究者看到问题是如何演化的，而不是只得到一个孤立的异常标记。",
    "综合实验结果来看，这套系统已经较好完成了从数据处理到可视化分析的完整链路，也验证了方案在稳定性、完整性和实用性方面的可行性。",
    "本文的创新点主要体现在三个方面。第一，完成了从原始数据到动态展示的一体化流程；第二，设计了预警与事件联动机制；第三，形成了适合答辩展示和分析使用的交互式界面。这里的创新更强调完整实现和实用价值，而不是夸张的理论突破。",
    "总体来看，本文完成了一套数据驱动的卡车队列可视化系统，实现了回放、预警、交互分析和结果输出等目标。实验结果表明，该方案在典型场景下具备较好的稳定性和实用性，研究目标基本达成。",
    "当然，这项工作也还有一些不足。例如当前预警规则仍然偏经验化，场景规模还可以进一步扩展，平台形态也还可以继续完善。后续可以从 Web 化、三维化和更智能的识别机制等方向继续深入。我的汇报到这里结束，感谢各位老师聆听，恳请批评指正。",
]


def build_notes_markdown() -> str:
    parts: list[str] = []
    for idx, (title, note) in enumerate(zip(SLIDE_TITLES, SLIDE_NOTES), 1):
        parts.append(f"# {idx:02d}_{title}\n\n{note}\n")
    return "\n".join(parts)


def build_ppt() -> Path:
    import win32com.client  # type: ignore

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_NOTES.parent.mkdir(parents=True, exist_ok=True)
    OUT_NOTES.write_text(build_notes_markdown(), encoding="utf-8")

    app = win32com.client.Dispatch("PowerPoint.Application")
    app.Visible = 1
    app.DisplayAlerts = 0
    pres = app.Presentations.Add()
    width = pres.PageSetup.SlideWidth
    height = pres.PageSetup.SlideHeight

    while pres.Slides.Count > 0:
        pres.Slides(1).Delete()

    for idx, note in enumerate(SLIDE_NOTES, 1):
        image_path = IMAGE_DIR / f"slide_{idx:02d}.png"
        if not image_path.exists():
            raise FileNotFoundError(f"Missing slide image: {image_path}")
        slide = pres.Slides.Add(idx, 12)
        slide.Shapes.AddPicture(str(image_path), False, True, 0, 0, width, height)
        notes_shape = slide.NotesPage.Shapes.Placeholders(2)
        notes_shape.TextFrame.TextRange.Text = note

    pres.SaveAs(str(OUT_PPT), 24)
    pres.Saved = True
    try:
        pres.Close()
    except Exception:
        pass
    app.Quit()
    return OUT_PPT


if __name__ == "__main__":
    path = build_ppt()
    print(path)
