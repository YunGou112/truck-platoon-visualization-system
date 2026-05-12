import pandas as pd
from config import PlatoonConfig

class Truck:
    def __init__(self, truck_id, track_data):
        self.id = truck_id
        self.track = track_data  # 轨迹点列表
        self.color = (255, 255, 255)
        self.base_color = (255, 255, 255)
        self.current_pos_data = None
        self.prev_pos_data = None
        self.warning = 0
        self.warning_type = 0
        self.warning_text = ""
        self._warning_streak = 0
        self._cursor_idx = 0
        self._last_update_time = None
        # 用于底部“单车指标卡”的起点缓存
        self._start_ts = None
        self._start_mileage = None
        self._prepare_time_cache()

    def _prepare_time_cache(self):
        """预解析时间戳，避免每帧重复 to_datetime。"""
        for point in self.track:
            if '_ts' not in point:
                try:
                    point['_ts'] = pd.to_datetime(point['timestamp_str'])
                except Exception:
                    point['_ts'] = pd.Timestamp.min

    def update(self, current_time):
        """根据当前时间更新车辆位置"""
        if not self.track:
            self.current_pos_data = None
            return

        # 快速路径：根据时间方向前后移动游标
        if current_time < self.track[0]['_ts']:
            self.current_pos_data = None
            self._cursor_idx = 0
            self._last_update_time = current_time
            return

        n = len(self.track)
        if self._last_update_time is None:
            self._cursor_idx = 0
        elif current_time < self._last_update_time:
            # 时间倒退（拖动进度条等），游标向前回退
            while self._cursor_idx > 0 and self.track[self._cursor_idx]['_ts'] > current_time:
                self._cursor_idx -= 1
        else:
            # 正向播放，游标向后推进
            while self._cursor_idx + 1 < n and self.track[self._cursor_idx + 1]['_ts'] <= current_time:
                self._cursor_idx += 1

        self.prev_pos_data = self.current_pos_data
        if 0 <= self._cursor_idx < n and self.track[self._cursor_idx]['_ts'] <= current_time:
            self.current_pos_data = self.track[self._cursor_idx]
            # 首次进入有效状态时，记录起点（用于行驶时间/里程）
            if self._start_ts is None:
                self._start_ts = self.current_pos_data.get('_ts')
            if self._start_mileage is None:
                m = self.current_pos_data.get('mileage')
                try:
                    self._start_mileage = float(m) if m is not None else None
                except Exception:
                    self._start_mileage = None
        else:
            self.current_pos_data = None
        self._last_update_time = current_time

    def get_speed(self):
        """获取当前速度"""
        if self.current_pos_data and 'speed' in self.current_pos_data:
            return self.current_pos_data['speed']
        return 0.0

    def get_acceleration(self):
        """获取加速度"""
        if self.current_pos_data and self.prev_pos_data:
            if 'speed' in self.current_pos_data and 'speed' in self.prev_pos_data:
                if 'timestamp_str' in self.current_pos_data and 'timestamp_str' in self.prev_pos_data:
                    # speed 字段单位为 km/h，这里转换为 m/s 后计算加速度，单位 m/s^2
                    cur_speed_mps = (self.current_pos_data['speed'] or 0.0) / 3.6
                    prev_speed_mps = (self.prev_pos_data['speed'] or 0.0) / 3.6
                    delta_speed_mps = cur_speed_mps - prev_speed_mps
                    # 优先使用预解析时间缓存，避免重复转换
                    current_time = self.current_pos_data.get('_ts') or pd.to_datetime(self.current_pos_data['timestamp_str'])
                    prev_time = self.prev_pos_data.get('_ts') or pd.to_datetime(self.prev_pos_data['timestamp_str'])
                    delta_time = (current_time - prev_time).total_seconds()
                    if delta_time > 0:
                        return delta_speed_mps / delta_time
        return 0.0

    def get_headway_distance(self, other_truck):
        """获取与另一辆卡车的车头间距"""
        if self.current_pos_data and other_truck.current_pos_data:
            if 'lon' in self.current_pos_data and 'lat' in self.current_pos_data:
                if 'lon' in other_truck.current_pos_data and 'lat' in other_truck.current_pos_data:
                    # 使用 Haversine 公式计算两点距离（米）
                    import math
                    lon1 = float(self.current_pos_data['lon'])
                    lat1 = float(self.current_pos_data['lat'])
                    lon2 = float(other_truck.current_pos_data['lon'])
                    lat2 = float(other_truck.current_pos_data['lat'])

                    r = 6371000.0
                    p1, p2 = math.radians(lat1), math.radians(lat2)
                    d1 = math.radians(lat2 - lat1)
                    d2 = math.radians(lon2 - lon1)
                    a = math.sin(d1 / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(d2 / 2) ** 2
                    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return float('inf')

    def get_headway_time(self, other_truck):
        """获取与另一辆卡车的车头时距"""
        distance = self.get_headway_distance(other_truck)
        speed_mps = self.get_speed() / 3.6
        if speed_mps > 0:
            return distance / speed_mps
        return float('inf')

    def reset(self):
        """重置车辆状态"""
        self.current_pos_data = None
        self.prev_pos_data = None
        self.warning = 0
        self.warning_type = 0
        self.warning_text = ""
        self._warning_streak = 0
        self._cursor_idx = 0
        self._last_update_time = None
        # 注意：不清空 _start_ts/_start_mileage，这样快进/后退仍以片段起点为参考

    def get_driving_time_seconds(self):
        """从片段起点到当前帧的行驶时间（秒）。"""
        if self.current_pos_data is None:
            return None
        cur = self.current_pos_data.get('_ts')
        if cur is None or self._start_ts is None:
            return None
        try:
            return max(0.0, float((cur - self._start_ts).total_seconds()))
        except Exception:
            return None

    def get_driving_distance(self):
        """从片段起点到当前帧的行驶距离（与 mileage 同单位）。若无 mileage 则返回 None。"""
        if self.current_pos_data is None:
            return None
        if self._start_mileage is None:
            return None
        m = self.current_pos_data.get('mileage')
        try:
            cur = float(m) if m is not None else None
        except Exception:
            cur = None
        if cur is None:
            return None
        return cur - self._start_mileage

    def evaluate_warning(self, prev_truck=None, distance_m=None):
        """基于统一阈值评估当前帧是否预警。"""
        speed_kmh = self.get_speed()
        abs_acc = abs(self.get_acceleration())
        if prev_truck:
            distance_m = distance_m if distance_m is not None else self.get_headway_distance(prev_truck)
        else:
            distance_m = float('inf')

        triggered = []
        if prev_truck and distance_m < PlatoonConfig.WARNING_MIN_DISTANCE_M:
            triggered.append(1)  # 车距过近
        if abs_acc > PlatoonConfig.WARNING_MAX_ABS_ACCEL_MPS2:
            triggered.append(2)  # 急加减速
        if speed_kmh > PlatoonConfig.WARNING_MAX_SPEED_KMH:
            triggered.append(3)  # 超速

        if not triggered:
            self._warning_streak = 0
            self.warning = 0
            self.warning_type = 0
            self.warning_text = ""
            return

        self._warning_streak += 1
        if self._warning_streak < PlatoonConfig.WARNING_DEBOUNCE_FRAMES:
            self.warning = 0
            self.warning_type = 0
            self.warning_text = ""
            return

        self.warning = 1
        if len(triggered) >= 2:
            self.warning_type = 4
            self.warning_text = "多规则触发"
        else:
            self.warning_type = triggered[0]
            self.warning_text = {
                1: "车距过近",
                2: "急加减速",
                3: "超速"
            }.get(self.warning_type, "")
