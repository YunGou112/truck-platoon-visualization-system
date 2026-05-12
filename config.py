import os


class PlatoonConfig:
    """
    全局配置类：
    1. 定义数据路径（原始数据与处理后的数据）
    2. 定义数据列名映射（适配不同的原始数据格式）
    3. 定义编队筛选算法的阈值参数
    """
    MAX_DISTANCE_METERS = 100
    MAX_SPEED_DIFF = 10
    MAX_DIRECTION_DIFF = 45  # 最大方向差（度），同向行驶允许的范围
    MIN_CONTINUOUS_WINDOWS = 3  # 最小连续编队窗口数，避免偶然相遇
    INPUT_DIR = 'data_split'  # 输入数据目录（CSV文件）
    # =========================
    # 1. 路径配置
    # =========================
    # 原始 13G 数据文件路径
    INPUT_FILE = 'position-all-260302.json'

    # 处理后的编队数据存放目录
    OUTPUT_BASE_DIR = 'platoon_results'

    # =========================
    # 2. 数据字段映射
    # =========================
    # 请根据您的 JSON 原始数据实际键名修改以下变量

    # 时间戳列名
    COL_TIMESTAMP = 'timestamp_str'

    # 车辆ID列名
    COL_VID = 'vehicle_id'

    # 经纬度列名 (原始数据)
    COL_LON = 'lon'
    COL_LAT = 'lat'

    # 速度列名 (严格使用原始速度列，不再二次计算)
    SPEED_COLUMN = 'speed'

    # =========================
    # 3. 编队筛选算法参数
    # =========================
    # 最小持续时间 (秒)
    MIN_DURATION_SECONDS = 60

    # 最小车辆数 (少于该数量不视为编队)
    MIN_PLATOON_SIZE = 3

    # 最大车头时距/距离阈值 (用于判断是否在同一编队)
    MAX_GAP_DISTANCE = 100  # 单位：米

    # 数据采样间隔 (秒)，用于扫描窗口
    TIME_WINDOW_SECONDS = 30

    # =========================
    # 4. 可视化系统配置
    # =========================
    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 720
    FPS = 60
    # 图标角度偏移
    icon_angle_offset = 0
    # 地图显示边距
    MAP_MARGIN = 50

    # =========================
    # 5. 预警规则配置（可视化使用）
    # =========================
    # 注意：当前数据中的 speed 字段单位为 km/h
    WARNING_MIN_DISTANCE_M = 20.0
    WARNING_MAX_ABS_ACCEL_MPS2 = 3.0
    WARNING_MAX_SPEED_KMH = 90.0
    WARNING_DEBOUNCE_FRAMES = 2

    @staticmethod
    def ensure_dir():
        """确保输出目录存在"""
        if not os.path.exists(PlatoonConfig.OUTPUT_BASE_DIR):
            os.makedirs(PlatoonConfig.OUTPUT_BASE_DIR)
