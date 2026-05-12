import sys
import os

from config import PlatoonConfig

try:
    from .data_processor import DataProcessor
    from .visualizer import Visualizer
except ImportError:
    from data_processor import DataProcessor
    from visualizer import Visualizer


def run_visualization(data_folder):
    """核心可视化逻辑"""
    # 1. 检查路径
    if not os.path.exists(data_folder):
        print(f"错误：路径不存在 {data_folder}")
        return

    # 2. 初始化数据处理器
    print(f"正在加载数据: {data_folder} ...")
    try:
        processor = DataProcessor(data_folder)
    except Exception as e:
        print(f"数据加载失败: {e}")
        return

    # 3. 初始化 Pygame 可视化引擎
    viz = Visualizer(width=1280, height=720)

    # 4. 运行主循环
    print("可视化窗口已启动，请切换至该窗口。")
    viz.run(processor)


if __name__ == "__main__":
    # 检查是否有命令行参数传入
    if len(sys.argv) > 1:
        # 【修正点】取列表中的第二个元素
        target_folder = sys.argv[1]
    else:
        # 如果没有参数，使用默认配置（方便直接调试 main.py）
        print("未检测到启动参数，使用默认配置...")
        # 如果 config.py 里有定义，可以用下面的方式，或者直接写死路径
        target_folder = os.path.join(os.path.dirname(__file__), PlatoonConfig.OUTPUT_BASE_DIR, '12mins_4trucks')

    run_visualization(target_folder)
