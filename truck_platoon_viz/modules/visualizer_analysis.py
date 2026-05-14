import math
from datetime import timedelta

import pandas as pd
import pygame

from config import PlatoonConfig


WARNING_GROUP_MODES = ("time", "truck", "type")
WARNING_TYPE_OPTIONS = (0, 1, 2, 3, 4)
WARNING_FEED_CONTENT_TOP = 96
WARNING_FEED_CONTENT_BOTTOM_MARGIN = 12
WARNING_FEED_LINE_HEIGHT = 48
WARNING_FEED_ITEM_TOP_PADDING = 8


def _warning_type_label(warning_type):
    return {
        0: "全部",
        1: "车距",
        2: "加减速",
        3: "超速",
        4: "多规则",
    }.get(int(warning_type or 0), "未知")


def _get_filtered_warning_events(viz):
    events = list(viz.anomaly_events)
    type_filter = int(getattr(viz, "warning_feed_type_filter", 0) or 0)
    truck_filter = getattr(viz, "warning_feed_truck_filter", "all")

    if type_filter:
        events = [ev for ev in events if int(ev.get("warning_type", 0) or 0) == type_filter]
    if truck_filter not in (None, "", "all"):
        events = [ev for ev in events if str(ev.get("truck_id", "")) == str(truck_filter)]
    return events


def get_warning_feed_events(viz):
    """根据当前筛选和排序配置返回预警列表。"""
    events = _get_filtered_warning_events(viz)
    descending = bool(getattr(viz, "warning_feed_sort_desc", True))
    group_mode = getattr(viz, "warning_feed_group_by", "time")

    def event_ts(event):
        parsed = _get_event_timestamp(event)
        return parsed if parsed is not None else pd.Timestamp.min

    def truck_key(event):
        return str(event.get("truck_id", ""))

    def type_key(event):
        return int(event.get("warning_type", 0) or 0)

    if group_mode == "truck":
        events.sort(key=lambda ev: (truck_key(ev), type_key(ev), event_ts(ev)), reverse=False)
        if descending:
            grouped = {}
            for ev in events:
                grouped.setdefault(truck_key(ev), []).append(ev)
            events = []
            for key in sorted(grouped.keys()):
                events.extend(sorted(grouped[key], key=event_ts, reverse=True))
    elif group_mode == "type":
        events.sort(key=lambda ev: (type_key(ev), truck_key(ev), event_ts(ev)), reverse=False)
        if descending:
            grouped = {}
            for ev in events:
                grouped.setdefault(type_key(ev), []).append(ev)
            events = []
            for key in sorted(grouped.keys()):
                events.extend(sorted(grouped[key], key=event_ts, reverse=True))
    else:
        events.sort(key=event_ts, reverse=descending)

    return events


def get_warning_feed_summary(viz):
    truck_filter = getattr(viz, "warning_feed_truck_filter", "all")
    type_filter = int(getattr(viz, "warning_feed_type_filter", 0) or 0)
    group_mode = getattr(viz, "warning_feed_group_by", "time")
    descending = bool(getattr(viz, "warning_feed_sort_desc", True))
    sort_label = "新→旧" if descending else "旧→新"
    group_label = {"time": "时间", "truck": "车号", "type": "类型"}.get(group_mode, "时间")
    truck_label = "全部" if truck_filter in (None, "", "all") else str(truck_filter)[-4:]
    return {
        "sort_label": f"时间:{sort_label}",
        "group_label": f"分组:{group_label}",
        "type_label": f"类型:{_warning_type_label(type_filter)}",
        "truck_label": f"车辆:{truck_label}",
    }


