import sys
import os
import logging
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import PlatoonConfig

try:
    from .data_processor import DataProcessor
    from .visualizer import Visualizer
except ImportError:
    from data_processor import DataProcessor
    from visualizer import Visualizer


logger = logging.getLogger(__name__)


def _resolve_default_data_folder():
    base_dir = PROJECT_ROOT / PlatoonConfig.OUTPUT_BASE_DIR
    preferred = base_dir / "12mins_4trucks"
    if preferred.exists():
        return str(preferred)

    if base_dir.exists():
        candidates = sorted(path for path in base_dir.iterdir() if path.is_dir())
        if candidates:
            return str(candidates[0])

    return str(preferred)


def run_visualization(data_folder):
    """核心可视化逻辑"""
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # 1. 检查路径
    if not os.path.exists(data_folder):
        logger.error("路径不存在: %s", data_folder)
        return

    # 2. 初始化数据处理器
    logger.info("正在加载数据: %s ...", data_folder)
    try:
        processor = DataProcessor(data_folder)
    except Exception as e:
        logger.exception("数据加载失败: %s", e)
        return

    # 3. 初始化 Pygame 可视化引擎
    viz = Visualizer(width=1280, height=720)

    # 4. 运行主循环
    logger.info("可视化窗口已启动，请切换至该窗口。")
    viz.run(processor)


if __name__ == "__main__":
    # 检查是否有命令行参数传入
    if len(sys.argv) > 1:
        # 【修正点】取列表中的第二个元素
        target_folder = sys.argv[1]
    else:
        # 如果没有参数，使用默认配置（方便直接调试 main.py）
        logger.info("未检测到启动参数，使用默认配置...")
        target_folder = _resolve_default_data_folder()

    run_visualization(target_folder)
