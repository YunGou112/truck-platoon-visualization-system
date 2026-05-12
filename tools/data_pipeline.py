"""
Unified data pipeline entrypoint.

This script consolidates previous standalone scripts:
- preprocess_split.py
- platoon_analyzer.py
- calculate_platoon_metrics.py
"""

import argparse
import sys


def run_split():
    from preprocess_split import split_data_by_vehicle
    split_data_by_vehicle()


def run_analyze():
    from platoon_analyzer import DataProcessor
    processor = DataProcessor()
    processor.run()


def run_metrics():
    from calculate_platoon_metrics import PlatoonAnalyzer
    analyzer = PlatoonAnalyzer()
    analyzer.process_all_files("platoon_results")


def run_all():
    run_split()
    run_analyze()
    run_metrics()


def main():
    parser = argparse.ArgumentParser(description="Truck platoon data pipeline")
    parser.add_argument(
        "stage",
        choices=["split", "analyze", "metrics", "all"],
        default="all",
        nargs="?",
        help="Pipeline stage to run",
    )
    args = parser.parse_args()

    if args.stage == "split":
        run_split()
    elif args.stage == "analyze":
        run_analyze()
    elif args.stage == "metrics":
        run_metrics()
    else:
        run_all()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Pipeline failed: {e}")
        sys.exit(1)
