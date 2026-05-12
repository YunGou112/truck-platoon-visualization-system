import os
import pandas as pd
import colorsys
from config import PlatoonConfig

try:
    from .models import Truck
except ImportError:
    from models import Truck


class DataProcessor:
    def __init__(self, data_folder):
        self.min_time = None
        self.max_time = None
        self.trucks = {}
        self.all_platoons = {}
        self.current_platoon = None

        # 地图边界
        self.min_lon = 116.0
        self.max_lon = 117.0
        self.min_lat = 39.0
        self.max_lat = 40.0

        self._load_data(data_folder)

    def _load_data(self, folder_path):
        # 检查是否是 platoon_results 目录
        if os.path.basename(folder_path) == 'platoon_results':
            self._load_all_platoons(folder_path)
        else:
            # 处理单个编队文件夹
            self._load_single_platoon(folder_path)

    def _load_single_platoon(self, folder_path):
        csv_path = os.path.join(folder_path, 'platoon_data.csv')
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"未找到数据文件: {csv_path}")

        df = pd.read_csv(csv_path)

        if df.empty:
            print(f"警告：文件 {csv_path} 为空。")
            return

        print(f"检测到 CSV 列名: {df.columns.tolist()}")

        # 1. 处理时间列
        if 'timestamp_str' not in df.columns:
            raise KeyError("CSV文件中缺少 'timestamp_str' 列。")

        df['timestamp'] = pd.to_datetime(df['timestamp_str'])

        self.min_time = df['timestamp'].min()
        self.max_time = df['timestamp'].max()
        print(f"数据时间范围: {self.min_time} -> {self.max_time}")

        # 2. 【关键修正】处理坐标列
        # 优先使用 WGS84 (标准GPS)，如果没有则尝试 GCJ02 或 BD09
        coord_mapping = {
            'lon_wgs84': 'lon', 'lat_wgs84': 'lat',
            'lon_gcj02': 'lon', 'lat_gcj02': 'lat',
            'lon_bd09': 'lon', 'lat_bd09': 'lat'
        }

        renamed = False
        for src_col, target_col in coord_mapping.items():
            if src_col in df.columns and target_col not in df.columns:
                # 将原始列重命名为标准的 'lon' 或 'lat'
                df.rename(columns={src_col: target_col}, inplace=True)
                print(f"已将 '{src_col}' 映射为 '{target_col}'")
                renamed = True
                # 找到一对就停止，避免覆盖
                if 'lon' in df.columns and 'lat' in df.columns:
                    break

        if 'lon' not in df.columns or 'lat' not in df.columns:
            raise KeyError("无法识别经纬度列，请检查 CSV 中是否包含 wgs84/gcj02/bd09 坐标。")

        # 3. 自动计算地理边界
        self.min_lon = df['lon'].min() - 0.001
        self.max_lon = df['lon'].max() + 0.001
        self.min_lat = df['lat'].min() - 0.001
        self.max_lat = df['lat'].max() + 0.001

        # 4. 自动检测车辆 ID 列名
        id_col = None
        possible_id_names = ['vehicle_id', 'truck_id', 'id', 'vehicleId', 'ID']
        for name in possible_id_names:
            if name in df.columns:
                id_col = name
                break

        if id_col is None:
            print("错误：未识别车辆 ID 列！")
            return

        print(f"使用 '{id_col}' 列作为车辆 ID。")

        # 5. 按车辆 ID 分组数据，并按数量动态分配区分色
        grouped_items = list(df.groupby(id_col))
        total_trucks = len(grouped_items)

        for idx, (truck_id, group) in enumerate(grouped_items):
            group = group.sort_values(by='timestamp')

            # 确保只保留需要的列，减少内存占用
            # 但这里为了简单，保留所有列
            truck = Truck(str(truck_id), group.to_dict('records'))
            self.trucks[truck_id] = truck
            truck.base_color = self._generate_distinct_color(idx, total_trucks)
            truck.color = truck.base_color

        print(f"成功加载 {len(self.trucks)} 辆卡车的数据。")

    def _generate_distinct_color(self, index, total):
        """根据车辆数量动态生成区分度较高的颜色。"""
        if total <= 0:
            return (180, 180, 180)
        hue = (index / float(total)) % 1.0
        # 保持较高饱和度和亮度，便于在深色背景下区分
        r, g, b = colorsys.hsv_to_rgb(hue, 0.62, 0.95)
        return (int(r * 255), int(g * 255), int(b * 255))

    def _load_all_platoons(self, platoon_results_path):
        """加载platoon_results目录下的所有编队数据"""
        print(f"正在加载 platoon_results 目录: {platoon_results_path}")
        
        # 遍历所有子文件夹
        for root, dirs, files in os.walk(platoon_results_path):
            # 只处理直接子目录（每个子目录对应一个编队）
            if root == platoon_results_path:
                for dir_name in dirs:
                    platoon_folder = os.path.join(root, dir_name)
                    print(f"\n处理编队: {dir_name}")
                    
                    try:
                        # 为每个编队创建一个数据处理器
                        platoon_processor = DataProcessor(platoon_folder)
                        self.all_platoons[dir_name] = platoon_processor
                        print(f"成功加载编队: {dir_name}，包含 {len(platoon_processor.trucks)} 辆卡车")
                    except Exception as e:
                        print(f"加载编队 {dir_name} 失败: {e}")
        
        # 设置默认当前编队
        if self.all_platoons:
            first_platoon = next(iter(self.all_platoons.keys()))
            self.current_platoon = first_platoon
            # 使用第一个编队的时间范围和地理边界
            first_processor = self.all_platoons[first_platoon]
            self.min_time = first_processor.min_time
            self.max_time = first_processor.max_time
            self.min_lon = first_processor.min_lon
            self.max_lon = first_processor.max_lon
            self.min_lat = first_processor.min_lat
            self.max_lat = first_processor.max_lat
            # 使用第一个编队的卡车数据
            self.trucks = first_processor.trucks
            print(f"默认选择编队: {first_platoon}")
        else:
            print("警告：platoon_results 目录中没有找到有效的编队数据")

    def geo_to_screen(self, lon, lat, width, height, zoom=1.0, offset_x=0, offset_y=0):
        """将经纬度转换为屏幕坐标"""
        lon_range = self.max_lon - self.min_lon
        lat_range = self.max_lat - self.min_lat
        if abs(lon_range) < 1e-12:
            lon_range = 1.0
        if abs(lat_range) < 1e-12:
            lat_range = 1.0

        x = (lon - self.min_lon) / lon_range * width
        y = (self.max_lat - lat) / lat_range * height

        cx, cy = width / 2, height / 2
        x = (x - cx) * zoom + cx + offset_x
        y = (y - cy) * zoom + cy + offset_y

        return int(x), int(y)

    def switch_platoon(self, platoon_name):
        """切换到指定的编队"""
        if platoon_name in self.all_platoons:
            platoon_processor = self.all_platoons[platoon_name]
            self.current_platoon = platoon_name
            self.min_time = platoon_processor.min_time
            self.max_time = platoon_processor.max_time
            self.min_lon = platoon_processor.min_lon
            self.max_lon = platoon_processor.max_lon
            self.min_lat = platoon_processor.min_lat
            self.max_lat = platoon_processor.max_lat
            self.trucks = platoon_processor.trucks
            print(f"已切换到编队: {platoon_name}")
            return True
        else:
            print(f"编队 {platoon_name} 不存在")
            return False

    def get_available_platoons(self):
        """获取所有可用的编队名称"""
        return list(self.all_platoons.keys())

    def filter_platoons_by_size(self, min_size, max_size=None):
        """根据编队大小筛选编队"""
        filtered_platoons = {}
        for platoon_name, platoon_processor in self.all_platoons.items():
            truck_count = len(platoon_processor.trucks)
            if truck_count >= min_size and (max_size is None or truck_count <= max_size):
                filtered_platoons[platoon_name] = platoon_processor
        return filtered_platoons

    def filter_platoons_by_time(self, start_time, end_time):
        """根据时间范围筛选编队"""
        filtered_platoons = {}
        for platoon_name, platoon_processor in self.all_platoons.items():
            if platoon_processor.min_time and platoon_processor.max_time:
                if (platoon_processor.min_time <= end_time) and (platoon_processor.max_time >= start_time):
                    filtered_platoons[platoon_name] = platoon_processor
        return filtered_platoons

    def apply_filter(self, min_size=None, max_size=None, start_time=None, end_time=None):
        """应用筛选条件，返回筛选后的编队"""
        filtered_platoons = self.all_platoons.copy()
        
        if min_size is not None or max_size is not None:
            filtered_platoons = self.filter_platoons_by_size(min_size or 1, max_size)
        
        if start_time is not None and end_time is not None:
            time_filtered = self.filter_platoons_by_time(start_time, end_time)
            filtered_platoons = {
                name: processor
                for name, processor in filtered_platoons.items()
                if name in time_filtered
            }
        
        return filtered_platoons
