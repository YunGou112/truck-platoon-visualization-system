import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from truck_platoon_viz.data_processor import DataProcessor


def _write_platoon_csv(folder: Path, rows):
    folder.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(folder / "platoon_data.csv", index=False)


class DataProcessorTests(unittest.TestCase):
    def test_package_import_and_single_platoon_load(self):
        with TemporaryDirectory() as tmp:
            platoon_dir = Path(tmp) / "sample_platoon"
            _write_platoon_csv(
                platoon_dir,
                [
                    {
                        "timestamp_str": "2026-01-01 08:00:00",
                        "vehicle_id": "A",
                        "lon_wgs84": 116.1000,
                        "lat_wgs84": 39.9000,
                        "speed": 60,
                    },
                    {
                        "timestamp_str": "2026-01-01 08:00:01",
                        "vehicle_id": "B",
                        "lon_wgs84": 116.1005,
                        "lat_wgs84": 39.9005,
                        "speed": 58,
                    },
                ],
            )

            processor = DataProcessor(str(platoon_dir))

            self.assertEqual(len(processor.trucks), 2)
            self.assertIsNotNone(processor.min_time)
            self.assertIsNotNone(processor.max_time)
            self.assertLess(processor.min_lon, processor.max_lon)
            self.assertLess(processor.min_lat, processor.max_lat)

    def test_apply_filter_combines_size_and_time_constraints(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "platoon_results"
            _write_platoon_csv(
                root / "3mins_3trucks_ok",
                [
                    {
                        "timestamp_str": "2026-01-01 08:00:00",
                        "vehicle_id": "A",
                        "lon": 116.1,
                        "lat": 39.9,
                        "speed": 60,
                    },
                    {
                        "timestamp_str": "2026-01-01 08:00:00",
                        "vehicle_id": "B",
                        "lon": 116.1005,
                        "lat": 39.9005,
                        "speed": 58,
                    },
                    {
                        "timestamp_str": "2026-01-01 08:00:00",
                        "vehicle_id": "C",
                        "lon": 116.1010,
                        "lat": 39.9010,
                        "speed": 59,
                    },
                ],
            )
            _write_platoon_csv(
                root / "3mins_2trucks_time_only",
                [
                    {
                        "timestamp_str": "2026-01-01 08:00:00",
                        "vehicle_id": "A",
                        "lon": 116.2,
                        "lat": 39.8,
                        "speed": 60,
                    },
                    {
                        "timestamp_str": "2026-01-01 08:00:00",
                        "vehicle_id": "B",
                        "lon": 116.2005,
                        "lat": 39.8005,
                        "speed": 61,
                    },
                ],
            )
            _write_platoon_csv(
                root / "3mins_4trucks_size_only",
                [
                    {
                        "timestamp_str": "2026-01-01 09:00:00",
                        "vehicle_id": truck_id,
                        "lon": 116.3 + idx * 0.0005,
                        "lat": 39.7 + idx * 0.0005,
                        "speed": 62,
                    }
                    for idx, truck_id in enumerate(["A", "B", "C", "D"])
                ],
            )

            processor = DataProcessor(str(root))
            filtered = processor.apply_filter(
                min_size=3,
                max_size=3,
                start_time=pd.Timestamp("2026-01-01 07:59:59"),
                end_time=pd.Timestamp("2026-01-01 08:00:30"),
            )

            self.assertEqual(list(filtered.keys()), ["3mins_3trucks_ok"])


if __name__ == "__main__":
    unittest.main()
