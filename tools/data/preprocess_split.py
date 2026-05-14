import csv
import json
import math
import os
from collections import OrderedDict
from datetime import datetime

import pandas as pd

INPUT_FILE = "position-all-260302.json"
OUTPUT_DIR = "data_split"
MAX_OPEN_FILES = 128

FIELDNAMES = [
    "timestamp_ms",
    "timestamp_str",
    "lon_bd09", "lat_bd09",
    "lon_gcj02", "lat_gcj02",
    "lon_wgs84", "lat_wgs84",
    "speed", "direction", "mileage",
    "driving_mode", "driving_model",
    "device_id", "attributes",
    "calc_speed", "vehicle_id"
]


def haversine_distance(lon1, lat1, lon2, lat2):
    r = 6371000
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    d1 = math.radians(lat2 - lat1)
    d2 = math.radians(lon2 - lon1)
    a = math.sin(d1 / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(d2 / 2) ** 2
    return r * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


def compute_speed(prev_ts, prev_lon, prev_lat, cur_ts, cur_lon, cur_lat):
    if None in (prev_ts, prev_lon, prev_lat, cur_ts, cur_lon, cur_lat):
        return 0.0
    dt = (cur_ts - prev_ts) / 1000.0
    if dt <= 0:
        return 0.0
    return round(haversine_distance(prev_lon, prev_lat, cur_lon, cur_lat) / dt, 3)


def format_ts_ms(ts_ms):
    if ts_ms is None:
        return ""
    try:
        dt = datetime.fromtimestamp(ts_ms / 1000.0)
        # 保留毫秒，防止高频数据被压缩到秒级
        return dt.strftime("%Y-%m-%d %H:%M:%S.") + f"{int(ts_ms) % 1000:03d}"
    except Exception:
        return str(ts_ms)


class SplitWriter:
    """按车辆拆分写入，带有限文件句柄缓存。"""

    def __init__(self, output_dir):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self._open_files = OrderedDict()  # vid -> (fh, writer)
        self._last_point = {}  # vid -> (ts, lon, lat)
        self.stats = {"total_lines": 0, "json_ok": 0, "valid_rows": 0, "invalid_rows": 0}

    def _ensure_writer(self, vehicle_id):
        if vehicle_id in self._open_files:
            fh, writer = self._open_files.pop(vehicle_id)
            self._open_files[vehicle_id] = (fh, writer)
            return writer

        if len(self._open_files) >= MAX_OPEN_FILES:
            _, (old_fh, _) = self._open_files.popitem(last=False)
            old_fh.close()

        safe_vid = str(vehicle_id).replace("/", "_")
        file_path = os.path.join(self.output_dir, f"{safe_vid}.csv")
        need_header = not os.path.exists(file_path) or os.path.getsize(file_path) == 0
        fh = open(file_path, "a", newline="", encoding="utf-8-sig")
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        if need_header:
            writer.writeheader()
        self._open_files[vehicle_id] = (fh, writer)
        return writer

    def write(self, vehicle_id, source):
        ts_ms = source.get("dateTime")
        gcj = source.get("gcj02", {}) or {}
        bd = source.get("bd09", {}) or {}

        lon_gcj = gcj.get("lon")
        lat_gcj = gcj.get("lat")
        lon_bd = bd.get("lon")
        lat_bd = bd.get("lat")

        prev_ts, prev_lon, prev_lat = self._last_point.get(vehicle_id, (None, None, None))
        calc_speed = compute_speed(prev_ts, prev_lon, prev_lat, ts_ms, lon_gcj, lat_gcj)
        self._last_point[vehicle_id] = (ts_ms, lon_gcj, lat_gcj)

        attrs = source.get("attributes")
        if isinstance(attrs, dict):
            attrs = json.dumps(attrs, ensure_ascii=False)

        driving_mode = (
            source.get("attributesData", {})
            .get("hexE3Data", {})
            .get("drivingMode")
        )

        row = {
            "timestamp_ms": ts_ms,
            "timestamp_str": format_ts_ms(ts_ms),
            "lon_bd09": lon_bd,
            "lat_bd09": lat_bd,
            "lon_gcj02": lon_gcj,
            "lat_gcj02": lat_gcj,
            "lon_wgs84": source.get("longitude"),
            "lat_wgs84": source.get("latitude"),
            "speed": source.get("speed"),
            "direction": source.get("direction"),
            "mileage": source.get("mileage"),
            "driving_mode": driving_mode,
            "driving_model": source.get("drivingModel"),
            "device_id": source.get("deviceId"),
            "attributes": attrs,
            "calc_speed": calc_speed,
            "vehicle_id": vehicle_id,
        }
        self._ensure_writer(vehicle_id).writerow(row)
        self.stats["valid_rows"] += 1

    def close(self):
        for fh, _ in self._open_files.values():
            fh.close()
        self._open_files.clear()


def split_data_by_vehicle(input_file=INPUT_FILE, output_dir=OUTPUT_DIR):
    writer = SplitWriter(output_dir)
    print(f"开始拆分: {input_file}")
    print(f"输出目录: {output_dir}")

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            for line in f:
                writer.stats["total_lines"] += 1
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    writer.stats["json_ok"] += 1
                except json.JSONDecodeError:
                    writer.stats["invalid_rows"] += 1
                    continue

                src = obj.get("_source", {})
                vid = src.get("vehicleId")
                if not vid or src.get("dateTime") is None:
                    writer.stats["invalid_rows"] += 1
                    continue
                writer.write(str(vid), src)

                if writer.stats["total_lines"] % 200000 == 0:
                    print(
                        f"\r已读 {writer.stats['total_lines']:,} 行，"
                        f"有效 {writer.stats['valid_rows']:,} 行",
                        end=""
                    )
    finally:
        writer.close()

    print("\n拆分完成。")
    print(
        f"总行数: {writer.stats['total_lines']:,}, "
        f"JSON有效: {writer.stats['json_ok']:,}, "
        f"有效记录: {writer.stats['valid_rows']:,}, "
        f"无效记录: {writer.stats['invalid_rows']:,}"
    )


def sort_vehicle_csvs(output_dir=OUTPUT_DIR):
    """对 data_split 下每车文件按 timestamp_ms 排序，并去重（同车同毫秒保留最后一条）。"""
    if not os.path.exists(output_dir):
        print(f"未找到目录: {output_dir}")
        return

    files = [f for f in os.listdir(output_dir) if f.endswith(".csv")]
    if not files:
        print(f"{output_dir} 下没有 CSV")
        return

    print(f"开始排序与去重: {output_dir} （共 {len(files)} 个文件）")
    for i, fn in enumerate(files, start=1):
        fp = os.path.join(output_dir, fn)
        try:
            df = pd.read_csv(fp, low_memory=False)
        except Exception as e:
            print(f"跳过 {fn}：读取失败 {e}")
            continue

        if "timestamp_ms" not in df.columns:
            # 没有 timestamp_ms 的旧文件不处理
            continue

        df["timestamp_ms"] = pd.to_numeric(df["timestamp_ms"], errors="coerce")
        df = df.dropna(subset=["timestamp_ms"])
        df["timestamp_ms"] = df["timestamp_ms"].astype("int64")
        df = df.sort_values("timestamp_ms")
        # 同一毫秒重复记录保留最后一条
        df = df.drop_duplicates(subset=["timestamp_ms"], keep="last")
        df.to_csv(fp, index=False, encoding="utf-8-sig")

        if i % 200 == 0:
            print(f"\r已处理 {i}/{len(files)} 个文件", end="")
    print("\n排序完成。")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Split raw JSON by vehicle")
    parser.add_argument("--input", default=INPUT_FILE)
    parser.add_argument("--output", default=OUTPUT_DIR)
    parser.add_argument("--sort", action="store_true", help="Sort and deduplicate per-vehicle CSVs after split")
    args = parser.parse_args()

    split_data_by_vehicle(args.input, args.output)
    if args.sort:
        sort_vehicle_csvs(args.output)
