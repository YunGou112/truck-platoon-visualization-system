import math

import pygame

# 车辆屏幕标记为圆点，半径需与 position / label_renderer 中碰撞框一致
VEHICLE_MARKER_RADIUS = 10


def _draw_vehicle_marker(screen, viz, truck, x, y):
    """以圆点表示车辆位置（替代原卡车位图）。"""
    r = VEHICLE_MARKER_RADIUS
    cx, cy = int(round(x)), int(round(y))
    col = truck.color
    if not isinstance(col, (tuple, list)) or len(col) < 3:
        col = (100, 200, 140)
    else:
        col = tuple(int(c) for c in col[:3])
    pygame.draw.circle(screen, col, (cx, cy), r)
    pygame.draw.circle(screen, (35, 45, 60), (cx, cy), r, 2)
    if truck.warning:
        pygame.draw.circle(screen, (255, 70, 70), (cx, cy), r + 2, 2)
    if str(truck.id) == str(viz.selected_truck_id):
        pygame.draw.circle(screen, (255, 215, 90), (cx, cy), r + 4, 2)


def render_frame(viz, processor):
    viz.screen.blit(viz.background_surface, (0, 0))
    if len(viz._text_cache) > 3000:
        viz._text_cache.clear()

    trucks_now = [t for t in processor.trucks.values() if t.current_pos_data]
    ordered_trucks = viz._order_trucks_by_motion(trucks_now)
    for truck in ordered_trucks:
        sx, sy = processor.geo_to_screen(
            truck.current_pos_data['lon'],
            truck.current_pos_data['lat'],
            viz.width, viz.height,
            viz.view_zoom, viz.view_offset_x, viz.view_offset_y
        )
        truck.current_pos_data['screen_x'] = sx
        truck.current_pos_data['screen_y'] = sy

    if not viz.dragging_map:
        focus_truck = None
        if viz.selected_truck_id is not None:
            for t in ordered_trucks:
                if str(t.id) == str(viz.selected_truck_id):
                    focus_truck = t
                    break
        changed = viz._keep_convoy_in_center_zone(ordered_trucks, focus_truck=focus_truck)
        if changed:
            for truck in ordered_trucks:
                sx, sy = processor.geo_to_screen(
                    truck.current_pos_data['lon'],
                    truck.current_pos_data['lat'],
                    viz.width, viz.height,
                    viz.view_zoom, viz.view_offset_x, viz.view_offset_y
                )
                truck.current_pos_data['screen_x'] = sx
                truck.current_pos_data['screen_y'] = sy

    visible_trucks = [
        t for t in ordered_trucks
        if (
            -viz.screen_margin <= t.current_pos_data.get('screen_x', -9999) <= viz.width + viz.screen_margin
            and -viz.screen_margin <= t.current_pos_data.get('screen_y', -9999) <= viz.height + viz.screen_margin
        )
    ]

    neighbor_distance = {}
    for idx in range(1, len(visible_trucks)):
        rear = visible_trucks[idx]
        front = visible_trucks[idx - 1]
        neighbor_distance[rear.id] = rear.get_headway_distance(front)

    ordered_neighbor_distance = {}
    for idx in range(1, len(ordered_trucks)):
        rear = ordered_trucks[idx]
        front = ordered_trucks[idx - 1]
        ordered_neighbor_distance[rear.id] = rear.get_headway_distance(front)

    warning_messages = []
    for idx, truck in enumerate(visible_trucks):
        prev_truck = visible_trucks[idx - 1] if idx > 0 else None
        truck.evaluate_warning(prev_truck, neighbor_distance.get(truck.id))
        truck.color = (255, 80, 80) if truck.warning else getattr(truck, 'base_color', (80, 220, 120))
        if truck.warning and truck.warning_text:
            warning_messages.append(f"{truck.id[-4:]} {truck.warning_text}")

    viz.latest_warning_text = " | ".join(warning_messages[:2]) if warning_messages else ""
    prev_by_id = {visible_trucks[i].id: visible_trucks[i - 1] for i in range(1, len(visible_trucks))}
    viz._record_anomaly_events(visible_trucks, neighbor_distance, prev_by_id)

    for idx in range(1, len(visible_trucks)):
        front = visible_trucks[idx - 1]
        rear = visible_trucks[idx]
        x1, y1 = front.current_pos_data.get('screen_x', -1), front.current_pos_data.get('screen_y', -1)
        x2, y2 = rear.current_pos_data.get('screen_x', -1), rear.current_pos_data.get('screen_y', -1)
        if not (0 <= x1 <= viz.width and 0 <= y1 <= viz.height and 0 <= x2 <= viz.width and 0 <= y2 <= viz.height):
            continue

        distance_warning = rear.warning_type in (1, 4)
        line_color = (255, 90, 90) if distance_warning else (130, 130, 130)
        line_width = 3 if distance_warning else 1
        pygame.draw.line(viz.screen, line_color, (x1, y1), (x2, y2), line_width)

    for truck in visible_trucks:
        if len(truck.track) > 1:
            recent_track = viz._get_recent_track_segment(truck.track)
            sampled_track = viz._sample_track_dynamic(recent_track)
            points = []
            for p in sampled_track:
                x, y = processor.geo_to_screen(
                    p['lon'], p['lat'],
                    viz.width, viz.height,
                    viz.view_zoom, viz.view_offset_x, viz.view_offset_y
                )
                if 0 <= x <= viz.width and 0 <= y <= viz.height:
                    points.append((x, y))
            if len(points) > 1:
                pygame.draw.lines(viz.screen, (80, 80, 80), False, points, 2)

        if truck.current_pos_data:
            x = truck.current_pos_data.get('screen_x')
            y = truck.current_pos_data.get('screen_y')
            if x is None or y is None:
                x, y = processor.geo_to_screen(
                    truck.current_pos_data['lon'],
                    truck.current_pos_data['lat'],
                    viz.width, viz.height,
                    viz.view_zoom, viz.view_offset_x, viz.view_offset_y
                )
            if 0 <= x <= viz.width and 0 <= y <= viz.height:
                truck.current_pos_data['screen_x'] = x
                truck.current_pos_data['screen_y'] = y
                _draw_vehicle_marker(viz.screen, viz, truck, x, y)

                is_selected = str(truck.id) == str(viz.selected_truck_id)
                speed = truck.get_speed()
                if is_selected and speed > 0 and len(truck.track) >= 2:
                    prev_point = truck.track[-2]
                    curr_point = truck.track[-1]
                    dx = curr_point['lon'] - prev_point['lon']
                    dy = curr_point['lat'] - prev_point['lat']
                    length = (dx**2 + dy**2)**0.5
                    if length > 0:
                        dx /= length
                        dy /= length
                        vec_length = speed * 0.1
                        vec_x = x + dx * vec_length
                        vec_y = y - dy * vec_length
                        pygame.draw.line(viz.screen, (0, 255, 0), (x, y), (int(vec_x), int(vec_y)), 2)
                        arrow_size = 5
                        angle = math.atan2(dy, dx)
                        arrow_x1 = vec_x - arrow_size * math.cos(angle - math.pi / 6)
                        arrow_y1 = vec_y + arrow_size * math.sin(angle - math.pi / 6)
                        arrow_x2 = vec_x - arrow_size * math.cos(angle + math.pi / 6)
                        arrow_y2 = vec_y + arrow_size * math.sin(angle + math.pi / 6)
                        pygame.draw.line(viz.screen, (0, 255, 0), (int(vec_x), int(vec_y)), (int(arrow_x1), int(arrow_y1)), 2)
                        pygame.draw.line(viz.screen, (0, 255, 0), (int(vec_x), int(vec_y)), (int(arrow_x2), int(arrow_y2)), 2)

                acceleration = truck.get_acceleration()
                if is_selected and abs(acceleration) > 0.1:
                    accel_color = (255, 0, 0) if acceleration > 0 else (0, 0, 255)
                    accel_length = abs(acceleration) * 10
                    accel_x = x + 20
                    accel_y = y + 50
                    pygame.draw.line(viz.screen, accel_color, (accel_x, accel_y), (accel_x, accel_y - accel_length), 2)
                    arrow_size = 3
                    pygame.draw.line(viz.screen, accel_color, (accel_x, accel_y - accel_length), (accel_x - arrow_size, accel_y - accel_length + arrow_size), 2)
                    pygame.draw.line(viz.screen, accel_color, (accel_x, accel_y - accel_length), (accel_x + arrow_size, accel_y - accel_length + arrow_size), 2)

    viz._draw_compact_labels(visible_trucks)

    vehicle_tiles = []
    ordered_for_tiles = list(ordered_trucks)
    if viz.selected_truck_id is not None:
        ordered_for_tiles.sort(key=lambda truck: (str(truck.id) != str(viz.selected_truck_id),))

    for idx, truck in enumerate(ordered_for_tiles):
        front_truck = None
        if truck in ordered_trucks:
            original_idx = ordered_trucks.index(truck)
            if original_idx > 0:
                front_truck = ordered_trucks[original_idx - 1]
        gap_m = None if idx == 0 else ordered_neighbor_distance.get(truck.id)
        if front_truck is not None:
            gap_m = ordered_neighbor_distance.get(truck.id)
        vehicle_tiles.append({
            "truck_id": truck.id,
            "warning": bool(truck.warning),
            "selected": str(truck.id) == str(viz.selected_truck_id),
            "speed_kmh": float(truck.get_speed() or 0.0),
            "gap_m": None if gap_m in (None, float("inf")) else float(gap_m),
            "drive_time_s": truck.get_driving_time_seconds() if hasattr(truck, "get_driving_time_seconds") else None,
            "drive_dist": truck.get_driving_distance() if hasattr(truck, "get_driving_distance") else None,
        })

    sidebar_w = 320
    progress_bar_h = 10
    progress_margin = 0
    reserved_bottom = progress_bar_h + progress_margin + 6

    viz.ui_elements_system.draw_vehicle_tiles(
        viz.screen,
        viz.width,
        viz.height,
        vehicle_tiles,
        start_x=sidebar_w,
        bottom_padding=reserved_bottom,
    )
    viz.ui_elements_system.selected_truck_id = viz.selected_truck_id
    viz.ui_elements_system._active_warning_event_key = viz._active_warning_event_key

    sidebar_bottom_y = viz.height - reserved_bottom
    platoon_name = getattr(processor, "current_platoon", "") or ""
    warning_now = sum(1 for t in visible_trucks if getattr(t, "warning", 0))
    by_type = {1: 0, 2: 0, 3: 0, 4: 0}
    for ev in viz.anomaly_events[-2000:]:
        wt = int(ev.get("warning_type", 0) or 0)
        if wt in by_type:
            by_type[wt] += 1

    selected_detail = None
    if viz.selected_truck_id is not None:
        sel = None
        for t in ordered_trucks:
            if str(t.id) == str(viz.selected_truck_id):
                sel = t
                break
        if sel is not None and sel.current_pos_data:
            front = None
            for i, t in enumerate(ordered_trucks):
                if t is sel:
                    front = ordered_trucks[i - 1] if i > 0 else None
                    break
            gap_m = None
            if front is not None:
                gap_m = sel.get_headway_distance(front)
                if gap_m == float("inf"):
                    gap_m = None
            selected_detail = {
                "truck_id": sel.id,
                "speed_kmh": float(sel.get_speed() or 0.0),
                "gap_m": gap_m,
                "drive_time_s": sel.get_driving_time_seconds() if hasattr(sel, "get_driving_time_seconds") else None,
                "drive_dist_km": sel.get_driving_distance() if hasattr(sel, "get_driving_distance") else None,
                "warning_text": getattr(sel, "warning_text", "") if getattr(sel, "warning", 0) else "",
            }

    if processor.min_time and processor.max_time:
        total_dur_s = (processor.max_time - processor.min_time).total_seconds()
    else:
        total_dur_s = None

    sidebar_data = {
        "overview": {
            "platoon": platoon_name if platoon_name else "-",
            "visible_count": len(visible_trucks),
            "total_count": len(processor.trucks),
            "duration_s": total_dur_s,
            "head": (str(ordered_trucks[0].id)[-4:] if ordered_trucks else "-"),
            "tail": (str(ordered_trucks[-1].id)[-4:] if ordered_trucks else "-"),
        },
        "safety": {
            "warning_now": warning_now,
            "warnings_total": len(viz.anomaly_events),
            "by_type": by_type,
        },
        "selected": selected_detail,
        "controls": [
            "Space 播放/暂停",
            "↑↓ 整数调速",
            "←→ 快退/快进(5s)",
            "N/P 预警跳转",
            "R 重置时间/视图",
            "X 取消选中车辆",
            "C 开关配置面板",
            "E 导出当前数据与预警",
            "F 导出所有编队数据",
            "拖动底部进度条 跳转",
            "点击车辆/预警事件 选中车辆",
            "点击预警面板按钮 筛选/排序",
            "滚轮 缩放 | 左键拖拽 平移",
        ],
    }

    viz.ui_elements_system.draw_left_sidebar(
        viz.screen,
        viz.width,
        viz.height,
        sidebar_bottom_y,
        sidebar_data,
        viz.chart_data,
        viz.chart_max_points,
    )

    viz.ui_elements_system.draw_config_panel(
        viz.screen, viz.width, viz.height,
        viz.show_config, viz.config
    )

    visible_warning_events = viz._get_warning_feed_events()
    viz.ui_elements_system.warning_feed_state = viz._get_warning_feed_summary()
    rect = viz.ui_elements_system.draw_warning_feed(
        viz.screen, viz.width, viz.height, visible_warning_events, viz._warning_feed_scroll_px
    )
    if rect is not None:
        viz._warning_feed_rect = rect
    viz._warning_feed_scroll_px = max(0, min(viz._warning_feed_get_max_scroll_px(), int(viz._warning_feed_scroll_px)))

    viz.ui_elements_system.draw_progress_bar_minimal(
        viz.screen,
        viz.width,
        viz.height,
        viz.current_sim_time,
        processor.min_time,
        processor.max_time,
        bar_h=progress_bar_h,
        margin=progress_margin,
    )
    viz._progress_rect = pygame.Rect(0, viz.height - progress_bar_h - progress_margin, viz.width, progress_bar_h)