def cycle_warning_feed_action(viz, action):
    """切换预警窗口的筛选/排序按钮状态。"""
    if action == "sort":
        viz.warning_feed_sort_desc = not bool(getattr(viz, "warning_feed_sort_desc", True))
    elif action == "group":
        current = getattr(viz, "warning_feed_group_by", "time")
        try:
            idx = WARNING_GROUP_MODES.index(current)
        except ValueError:
            idx = 0
        viz.warning_feed_group_by = WARNING_GROUP_MODES[(idx + 1) % len(WARNING_GROUP_MODES)]
    elif action == "type":
        current = int(getattr(viz, "warning_feed_type_filter", 0) or 0)
        try:
            idx = WARNING_TYPE_OPTIONS.index(current)
        except ValueError:
            idx = 0
        viz.warning_feed_type_filter = WARNING_TYPE_OPTIONS[(idx + 1) % len(WARNING_TYPE_OPTIONS)]
    elif action == "truck":
        current = getattr(viz, "warning_feed_truck_filter", "all")
        type_filter = int(getattr(viz, "warning_feed_type_filter", 0) or 0)
        source_events = viz.anomaly_events
        if type_filter:
            source_events = [ev for ev in source_events if int(ev.get("warning_type", 0) or 0) == type_filter]
        unique_trucks = sorted({str(ev.get("truck_id", "")) for ev in source_events if ev.get("truck_id")})
        options = ["all"] + unique_trucks
        if getattr(viz, "selected_truck_id", None):
            selected = str(viz.selected_truck_id)
            if selected not in options:
                options.append(selected)
        try:
            idx = options.index(str(current))
        except ValueError:
            idx = 0
        viz.warning_feed_truck_filter = options[(idx + 1) % len(options)]

    viz._warning_feed_scroll_px = 0
    viz._warning_nav_index = None
    _sync_active_warning_visibility(viz)


def _sync_active_warning_visibility(viz):
    active_key = getattr(viz, "_active_warning_event_key", None)
    if not active_key:
        return
    visible = get_warning_feed_events(viz)
    for idx, event in enumerate(visible):
        event_key = (
            event.get("timestamp_str", ""),
            str(event.get("truck_id", "")),
            int(event.get("warning_type", 0) or 0),
        )
        if event_key == active_key:
            viz._warning_nav_index = idx
            return
    viz._warning_nav_index = None


def order_trucks_by_motion(viz, trucks):
    """根据车辆主运动方向排序，保证头车在前。"""
    if not trucks:
        return []
    if len(trucks) == 1:
        return list(trucks)

    try:
        lat0 = sum(float(t.current_pos_data["lat"]) for t in trucks) / len(trucks)
    except Exception:
        lat0 = 0.0

    cos0 = math.cos(math.radians(lat0)) if lat0 else 1.0
    kx = 111320.0 * cos0
    ky = 110540.0

    def to_xy(point):
        return float(point["lon"]) * kx, float(point["lat"]) * ky

    heading_x = 0.0
    heading_y = 0.0
    heading_count = 0
    for truck in trucks:
        cur = getattr(truck, "current_pos_data", None)
        if not cur:
            continue
        degrees = None
        for key in ("direction", "heading", "yaw"):
            if key in cur and cur[key] is not None:
                degrees = cur[key]
                break
        if degrees is None:
            continue
        try:
            degrees = float(degrees)
        except Exception:
            continue
        theta = math.radians(degrees % 360.0)
        hx = math.sin(theta)
        hy = math.cos(theta)
        try:
            speed = max(0.0, float(cur.get("speed", 0.0) or 0.0))
        except Exception:
            speed = 1.0
        weight = 1.0 + speed
        heading_x += hx * weight
        heading_y += hy * weight
        heading_count += 1

    motion_x = 0.0
    motion_y = 0.0
    motion_count = 0
    for truck in trucks:
        cur = getattr(truck, "current_pos_data", None)
        prev = getattr(truck, "prev_pos_data", None)
        if not cur or not prev:
            continue
        if "lon" not in cur or "lat" not in cur or "lon" not in prev or "lat" not in prev:
            continue
        try:
            x1, y1 = to_xy(cur)
            x0, y0 = to_xy(prev)
        except Exception:
            continue
        dx = x1 - x0
        dy = y1 - y0
        if dx * dx + dy * dy < 1e-6:
            continue
        motion_x += dx
        motion_y += dy
        motion_count += 1

    unit_x = 0.0
    unit_y = 0.0
    if heading_count > 0:
        norm = math.hypot(heading_x, heading_y)
        if norm > 1e-6:
            unit_x = heading_x / norm
            unit_y = heading_y / norm
    elif motion_count > 0:
        norm = math.hypot(motion_x, motion_y)
        if norm > 1e-6:
            unit_x = motion_x / norm
            unit_y = motion_y / norm

    if unit_x == 0.0 and unit_y == 0.0:
        points = []
        for truck in trucks:
            try:
                points.append(to_xy(truck.current_pos_data))
            except Exception:
                continue
        if len(points) >= 2:
            mean_x = sum(p[0] for p in points) / len(points)
            mean_y = sum(p[1] for p in points) / len(points)
            sxx = sum((p[0] - mean_x) ** 2 for p in points) / len(points)
            syy = sum((p[1] - mean_y) ** 2 for p in points) / len(points)
            sxy = sum((p[0] - mean_x) * (p[1] - mean_y) for p in points) / len(points)
            trace = sxx + syy
            det = sxx * syy - sxy * sxy
            disc = max(0.0, trace * trace / 4.0 - det)
            lam1 = trace / 2.0 + math.sqrt(disc)
            if abs(sxy) > 1e-9:
                vec_x = 1.0
                vec_y = (lam1 - sxx) / sxy
            else:
                vec_x, vec_y = (1.0, 0.0) if sxx >= syy else (0.0, 1.0)
            norm = math.hypot(vec_x, vec_y)
            if norm > 1e-6:
                unit_x, unit_y = vec_x / norm, vec_y / norm

    if unit_x != 0.0 or unit_y != 0.0:
        prev_dir = getattr(viz, "_convoy_dir", None)
        if prev_dir is not None:
            prev_x, prev_y = prev_dir
            if unit_x * prev_x + unit_y * prev_y < 0:
                unit_x, unit_y = -unit_x, -unit_y
            alpha = 0.25
            unit_x = (1 - alpha) * prev_x + alpha * unit_x
            unit_y = (1 - alpha) * prev_y + alpha * unit_y
            norm = math.hypot(unit_x, unit_y)
            if norm > 1e-6:
                unit_x, unit_y = unit_x / norm, unit_y / norm
        viz._convoy_dir = (unit_x, unit_y)

    def project(truck):
        try:
            x, y = to_xy(truck.current_pos_data)
        except Exception:
            return -1e18
        return x * unit_x + y * unit_y

    return sorted(trucks, key=project, reverse=True)


