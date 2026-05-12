import math
import os
from collections import defaultdict

import pandas as pd

from config import PlatoonConfig


class GeoUtils:
    @staticmethod
    def haversine(lon1, lat1, lon2, lat2):
        r = 6371000
        p1, p2 = math.radians(lat1), math.radians(lat2)
        d1 = math.radians(lat2 - lat1)
        d2 = math.radians(lon2 - lon1)
        a = math.sin(d1 / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(d2 / 2) ** 2
        return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    @staticmethod
    def direction_diff(d1, d2):
        diff = abs((d1 or 0) - (d2 or 0))
        return min(diff, 360 - diff)


class PlatoonDetector:
    def __init__(self):
        self.cfg = PlatoonConfig()

    def _representative_points(self, window_df):
        """
        每个窗口内每车仅保留一个代表点，避免同车多时刻混算误判。
        这里使用窗口内最新点。
        """
        ordered = window_df.sort_values("timestamp_ms")
        rep = ordered.groupby("vehicle_id", as_index=False).tail(1)
        return rep

    def get_clusters(self, window_df):
        rep = self._representative_points(window_df)
        if len(rep) < self.cfg.MIN_PLATOON_SIZE:
            return []

        points = rep[["vehicle_id", "lon_gcj02", "lat_gcj02", self.cfg.SPEED_COLUMN, "direction"]].values
        n = len(points)
        adj = defaultdict(set)

        for i in range(n):
            for j in range(i + 1, n):
                id1, lon1, lat1, spd1, dir1 = points[i]
                id2, lon2, lat2, spd2, dir2 = points[j]
                if None in (lon1, lat1, lon2, lat2):
                    continue
                if GeoUtils.haversine(lon1, lat1, lon2, lat2) > self.cfg.MAX_DISTANCE_METERS:
                    continue
                if abs((spd1 or 0) - (spd2 or 0)) > self.cfg.MAX_SPEED_DIFF:
                    continue
                if GeoUtils.direction_diff(dir1, dir2) > self.cfg.MAX_DIRECTION_DIFF:
                    continue
                adj[id1].add(id2)
                adj[id2].add(id1)

        visited, clusters = set(), []
        for i in range(n):
            start = points[i][0]
            if start in visited:
                continue
            stack = [start]
            visited.add(start)
            comp = set()
            while stack:
                node = stack.pop()
                comp.add(node)
                for nb in adj[node]:
                    if nb not in visited:
                        visited.add(nb)
                        stack.append(nb)
            if len(comp) >= self.cfg.MIN_PLATOON_SIZE:
                clusters.append(comp)
        return clusters


class SegmentManager:
    def __init__(self):
        self.active = {}
        self.window_count = defaultdict(int)
        self.completed = []

    def update(self, t_window, clusters):
        cur = set()
        for c in clusters:
            key = frozenset(c)
            cur.add(key)
            if key not in self.active:
                self.active[key] = t_window
                self.window_count[key] = 1
            else:
                self.window_count[key] += 1

        to_close = [k for k in self.active if k not in cur]
        for k in to_close:
            self.completed.append((self.active[k], t_window, list(k), self.window_count[k]))
            del self.active[k]
            del self.window_count[k]

    def finalize(self, end_time):
        for k, start in self.active.items():
            self.completed.append((start, end_time, list(k), self.window_count[k]))


class DataProcessor:
    def __init__(self):
        self.cfg = PlatoonConfig()
        self.detector = PlatoonDetector()
        self.manager = SegmentManager()
        self.stats = {"rows_loaded": 0, "rows_used_for_windows": 0, "windows": 0}

    def load_data(self):
        input_dir = self.cfg.INPUT_DIR
        if not os.path.exists(input_dir):
            print(f"错误：未找到输入目录 {input_dir}")
            return None

        files = [f for f in os.listdir(input_dir) if f.endswith(".csv")]
        if not files:
            print(f"错误：{input_dir} 下没有 CSV")
            return None

        all_df = []
        print(f"正在加载 {len(files)} 个车辆文件...")
        usecols = [
            "timestamp_ms", "timestamp_str", "vehicle_id",
            "lon_bd09", "lat_bd09", "lon_gcj02", "lat_gcj02", "lon_wgs84", "lat_wgs84",
            "speed", "direction", "mileage", "driving_mode", "driving_model",
            "device_id", "attributes", "calc_speed"
        ]
        for i, fn in enumerate(files, start=1):
            fp = os.path.join(input_dir, fn)
            try:
                df = pd.read_csv(fp, usecols=lambda c: c in usecols, low_memory=False)
            except Exception:
                df = pd.read_csv(fp, low_memory=False)
            if "vehicle_id" not in df.columns:
                df["vehicle_id"] = fn.replace(".csv", "")
            if "timestamp_ms" not in df.columns and "timestamp_str" in df.columns:
                ts = pd.to_datetime(df["timestamp_str"], errors="coerce")
                df["timestamp_ms"] = (ts.astype("int64") // 10**6).where(~ts.isna(), None)
            all_df.append(df)
            if i % 200 == 0:
                print(f"\r已加载 {i}/{len(files)} 个文件", end="")

        full = pd.concat(all_df, ignore_index=True)
        full = full.dropna(subset=["timestamp_ms", "lon_gcj02", "lat_gcj02"])
        full["timestamp_ms"] = full["timestamp_ms"].astype("int64")
        full["timestamp_dt"] = pd.to_datetime(full["timestamp_ms"], unit="ms", errors="coerce")
        full = full.dropna(subset=["timestamp_dt"]).sort_values(["vehicle_id", "timestamp_ms"])
        # 同车同毫秒只保留最后一条，避免乱序/重复导致误判
        full = full.drop_duplicates(subset=["vehicle_id", "timestamp_ms"], keep="last")
        full = full.sort_values("timestamp_ms")
        self.stats["rows_loaded"] = len(full)
        return full

    def run(self):
        df = self.load_data()
        if df is None or df.empty:
            return

        print(f"数据范围: {df['timestamp_dt'].min()} ~ {df['timestamp_dt'].max()}")
        print(f"总记录: {len(df):,}, 车辆数: {df['vehicle_id'].nunique()}")

        df["time_window"] = df["timestamp_dt"].dt.floor(f"{self.cfg.TIME_WINDOW_SECONDS}s")
        grouped = df.groupby("time_window", sort=True)
        total = len(grouped)
        self.stats["windows"] = total

        for i, (t_window, g) in enumerate(grouped, start=1):
            self.stats["rows_used_for_windows"] += len(g)
            clusters = self.detector.get_clusters(g)
            self.manager.update(t_window, clusters)
            if i % 200 == 0:
                print(f"\r窗口处理进度 {i}/{total}", end="")

        self.manager.finalize(df["timestamp_dt"].max())
        print("\n窗口扫描完成，开始保存结果...")
        self._save_results(df)
        self._print_stats()

    def _save_results(self, full_df):
        os.makedirs(self.cfg.OUTPUT_BASE_DIR, exist_ok=True)
        min_windows = getattr(self.cfg, "MIN_CONTINUOUS_WINDOWS", 3)
        keep, skip = 0, 0

        for start, end, vids, windows in self.manager.completed:
            dur = (end - start).total_seconds()
            if dur < self.cfg.MIN_DURATION_SECONDS or len(vids) < self.cfg.MIN_PLATOON_SIZE or windows < min_windows:
                skip += 1
                continue

            seg = full_df[
                (full_df["vehicle_id"].isin(vids))
                & (full_df["timestamp_dt"] >= start)
                & (full_df["timestamp_dt"] <= end)
            ].copy()
            if seg.empty:
                skip += 1
                continue

            folder = f"{int(dur // 60)}mins_{len(vids)}trucks"
            save_dir = os.path.join(self.cfg.OUTPUT_BASE_DIR, folder)
            idx = 1
            while os.path.exists(save_dir):
                save_dir = os.path.join(self.cfg.OUTPUT_BASE_DIR, f"{folder}_{idx}")
                idx += 1
            os.makedirs(save_dir)

            seg = seg.sort_values(["timestamp_ms", "vehicle_id"])
            cols_drop = [c for c in ["timestamp_dt", "time_window"] if c in seg.columns]
            seg.drop(columns=cols_drop).to_csv(
                os.path.join(save_dir, "platoon_data.csv"),
                index=False,
                encoding="utf-8-sig",
            )
            print(f"已保存: {os.path.basename(save_dir)} (时长 {int(dur)}s, 窗口 {windows})")
            keep += 1

        print(f"完成：生成 {keep} 个编队包，过滤 {skip} 个片段")

    def _print_stats(self):
        print("==== 数据利用率统计 ====")
        print(f"加载有效记录: {self.stats['rows_loaded']:,}")
        print(f"参与窗口扫描记录: {self.stats['rows_used_for_windows']:,}")
        print(f"窗口数: {self.stats['windows']:,}")
        if self.stats["rows_loaded"] > 0:
            ratio = self.stats["rows_used_for_windows"] / self.stats["rows_loaded"] * 100
            print(f"窗口利用率: {ratio:.2f}%")


if __name__ == "__main__":
    DataProcessor().run()
