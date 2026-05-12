import os

import pandas as pd


def export_data(viz, processor):
    export_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'exports')
    os.makedirs(export_dir, exist_ok=True)

    export_data_rows = []
    for truck in processor.trucks.values():
        if truck.current_pos_data:
            data = truck.current_pos_data.copy()
            data['truck_id'] = truck.id
            data['speed'] = truck.get_speed()
            data['acceleration'] = truck.get_acceleration()
            export_data_rows.append(data)

    if export_data_rows:
        df = pd.DataFrame(export_data_rows)
        filename = f"export_{processor.current_platoon}_{viz.current_sim_time.strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(export_dir, filename)
        df.to_csv(filepath, index=False, encoding='utf-8')
        print(f"数据已导出到: {filepath}")

        try:
            active_trucks = [t for t in processor.trucks.values() if t.current_pos_data]
            ordered = sorted(active_trucks, key=lambda t: t.current_pos_data['lon'], reverse=True)
            neighbor_distance = {}
            for i in range(1, len(ordered)):
                neighbor_distance[ordered[i].id] = ordered[i].get_headway_distance(ordered[i - 1])
            kpis = viz._compute_kpis(ordered, neighbor_distance)
            kpi_row = {
                "timestamp_str": viz.current_sim_time.strftime("%Y-%m-%d %H:%M:%S") if viz.current_sim_time else "",
                "platoon": getattr(processor, "current_platoon", ""),
                **kpis,
            }
            kpi_df = pd.DataFrame([kpi_row])
            kpi_filename = f"kpi_snapshot_{processor.current_platoon}_{viz.current_sim_time.strftime('%Y%m%d_%H%M%S')}.csv"
            kpi_path = os.path.join(export_dir, kpi_filename)
            kpi_df.to_csv(kpi_path, index=False, encoding="utf-8")
            print(f"KPI快照已导出到: {kpi_path}")
        except Exception:
            pass

        if viz.anomaly_events:
            event_filename = f"warnings_{processor.current_platoon}_{viz.current_sim_time.strftime('%Y%m%d_%H%M%S')}.csv"
            event_path = os.path.join(export_dir, event_filename)
            event_df = pd.DataFrame(viz.anomaly_events)
            event_df.to_csv(event_path, index=False, encoding='utf-8')
            print(f"预警事件已导出到: {event_path}")
    else:
        print("没有数据可导出")


def export_all_data(viz, processor):
    export_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'exports')
    os.makedirs(export_dir, exist_ok=True)

    if hasattr(processor, 'all_platoons'):
        for platoon_name, platoon_processor in processor.all_platoons.items():
            export_data_rows = []
            for truck in platoon_processor.trucks.values():
                for point in truck.track:
                    data = point.copy()
                    data['truck_id'] = truck.id
                    export_data_rows.append(data)

            if export_data_rows:
                df = pd.DataFrame(export_data_rows)
                filename = f"export_{platoon_name}.csv"
                filepath = os.path.join(export_dir, filename)
                df.to_csv(filepath, index=False, encoding='utf-8')
                print(f"编队 {platoon_name} 数据已导出到: {filepath}")
        print("所有编队数据导出完成")
    else:
        print("没有找到编队数据")