def keep_convoy_in_center_zone(viz, ordered_trucks, focus_truck=None):
    """自动平移视图，使车辆保持在屏幕中间区域。"""
    if not ordered_trucks:
        return False

    targets = [focus_truck] if focus_truck is not None else ordered_trucks
    xs = []
    ys = []
    for truck in targets:
        point = getattr(truck, "current_pos_data", None)
        if not point:
            continue
        sx = point.get("screen_x")
        sy = point.get("screen_y")
        if sx is None or sy is None:
            continue
        xs.append(float(sx))
        ys.append(float(sy))
    if not xs:
        return False

    left, right = min(xs), max(xs)
    top, bottom = min(ys), max(ys)
    bbox_w = right - left
    bbox_h = bottom - top

    safe_left = viz.width * 0.25
    safe_right = viz.width * 0.75
    safe_top = viz.height * 0.25
    safe_bottom = viz.height * 0.75
    safe_w = safe_right - safe_left
    safe_h = safe_bottom - safe_top

    dx = 0.0
    dy = 0.0
    if bbox_w > safe_w:
        dx = (safe_left + safe_right) * 0.5 - (left + right) * 0.5
    else:
        if left < safe_left:
            dx = safe_left - left
        elif right > safe_right:
            dx = safe_right - right

    if bbox_h > safe_h:
        dy = (safe_top + safe_bottom) * 0.5 - (top + bottom) * 0.5
    else:
        if top < safe_top:
            dy = safe_top - top
        elif bottom > safe_bottom:
            dy = safe_bottom - bottom

    deadband = 1.2
    if abs(dx) < deadband:
        dx = 0.0
    if abs(dy) < deadband:
        dy = 0.0
    if dx == 0.0 and dy == 0.0:
        return False

    alpha = 0.18
    max_step = 18.0
    viz.view_offset_x += max(-max_step, min(max_step, dx * alpha))
    viz.view_offset_y += max(-max_step, min(max_step, dy * alpha))
    return True


