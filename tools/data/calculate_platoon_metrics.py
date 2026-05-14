import os
import pandas as pd
import math

class PlatoonAnalyzer:
    def __init__(self):
        self.min_duration_seconds = 5 * 60
    
    def haversine(self, lon1, lat1, lon2, lat2):
        """计算两点间距离(米)"""
        R = 6371000
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    def _ensure_time_columns(self, df):
        if 'timestamp_ms' in df.columns:
            df['timestamp_ms'] = pd.to_numeric(df['timestamp_ms'], errors='coerce')
            df['timestamp_dt'] = pd.to_datetime(df['timestamp_ms'], unit='ms', errors='coerce')
        elif 'timestamp_str' in df.columns:
            df['timestamp_dt'] = pd.to_datetime(df['timestamp_str'], errors='coerce')
            df['timestamp_ms'] = (df['timestamp_dt'].astype('int64') // 10**6).where(~df['timestamp_dt'].isna(), None)
        else:
            raise ValueError("缺少 timestamp_ms 或 timestamp_str 列")
        return df

    def calculate_headway(self, df):
        """计算车头时距和间距"""
        grouped = df.groupby('timestamp_ms')
        
        # 存储计算结果
        headway_distances = []
        headway_times = []
        
        # 对每个时间点计算
        for timestamp, group in grouped:
            if len(group) < 2:
                # 车辆数不足，无法计算
                for _ in range(len(group)):
                    headway_distances.append(0)
                    headway_times.append(0)
                continue
            
            sorted_group = group.sort_values('lon_gcj02')
            
            # 计算车头间距
            distances = [0]  # 第一辆车没有前车
            for i in range(1, len(sorted_group)):
                prev = sorted_group.iloc[i-1]
                curr = sorted_group.iloc[i]
                dist = self.haversine(
                    prev['lon_gcj02'], prev['lat_gcj02'],
                    curr['lon_gcj02'], curr['lat_gcj02']
                )
                distances.append(dist)
            
            # 计算车头时距（基于速度和距离）
            times = [0]  # 第一辆车没有前车
            for i in range(1, len(sorted_group)):
                if sorted_group.iloc[i]['speed'] > 0:
                    time = distances[i] / (sorted_group.iloc[i]['speed'] / 3.6)  # 转换为米/秒
                else:
                    time = 0
                times.append(time)
            
            mapped = {}
            for i, row in enumerate(sorted_group.itertuples()):
                mapped[row.Index] = (distances[i], times[i])
            for idx in group.index:
                d, t = mapped.get(idx, (0, 0))
                headway_distances.append(d)
                headway_times.append(t)
        
        return headway_distances, headway_times
    
    def calculate_acceleration(self, df):
        """计算加速度"""
        accelerations = []
        
        # 按车辆分组
        grouped = df.groupby('vehicle_id')
        
        for vehicle_id, group in grouped:
            sorted_group = group.sort_values('timestamp_ms')
            
            # 计算加速度
            vehicle_accelerations = []
            for i in range(len(sorted_group)):
                if i == 0:
                    # 第一个时间点，无法计算加速度
                    vehicle_accelerations.append(0)
                else:
                    time_diff = (sorted_group.iloc[i]['timestamp_ms'] - sorted_group.iloc[i-1]['timestamp_ms']) / 1000.0
                    
                    if time_diff > 0:
                        # 计算速度差（米/秒）
                        speed_diff = (sorted_group.iloc[i]['speed'] - sorted_group.iloc[i-1]['speed']) / 3.6
                        acceleration = speed_diff / time_diff
                    else:
                        acceleration = 0
                    
                    vehicle_accelerations.append(acceleration)
            
            # 按原始顺序保存结果
            mapped = {idx: vehicle_accelerations[i] for i, idx in enumerate(sorted_group.index)}
            for idx in group.index:
                accelerations.append(mapped.get(idx, 0))
        
        return accelerations
    
    def process_file(self, file_path):
        """处理单个文件"""
        print(f"处理文件: {file_path}")
        
        # 读取文件
        df = pd.read_csv(file_path, low_memory=False)
        df = self._ensure_time_columns(df)

        # 舍弃时长不足 5 分钟的片段（不写回文件）
        try:
            t_min = df['timestamp_dt'].min()
            t_max = df['timestamp_dt'].max()
            duration_seconds = (t_max - t_min).total_seconds() if pd.notna(t_min) and pd.notna(t_max) else 0
        except Exception:
            duration_seconds = 0

        if duration_seconds < self.min_duration_seconds:
            print(f"跳过：时长 {int(duration_seconds)}s < {self.min_duration_seconds}s（5分钟）")
            return
        
        # 计算车头时距和间距
        headway_distances, headway_times = self.calculate_headway(df)
        
        # 计算加速度
        accelerations = self.calculate_acceleration(df)
        
        # 添加新列
        df['headway_distance'] = headway_distances
        df['headway_time'] = headway_times
        df['acceleration'] = accelerations
        
        keep_cols = [c for c in df.columns if c != 'timestamp_dt']
        df[keep_cols].to_csv(file_path, index=False, encoding='utf-8-sig')
        print(f"已更新文件: {file_path}")
    
    def process_all_files(self, directory):
        """处理所有文件"""
        # 找到所有platoon_data.csv文件
        import glob
        files = glob.glob(os.path.join(directory, '**', 'platoon_data.csv'), recursive=True)
        
        print(f"找到 {len(files)} 个文件需要处理")
        
        for file_path in files:
            try:
                self.process_file(file_path)
            except Exception as e:
                print(f"处理文件 {file_path} 时出错: {e}")

if __name__ == "__main__":
    analyzer = PlatoonAnalyzer()
    analyzer.process_all_files('platoon_results')
    print("所有文件处理完成！")