def pick_warning_event_at(viz, pos):
    """根据鼠标位置选中右侧预警事件流中的某条事件。"""
    visible_events = get_warning_feed_events(viz)
    if not visible_events:
        return None
    x, y = pos
    rect = viz._warning_feed_rect
    content_rect = pygame.Rect(
        rect.x + 10,
        rect.y + WARNING_FEED_CONTENT_TOP,
        rect.w - 20,
        rect.bottom - WARNING_FEED_CONTENT_BOTTOM_MARGIN - (rect.y + WARNING_FEED_CONTENT_TOP),
    )
    if not content_rect.collidepoint((x, y)):
        return None

    line_h = WARNING_FEED_LINE_HEIGHT
    max_lines = max(1, content_rect.h // line_h)
    total = len(visible_events)
    max_scroll = max(0, (total - max_lines) * line_h)
    scroll_offset_px = max(0, min(int(viz._warning_feed_scroll_px), int(max_scroll)))
    first_idx_from_bottom = scroll_offset_px // line_h
    start = max(0, total - max_lines - first_idx_from_bottom)
    end = total - first_idx_from_bottom
    visible = visible_events[start:end]

    rel_y = y - (content_rect.y + WARNING_FEED_ITEM_TOP_PADDING)
    if rel_y < 0:
        return None
    idx = int(rel_y // line_h)
    if 0 <= idx < len(visible):
        return visible[idx]
    return None


def warning_feed_get_max_scroll_px(viz):
    """计算右上角预警事件面板当前最大滚动距离。"""
    visible_events = get_warning_feed_events(viz)
    if not visible_events:
        return 0
    rect = viz._warning_feed_rect
    content_h = max(1, rect.bottom - WARNING_FEED_CONTENT_BOTTOM_MARGIN - (rect.y + WARNING_FEED_CONTENT_TOP))
    line_h = WARNING_FEED_LINE_HEIGHT
    max_lines = max(1, content_h // line_h)
    total = len(visible_events)
    return max(0, (total - max_lines) * line_h)


def jump_to_warning_event(viz, processor, event_or_index, pause=True):
    """跳转到指定预警事件并刷新车辆状态。"""
    visible_events = get_warning_feed_events(viz)
    if not visible_events:
        return False

    if isinstance(event_or_index, int):
        if event_or_index < 0 or event_or_index >= len(visible_events):
            return False
        event = visible_events[event_or_index]
        event_index = event_or_index
    else:
        event = event_or_index
        try:
            event_index = visible_events.index(event)
        except ValueError:
            return False

    ts = event.get("timestamp_str")
    if not ts:
        return False
    parsed = event.get("_parsed_ts")
    if parsed is None:
        parsed = pd.to_datetime(ts, errors="coerce")
        event["_parsed_ts"] = parsed
    if pd.isna(parsed):
        return False

    new_time = parsed.to_pydatetime() if hasattr(parsed, "to_pydatetime") else parsed
    viz.current_sim_time = new_time
    viz.selected_truck_id = event.get("truck_id")
    viz._warning_nav_index = event_index
    viz._active_warning_event_key = (
        event.get("timestamp_str", ""),
        str(event.get("truck_id", "")),
        int(event.get("warning_type", 0) or 0),
    )
    if hasattr(viz, "ui_elements_system"):
        viz.ui_elements_system._active_warning_event_key = viz._active_warning_event_key
    if pause:
        viz.is_playing = False

    for truck in processor.trucks.values():
        truck.update(viz.current_sim_time)

    _sync_warning_feed_ui_state(viz)
    _scroll_warning_feed_to_event(viz, event_index)
    return True


def navigate_warning_event(viz, processor, step):
    """跳到上一条或下一条预警事件。step 为 -1 或 +1。"""
    visible_events = get_warning_feed_events(viz)
    if not visible_events:
        return False

    if step == 0:
        return False

    current_index = getattr(viz, "_warning_nav_index", None)
    if current_index is not None and 0 <= current_index < len(visible_events):
        target_index = current_index + (1 if step > 0 else -1)
        if 0 <= target_index < len(visible_events):
            return jump_to_warning_event(viz, processor, target_index, pause=True)

    if viz.current_sim_time is None:
        target_index = 0 if step > 0 else len(visible_events) - 1
        return jump_to_warning_event(viz, processor, target_index, pause=True)

    current_ts = pd.to_datetime(viz.current_sim_time, errors="coerce")
    if pd.isna(current_ts):
        target_index = 0 if step > 0 else len(visible_events) - 1
        return jump_to_warning_event(viz, processor, target_index, pause=True)

    if step > 0:
        for idx, event in enumerate(visible_events):
            event_ts = _get_event_timestamp(event)
            if event_ts is not None and event_ts > current_ts:
                return jump_to_warning_event(viz, processor, idx, pause=True)
    else:
        for idx in range(len(visible_events) - 1, -1, -1):
            event_ts = _get_event_timestamp(visible_events[idx])
            if event_ts is not None and event_ts < current_ts:
                return jump_to_warning_event(viz, processor, idx, pause=True)

    return False


def _get_event_timestamp(event):
    parsed = event.get("_parsed_ts")
    if parsed is None:
        parsed = pd.to_datetime(event.get("timestamp_str", ""), errors="coerce")
        event["_parsed_ts"] = parsed
    if pd.isna(parsed):
        return None
    return parsed


def _scroll_warning_feed_to_event(viz, event_index):
    visible_events = get_warning_feed_events(viz)
    if event_index < 0 or event_index >= len(visible_events):
        return
    rect = viz._warning_feed_rect
    content_h = max(1, rect.bottom - WARNING_FEED_CONTENT_BOTTOM_MARGIN - (rect.y + WARNING_FEED_CONTENT_TOP))
    line_h = WARNING_FEED_LINE_HEIGHT
    max_lines = max(1, content_h // line_h)
    total = len(visible_events)
    reversed_index = total - 1 - event_index
    first_from_bottom = int(viz._warning_feed_scroll_px // line_h)

    if reversed_index < first_from_bottom:
        first_from_bottom = reversed_index
    elif reversed_index >= first_from_bottom + max_lines:
        first_from_bottom = reversed_index - max_lines + 1

    max_scroll = max(0, (total - max_lines) * line_h)
    viz._warning_feed_scroll_px = max(0, min(max_scroll, first_from_bottom * line_h))


def seek_seconds(viz, processor, delta_seconds):
    """快进/后退固定秒数，并立即刷新车辆状态。"""
    if viz.current_sim_time is None:
        viz.current_sim_time = processor.min_time
    try:
        new_time = viz.current_sim_time + timedelta(seconds=float(delta_seconds))
    except (TypeError, ValueError):
        return

    if processor.min_time is not None:
        new_time = max(processor.min_time, new_time)
    if processor.max_time is not None:
        new_time = min(processor.max_time, new_time)

    viz.current_sim_time = new_time
    viz._warning_nav_index = None
    viz._active_warning_event_key = None
    _sync_warning_feed_ui_state(viz)
    for truck in processor.trucks.values():
        truck.update(viz.current_sim_time)


def sample_track(track, max_points=100):
    """对轨迹点进行抽样，减少绘制点数。"""
    if len(track) <= max_points:
        return track
    step = len(track) // max_points
    return [track[i] for i in range(0, len(track), step)]


def sample_track_dynamic(viz, track):
    """按缩放级别动态采样轨迹点。"""
    max_points = int(60 + viz.view_zoom * 70)
    max_points = max(50, min(400, max_points))
    return sample_track(track, max_points=max_points)


def get_recent_track_segment(viz, track):
    """仅保留最近时间窗口的轨迹段。"""
    if not track or viz.current_sim_time is None:
        return track
    cutoff = viz.current_sim_time - timedelta(seconds=viz.track_time_window_seconds)
    start_idx = 0
    for idx in range(len(track) - 1, -1, -1):
        ts = track[idx].get("_ts")
        if ts is not None and ts < cutoff:
            start_idx = idx + 1
            break
    return track[start_idx:]


def record_anomaly_events(viz, ordered_trucks, neighbor_distance, prev_by_id):
    """记录预警事件，使用时间+车辆+类型去重。"""
    for truck in ordered_trucks:
        if not truck.warning:
            continue

        timestamp_str = truck.current_pos_data.get("timestamp_str", "") if truck.current_pos_data else ""
        event_key = (timestamp_str, str(truck.id), int(truck.warning_type))
        if event_key in viz._anomaly_event_keys:
            continue

        viz._anomaly_event_keys.add(event_key)
        prev_truck = prev_by_id.get(truck.id)
        distance_m = None
        if prev_truck is not None:
            distance_m = neighbor_distance.get(truck.id)
            if distance_m is None:
                distance_m = truck.get_headway_distance(prev_truck)

        speed_kmh = float(truck.get_speed() or 0.0)
        accel_mps2 = float(truck.get_acceleration() or 0.0)
        value_parts = []
        severity = "info"
        if truck.warning_type in (1, 4) and distance_m not in (None, float("inf")):
            value_parts.append(f"d={distance_m:.1f}m<{PlatoonConfig.WARNING_MIN_DISTANCE_M:.0f}m")
            severity = "high"
        if truck.warning_type in (2, 4):
            value_parts.append(f"|a|={abs(accel_mps2):.2f}>{PlatoonConfig.WARNING_MAX_ABS_ACCEL_MPS2:.1f}")
            if severity != "high":
                severity = "medium"
        if truck.warning_type in (3, 4):
            value_parts.append(f"v={speed_kmh:.1f}>{PlatoonConfig.WARNING_MAX_SPEED_KMH:.0f}")
            if severity != "high":
                severity = "medium"

        viz.anomaly_events.append(
            {
                "timestamp_str": timestamp_str,
                "truck_id": truck.id,
                "warning_type": int(truck.warning_type or 0),
                "warning_type_label": _warning_type_label(int(truck.warning_type or 0)),
                "warning_text": truck.warning_text,
                "message": truck.warning_text,
                "severity": severity,
                "value_str": " ".join(p for p in value_parts if p).strip(),
                "speed_kmh": speed_kmh,
                "acceleration_mps2": accel_mps2,
                "neighbor_distance_m": None if distance_m in (None, float("inf")) else float(distance_m),
            }
        )

        if len(viz.anomaly_events) > viz._warning_feed_max_events:
            drop = len(viz.anomaly_events) - viz._warning_feed_max_events
            viz.anomaly_events = viz.anomaly_events[drop:]

    _sync_active_warning_visibility(viz)


def _sync_warning_feed_ui_state(viz):
    if hasattr(viz, "ui_elements_system"):
        viz.ui_elements_system.selected_truck_id = viz.selected_truck_id
        viz.ui_elements_system._active_warning_event_key = viz._active_warning_event_key


def compute_kpis(_viz, visible_trucks, neighbor_distance):
    """计算底部 KPI。"""
    if not visible_trucks:
        return {
            "min_neighbor_distance_m": None,
            "overspeed_count": 0,
            "accel_anomaly_count": 0,
        }

    dists = [d for d in neighbor_distance.values() if d is not None and d != float("inf")]
    min_dist = min(dists) if dists else None

    overspeed = 0
    accel_anomaly = 0
    for truck in visible_trucks:
        if (truck.get_speed() or 0.0) > PlatoonConfig.WARNING_MAX_SPEED_KMH:
            overspeed += 1
        if abs(truck.get_acceleration() or 0.0) > PlatoonConfig.WARNING_MAX_ABS_ACCEL_MPS2:
            accel_anomaly += 1

    return {
        "min_neighbor_distance_m": min_dist,
        "overspeed_count": overspeed,
        "accel_anomaly_count": accel_anomaly,
    }


def update_chart_data(viz, processor):
    """更新图表数据。"""
    if not processor.trucks:
        return

    speeds = []
    accelerations = []
    headways = []
    active_trucks = [truck for truck in processor.trucks.values() if truck.current_pos_data]
    for truck in active_trucks:
        speeds.append(truck.get_speed())
        accelerations.append(truck.get_acceleration())

    ordered = sorted(active_trucks, key=lambda truck: truck.current_pos_data["lon"], reverse=True)
    for idx in range(1, len(ordered)):
        rear = ordered[idx]
        front = ordered[idx - 1]
        headway = rear.get_headway_time(front)
        if headway < float("inf"):
            headways.append(headway)

    if speeds:
        avg_speed = sum(speeds) / len(speeds)
        viz.chart_data["speed"].append(avg_speed)
        if len(speeds) > 1:
            variance = sum((speed - avg_speed) ** 2 for speed in speeds) / len(speeds)
            viz.chart_data["speed_variance"].append(variance ** 0.5)

    if accelerations:
        viz.chart_data["acceleration"].append(sum(accelerations) / len(accelerations))

    if headways:
        viz.chart_data["headway"].append(sum(headways) / len(headways))

    for key in viz.chart_data:
        if len(viz.chart_data[key]) > viz.chart_max_points:
            viz.chart_data[key] = viz.chart_data[key][-viz.chart_max_points:]
