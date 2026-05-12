import pygame
import sys
import math
from datetime import timedelta
import os
import pandas as pd
from config import PlatoonConfig

try:
    from .modules.label_system import LabelSystem
    from .modules.ui_elements import UIElementsSystem
    from .modules.visualizer_export import export_all_data, export_data
    from .modules.visualizer_interaction import handle_event
    from .modules.visualizer_render import render_frame, VEHICLE_MARKER_RADIUS
except ImportError:
    from modules.label_system import LabelSystem
    from modules.ui_elements import UIElementsSystem
    from modules.visualizer_export import export_all_data, export_data
    from modules.visualizer_interaction import handle_event
    from modules.visualizer_render import render_frame, VEHICLE_MARKER_RADIUS


class Visualizer:
    """可视化引擎：负责渲染与交互"""

    def __init__(self, width=1280, height=720):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        pygame.display.set_caption("数据驱动的卡车队列可视化系统 — 兰州交通大学")

        self.clock = pygame.time.Clock()

        # 字体初始化
        try:
            self.font = pygame.font.SysFont("SimHei", 24)
            self.small_font = pygame.font.SysFont("SimHei", 18)
        except:
            self.font = pygame.font.Font(None, 24)
            self.small_font = pygame.font.Font(None, 18)
        
        # 播放控制参数
        self.play_speed = 1
        self.min_play_speed = 1
        self.max_play_speed = 20
        self.is_playing = True
        self.current_sim_time = None

        # --- 新增：视图控制参数 ---
        self.view_zoom = 2.0  # 缩放倍数 - 设置更合理的默认值
        self.view_offset_x = 0  # X轴偏移
        self.view_offset_y = 0  # Y轴偏移
        self.dragging_map = False  # 是否正在拖动地图
        self.last_mouse_pos = (0, 0)  # 上一次鼠标位置

        # 底部进度条（可拖动）
        self.dragging_progress = False
        self._progress_rect = None

        # 配置参数
        self.config = {
            'show_speed_vector': True,
            'show_acceleration': True,
            'show_headway': True,
            'show_platoon_lines': True,
            'max_track_points': 200,
            'vehicle_size': 8,
            'line_width': 2
        }

        # 配置界面
        self.show_config = False
        self.config_rect = pygame.Rect(width - 300, 50, 250, 300)
        
        # 图表数据
        self.chart_data = {
            'speed': [],  # 速度数据
            'acceleration': [],  # 加速度数据
            'headway': [],  # 车头时距数据
            'speed_variance': []  # 速度一致性数据（标准差）
        }
        self.chart_max_points = 100  # 图表最大数据点数量
        self.latest_warning_text = ""
        self.anomaly_events = []
        self._anomaly_event_keys = set()
        # 右侧预警事件流（仅预警）
        self._warning_feed_scroll_px = 0
        self._warning_feed_rect = pygame.Rect(width - 260 - 10, 10, 260, min(320, max(220, height - 120)))
        self._warning_feed_max_events = 2000
        self.selected_truck_id = None
        self._text_cache = {}
        self.chart_update_interval_frames = 3
        self._frame_counter = 0
        self.track_time_window_seconds = 90
        self.screen_margin = 80
        # 编队方向缓存：用于排序防翻转
        self._convoy_dir = None  # (ux, uy) in local meters
        
        # 初始化标签系统
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        self.label_system = LabelSystem(config_path)
        
        # 初始化界面元素系统
        self.ui_elements_system = UIElementsSystem(self.label_system.config)
        self.background_surface = self._build_background_surface()

    def _build_background_surface(self):
        """预渲染静态背景，减少每帧绘制开销。"""
        surface = pygame.Surface((self.width, self.height))
        for y in range(self.height):
            color = (30 + y // 30, 30 + y // 30, 40 + y // 20)
            pygame.draw.line(surface, color, (0, y), (self.width, y))

        grid_size = 50
        for x in range(0, self.width, grid_size):
            pygame.draw.line(surface, (50, 50, 60), (x, 0), (x, self.height), 1)
        for y in range(0, self.height, grid_size):
            pygame.draw.line(surface, (50, 50, 60), (0, y), (self.width, y), 1)
        return surface

    def _render_text_cached(self, text, color, font_name="small"):
        """缓存文本渲染结果，减少重复 font.render 开销。"""
        key = (font_name, text, color)
        cached = self._text_cache.get(key)
        if cached is not None:
            return cached
        font = self.small_font if font_name == "small" else self.font
        surf = font.render(text, True, color)
        self._text_cache[key] = surf
        return surf

    def run(self, processor):
        """主循环"""
        # 1. 检查数据是否有效
        if processor.min_time is None or processor.max_time is None:
            print("错误：未能从数据中获取时间范围。请检查 CSV 文件是否包含 'timestamp' 列。")
            return

        # 2. 【关键修复】初始化当前时间
        self.current_sim_time = processor.min_time

        clock = pygame.time.Clock()
        running = True

        while running:
            # ... (后续代码保持不变) ...
            dt = self.clock.tick(60) / 1000.0
            self._frame_counter += 1

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                self._handle_event(event, processor)

            # 逻辑更新
            if self.is_playing:
                if self.current_sim_time < processor.max_time:
                    self.current_sim_time += timedelta(seconds=self.play_speed * dt)
                    for truck in processor.trucks.values():
                        truck.update(self.current_sim_time)
                    
                    # 图表隔帧更新，降低计算负载
                    if self._frame_counter % self.chart_update_interval_frames == 0:
                        self._update_chart_data(processor)
                else:
                    # 数据运行结束，回到初始状态并暂停
                    self.is_playing = False
                    self.current_sim_time = processor.min_time
                    for truck in processor.trucks.values():
                        truck.reset()
                    # 重置图表数据
                    self.chart_data = {
                        'speed': [],
                        'acceleration': [],
                        'headway': [],
                        'speed_variance': []
                    }
                    print("数据运行结束，已回到初始状态并暂停")
            elif self.dragging_progress:
                # 拖动时间轴时也要持续刷新车辆状态，避免轨迹/图标/卡片“消失”
                for truck in processor.trucks.values():
                    truck.update(self.current_sim_time)

            # 渲染绘制
            self._render(processor)
            pygame.display.flip()

    def _handle_event(self, event, processor):
        handle_event(self, event, processor)

    def _render(self, processor):
        render_frame(self, processor)

    def _seek_to_progress(self, processor, mouse_x):
        """根据鼠标 x 在进度条上的位置跳转时间。"""
        if processor.min_time is None or processor.max_time is None:
            return
        total = (processor.max_time - processor.min_time).total_seconds()
        if total <= 0:
            return
        w = max(1, self.width)
        ratio = max(0.0, min(1.0, float(mouse_x) / float(w)))
        self.current_sim_time = processor.min_time + timedelta(seconds=ratio * total)
        for ttruck in processor.trucks.values():
            ttruck.update(self.current_sim_time)

    def _pick_truck_at(self, pos, processor):
        """根据鼠标位置选中车辆。"""
        mx, my = pos
        for truck in processor.trucks.values():
            if not truck.current_pos_data:
                continue
            sx = truck.current_pos_data.get('screen_x')
            sy = truck.current_pos_data.get('screen_y')
            if sx is None or sy is None:
                continue
            pick_r = VEHICLE_MARKER_RADIUS + 10
            if (sx - mx) ** 2 + (sy - my) ** 2 <= pick_r ** 2:
                return truck
        return None

    def _order_trucks_by_motion(self, trucks):
        """根据车辆的运动主方向对车辆排序（头车在前）。

        逻辑：
        - 优先使用数据自带的方向字段（direction/heading），更“确定”
        - 优先用各车 current_pos_data 与 prev_pos_data 的位移向量估计车队主方向
        - 若主方向过小（例如静止/缺 prev），则回退到位置的主轴方向（PCA）
        - 对方向做“与上一帧对齐”的防翻转
        - 将每车当前位置投影到主方向上排序（投影越大越靠前）
        """
        if not trucks:
            return []
        if len(trucks) == 1:
            return list(trucks)

        # 用平均纬度做局部米制近似
        try:
            lat0 = sum(float(t.current_pos_data["lat"]) for t in trucks) / len(trucks)
        except Exception:
            lat0 = 0.0
        import math
        cos0 = math.cos(math.radians(lat0)) if lat0 else 1.0
        kx = 111320.0 * cos0
        ky = 110540.0

        def to_xy(p):
            return float(p["lon"]) * kx, float(p["lat"]) * ky

        # 0) 优先使用方向字段（direction/heading）
        hx_sum = 0.0
        hy_sum = 0.0
        hcnt = 0
        for t in trucks:
            cur = getattr(t, "current_pos_data", None)
            if not cur:
                continue
            deg = None
            for key in ("direction", "heading", "yaw"):
                if key in cur and cur[key] is not None:
                    deg = cur[key]
                    break
            if deg is None:
                continue
            try:
                deg = float(deg)
            except Exception:
                continue
            # 常见定义：0=北，90=东
            th = math.radians(deg % 360.0)
            # x 为东向，y 为北向
            hx = math.sin(th)
            hy = math.cos(th)
            spd = 1.0
            try:
                spd = max(0.0, float(cur.get("speed", 0.0) or 0.0))
            except Exception:
                spd = 1.0
            w = 1.0 + spd
            hx_sum += hx * w
            hy_sum += hy * w
            hcnt += 1

        # 1) 运动方向平均
        vx_sum = 0.0
        vy_sum = 0.0
        cnt = 0
        for t in trucks:
            cur = getattr(t, "current_pos_data", None)
            prev = getattr(t, "prev_pos_data", None)
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
            vx_sum += dx
            vy_sum += dy
            cnt += 1

        ux = 0.0
        uy = 0.0
        # 优先用 heading 合成方向
        if hcnt > 0:
            norm = math.hypot(hx_sum, hy_sum)
            if norm > 1e-6:
                ux = hx_sum / norm
                uy = hy_sum / norm
        elif cnt > 0:
            norm = math.hypot(vx_sum, vy_sum)
            if norm > 1e-6:
                ux = vx_sum / norm
                uy = vy_sum / norm

        # 2) 回退：位置主轴（2x2 PCA）
        if ux == 0.0 and uy == 0.0:
            pts = []
            for t in trucks:
                try:
                    pts.append(to_xy(t.current_pos_data))
                except Exception:
                    pass
            if len(pts) >= 2:
                mx = sum(p[0] for p in pts) / len(pts)
                my = sum(p[1] for p in pts) / len(pts)
                sxx = sum((p[0] - mx) ** 2 for p in pts) / len(pts)
                syy = sum((p[1] - my) ** 2 for p in pts) / len(pts)
                sxy = sum((p[0] - mx) * (p[1] - my) for p in pts) / len(pts)
                # 最大特征向量方向
                # 对称矩阵 [[sxx, sxy],[sxy, syy]]
                trace = sxx + syy
                det = sxx * syy - sxy * sxy
                disc = max(0.0, trace * trace / 4.0 - det)
                lam1 = trace / 2.0 + math.sqrt(disc)
                # (A - lam I)v=0 => (sxx-lam)*vx + sxy*vy = 0
                if abs(sxy) > 1e-9:
                    vx = 1.0
                    vy = (lam1 - sxx) / sxy
                else:
                    # 无相关：取方差更大轴
                    vx, vy = (1.0, 0.0) if sxx >= syy else (0.0, 1.0)
                norm = math.hypot(vx, vy)
                if norm > 1e-6:
                    ux, uy = vx / norm, vy / norm

        # 2.5) 方向防翻转：与上一帧方向对齐（点积为负则翻转）
        if ux != 0.0 or uy != 0.0:
            prev_dir = getattr(self, "_convoy_dir", None)
            if prev_dir is not None:
                pdx, pdy = prev_dir
                if ux * pdx + uy * pdy < 0:
                    ux, uy = -ux, -uy
            # 轻微平滑，降低抖动
            if prev_dir is not None:
                pdx, pdy = prev_dir
                alpha = 0.25
                ux = (1 - alpha) * pdx + alpha * ux
                uy = (1 - alpha) * pdy + alpha * uy
                norm = math.hypot(ux, uy)
                if norm > 1e-6:
                    ux, uy = ux / norm, uy / norm
            self._convoy_dir = (ux, uy)

        # 3) 投影排序
        def proj(t):
            try:
                x, y = to_xy(t.current_pos_data)
            except Exception:
                return -1e18
            return x * ux + y * uy

        ordered = sorted(trucks, key=proj, reverse=True)
        return ordered

    def _keep_convoy_in_center_zone(self, ordered_trucks, focus_truck=None):
        """自动平移视图，使车辆始终处于屏幕中间 50% 区域内。

        中间 50% 定义：x ∈ [0.25W, 0.75W], y ∈ [0.25H, 0.75H]
        若 focus_truck 不为空，则仅跟随该车，不再考虑其他车辆。
        返回：是否更新了 view_offset。
        """
        if not ordered_trucks:
            return False

        targets = [focus_truck] if focus_truck is not None else ordered_trucks

        xs = []
        ys = []
        for t in targets:
            p = getattr(t, "current_pos_data", None)
            if not p:
                continue
            sx = p.get("screen_x")
            sy = p.get("screen_y")
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

        safe_left = self.width * 0.25
        safe_right = self.width * 0.75
        safe_top = self.height * 0.25
        safe_bottom = self.height * 0.75
        safe_w = safe_right - safe_left
        safe_h = safe_bottom - safe_top

        dx = 0.0
        dy = 0.0

        # 当车队包围盒大于安全区时，改用“中心对齐”避免边界来回拉扯抖动
        if bbox_w > safe_w:
            convoy_cx = (left + right) * 0.5
            safe_cx = (safe_left + safe_right) * 0.5
            dx = safe_cx - convoy_cx
        else:
            if left < safe_left:
                dx = safe_left - left
            elif right > safe_right:
                dx = safe_right - right

        if bbox_h > safe_h:
            convoy_cy = (top + bottom) * 0.5
            safe_cy = (safe_top + safe_bottom) * 0.5
            dy = safe_cy - convoy_cy
        else:
            if top < safe_top:
                dy = safe_top - top
            elif bottom > safe_bottom:
                dy = safe_bottom - bottom

        # 死区：小幅误差不动，减少抖动
        deadband = 1.2
        if abs(dx) < deadband:
            dx = 0.0
        if abs(dy) < deadband:
            dy = 0.0

        if dx == 0.0 and dy == 0.0:
            return False

        # 平滑 + 限速：避免一帧移动过大造成震荡
        alpha = 0.18
        max_step = 18.0
        step_x = max(-max_step, min(max_step, dx * alpha))
        step_y = max(-max_step, min(max_step, dy * alpha))
        self.view_offset_x += step_x
        self.view_offset_y += step_y
        return True

    def _pick_warning_event_at(self, pos):
        """根据鼠标位置选中右侧预警事件流中的某条事件。"""
        if not self.anomaly_events:
            return None
        x, y = pos
        rect = self._warning_feed_rect
        panel_w = rect.w
        panel_x = rect.x
        panel_y = rect.y
        panel_h = rect.h

        content_rect = pygame.Rect(panel_x + 10, panel_y + 46, panel_w - 20, panel_h - 58)
        if not content_rect.collidepoint((x, y)):
            return None

        line_h = 34
        max_lines = max(1, content_rect.h // line_h)
        total = len(self.anomaly_events)
        max_scroll = max(0, (total - max_lines) * line_h)
        scroll_offset_px = max(0, min(int(self._warning_feed_scroll_px), int(max_scroll)))
        first_idx_from_bottom = scroll_offset_px // line_h
        start = max(0, total - max_lines - first_idx_from_bottom)
        end = total - first_idx_from_bottom
        visible = self.anomaly_events[start:end]

        rel_y = y - (content_rect.y + 8)
        if rel_y < 0:
            return None
        idx = int(rel_y // line_h)
        if 0 <= idx < len(visible):
            return visible[idx]
        return None

    def _warning_feed_get_max_scroll_px(self):
        """计算右上角预警事件面板当前的最大可滚动像素。"""
        if not self.anomaly_events:
            return 0
        rect = self._warning_feed_rect
        content_h = max(1, rect.h - 58)
        line_h = 34
        max_lines = max(1, content_h // line_h)
        total = len(self.anomaly_events)
        return max(0, (total - max_lines) * line_h)

    def _seek_seconds(self, processor, delta_seconds):
        """快进/后退固定秒数，并立即刷新车辆位置。"""
        if self.current_sim_time is None:
            self.current_sim_time = processor.min_time
        try:
            new_time = self.current_sim_time + timedelta(seconds=float(delta_seconds))
        except Exception:
            return

        if processor.min_time is not None:
            new_time = max(processor.min_time, new_time)
        if processor.max_time is not None:
            new_time = min(processor.max_time, new_time)

        self.current_sim_time = new_time
        for ttruck in processor.trucks.values():
            ttruck.update(self.current_sim_time)

    def _draw_compact_labels(self, ordered_trucks):
        """绘制紧凑标签，降低遮挡。"""
        existing = []
        for truck in ordered_trucks:
            sx = truck.current_pos_data.get('screen_x')
            sy = truck.current_pos_data.get('screen_y')
            if sx is None or sy is None:
                continue

            compact = f"{str(truck.id)[-4:]} {truck.get_speed():.0f}km/h"
            text = self._render_text_cached(compact, (245, 245, 245), "small")
            w, h = text.get_width() + 8, text.get_height() + 4
            candidates = [
                pygame.Rect(sx + 12, sy - 26, w, h),
                pygame.Rect(sx + 12, sy + 10, w, h),
                pygame.Rect(sx - w - 12, sy - 26, w, h),
                pygame.Rect(sx - w - 12, sy + 10, w, h),
            ]
            label_rect = candidates[0]
            for candidate in candidates:
                if candidate.left < 0 or candidate.top < 0 or candidate.right > self.width or candidate.bottom > self.height:
                    continue
                if any(candidate.colliderect(r) for r in existing):
                    continue
                label_rect = candidate
                break

            bg = (140, 50, 50) if truck.warning else (38, 38, 44)
            pygame.draw.rect(self.screen, bg, label_rect, border_radius=3)
            pygame.draw.rect(self.screen, (220, 220, 220), label_rect, 1, border_radius=3)
            self.screen.blit(text, (label_rect.x + 4, label_rect.y + 2))
            existing.append(label_rect)

            if str(truck.id) == str(self.selected_truck_id):
                detail_lines = [
                    f"ID: {truck.id}",
                    f"v: {truck.get_speed():.1f} km/h",
                    f"a: {truck.get_acceleration():.2f} m/s2",
                    f"warn: {truck.warning_text if truck.warning_text else 'none'}",
                ]
                panel = pygame.Rect(label_rect.x, label_rect.y - 82, 200, 78)
                if panel.top < 0:
                    panel.y = label_rect.bottom + 6
                if panel.right > self.width:
                    panel.x = self.width - panel.width - 8
                pygame.draw.rect(self.screen, (18, 18, 24), panel, border_radius=5)
                pygame.draw.rect(self.screen, (255, 230, 120), panel, 2, border_radius=5)
                for i, line in enumerate(detail_lines):
                    line_surf = self._render_text_cached(line, (245, 245, 245), "small")
                    self.screen.blit(line_surf, (panel.x + 8, panel.y + 6 + i * 16))

    def _sample_track(self, track, max_points=100):
        """对轨迹点进行抽样，减少绘制点数"""
        if len(track) <= max_points:
            return track
        step = len(track) // max_points
        return [track[i] for i in range(0, len(track), step)]

    def _sample_track_dynamic(self, track):
        """按缩放级别动态采样轨迹点。"""
        # 缩小时减少点数，放大时增加点数，限制上限防止过载
        max_points = int(60 + self.view_zoom * 70)
        max_points = max(50, min(400, max_points))
        return self._sample_track(track, max_points=max_points)

    def _get_recent_track_segment(self, track):
        """仅保留最近时间窗口的轨迹段，降低长轨迹绘制成本。"""
        if not track or self.current_sim_time is None:
            return track
        cutoff = self.current_sim_time - timedelta(seconds=self.track_time_window_seconds)
        start_idx = 0
        for i in range(len(track) - 1, -1, -1):
            ts = track[i].get('_ts')
            if ts is not None and ts < cutoff:
                start_idx = i + 1
                break
        return track[start_idx:]

    def _export_data(self, processor):
        export_data(self, processor)

    def _record_anomaly_events(self, ordered_trucks, neighbor_distance, prev_by_id):
        """记录预警事件（仅预警），使用时间+车辆+类型去重。"""
        for truck in ordered_trucks:
            if not truck.warning:
                continue

            timestamp_str = truck.current_pos_data.get('timestamp_str', '') if truck.current_pos_data else ''
            event_key = (timestamp_str, str(truck.id), int(truck.warning_type))
            if event_key in self._anomaly_event_keys:
                continue

            self._anomaly_event_keys.add(event_key)

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

            self.anomaly_events.append({
                'timestamp_str': timestamp_str,
                'truck_id': truck.id,
                'warning_type': int(truck.warning_type or 0),
                'warning_text': truck.warning_text,
                'message': truck.warning_text,
                'severity': severity,
                'value_str': " ".join([p for p in value_parts if p]).strip(),
                'speed_kmh': speed_kmh,
                'acceleration_mps2': accel_mps2,
                'neighbor_distance_m': None if distance_m in (None, float("inf")) else float(distance_m),
            })

            if len(self.anomaly_events) > self._warning_feed_max_events:
                drop = len(self.anomaly_events) - self._warning_feed_max_events
                self.anomaly_events = self.anomaly_events[drop:]

    def _compute_kpis(self, visible_trucks, neighbor_distance):
        """计算底部 KPI：最小相邻车距/超速车辆数/加速度异常车辆数。"""
        if not visible_trucks:
            return {
                "min_neighbor_distance_m": None,
                "overspeed_count": 0,
                "accel_anomaly_count": 0,
            }

        dists = [d for d in neighbor_distance.values() if d is not None and d != float("inf")]
        min_dist = min(dists) if dists else None

        overspeed = 0
        accel_anom = 0
        for t in visible_trucks:
            if (t.get_speed() or 0.0) > PlatoonConfig.WARNING_MAX_SPEED_KMH:
                overspeed += 1
            if abs(t.get_acceleration() or 0.0) > PlatoonConfig.WARNING_MAX_ABS_ACCEL_MPS2:
                accel_anom += 1

        return {
            "min_neighbor_distance_m": min_dist,
            "overspeed_count": overspeed,
            "accel_anomaly_count": accel_anom,
        }

    def _export_all_data(self, processor):
        export_all_data(self, processor)

    def _update_chart_data(self, processor):
        """更新图表数据"""
        if not processor.trucks:
            return
        
        # 收集速度和加速度数据
        speeds = []
        accelerations = []
        headways = []

        active_trucks = [t for t in processor.trucks.values() if t.current_pos_data]
        for truck in active_trucks:
            speeds.append(truck.get_speed())
            accelerations.append(truck.get_acceleration())

        # 使用相邻车辆计算平均车头时距，替代 O(n^2) 全对全计算
        ordered = sorted(active_trucks, key=lambda t: t.current_pos_data['lon'], reverse=True)
        for i in range(1, len(ordered)):
            rear = ordered[i]
            front = ordered[i - 1]
            headway = rear.get_headway_time(front)
            if headway < float('inf'):
                headways.append(headway)
        
        # 计算平均值
        if speeds:
            avg_speed = sum(speeds) / len(speeds)
            self.chart_data['speed'].append(avg_speed)
            
            # 计算速度一致性（标准差）
            if len(speeds) > 1:
                variance = sum((s - avg_speed) ** 2 for s in speeds) / len(speeds)
                self.chart_data['speed_variance'].append(variance ** 0.5)  # 标准差
        
        if accelerations:
            avg_accel = sum(accelerations) / len(accelerations)
            self.chart_data['acceleration'].append(avg_accel)
        
        if headways:
            avg_headway = sum(headways) / len(headways)
            self.chart_data['headway'].append(avg_headway)
        
        # 限制数据点数量
        for key in self.chart_data:
            if len(self.chart_data[key]) > self.chart_max_points:
                self.chart_data[key] = self.chart_data[key][-self.chart_max_points:]

    def _draw_config(self):
        """绘制配置界面"""
        if not self.show_config:
            return
        
        # 绘制配置面板 - 带圆角和阴影效果
        pygame.draw.rect(self.screen, (30, 30, 30), (self.config_rect.x + 5, self.config_rect.y + 5, self.config_rect.w, self.config_rect.h), border_radius=8)
        pygame.draw.rect(self.screen, (50, 50, 60), self.config_rect, border_radius=8)
        pygame.draw.rect(self.screen, (100, 100, 120), self.config_rect, 2, border_radius=8)
        
        # 绘制标题 - 带背景
        title_rect = pygame.Rect(self.config_rect.x, self.config_rect.y, self.config_rect.w, 40)
        pygame.draw.rect(self.screen, (60, 60, 80), title_rect, border_radius=8)
        title = self.font.render("配置", True, (255, 255, 255))
        title_x = self.config_rect.x + (self.config_rect.w - title.get_width()) // 2
        self.screen.blit(title, (title_x, self.config_rect.y + 10))
        
        # 绘制配置项
        y_offset = 60
        config_items = [
            ('show_speed_vector', '速度向量'),
            ('show_acceleration', '加速度指示器'),
            ('show_headway', '车头时距'),
            ('show_platoon_lines', '编队连接线'),
            ('max_track_points', '轨迹点数量'),
            ('vehicle_size', '车辆大小'),
            ('line_width', '线条宽度')
        ]
        
        for key, label in config_items:
            text = self.small_font.render(label, True, (255, 255, 255))
            self.screen.blit(text, (self.config_rect.x + 20, self.config_rect.y + y_offset))
            
            # 绘制开关或滑块
            if isinstance(self.config[key], bool):
                # 绘制开关 - 更美观的设计
                switch_rect = pygame.Rect(self.config_rect.x + 160, self.config_rect.y + y_offset - 2, 60, 24)
                pygame.draw.rect(self.screen, (80, 80, 90), switch_rect, border_radius=12)
                if self.config[key]:
                    pygame.draw.rect(self.screen, (0, 150, 255), switch_rect, border_radius=12)
                    # 开关按钮
                    pygame.draw.circle(self.screen, (255, 255, 255), (switch_rect.x + 48, switch_rect.y + 12), 8)
                else:
                    pygame.draw.circle(self.screen, (200, 200, 200), (switch_rect.x + 12, switch_rect.y + 12), 8)
            else:
                # 绘制值 - 带背景
                value_rect = pygame.Rect(self.config_rect.x + 160, self.config_rect.y + y_offset - 2, 60, 24)
                pygame.draw.rect(self.screen, (80, 80, 90), value_rect, border_radius=4)
                value_text = self.small_font.render(str(self.config[key]), True, (255, 255, 255))
                value_x = value_rect.x + (value_rect.w - value_text.get_width()) // 2
                self.screen.blit(value_text, (value_x, value_rect.y + 3))
            
            y_offset += 35
        
        # 绘制提示 - 带背景
        hint_rect = pygame.Rect(self.config_rect.x, self.config_rect.y + y_offset, self.config_rect.w, 30)
        pygame.draw.rect(self.screen, (60, 60, 80), hint_rect, border_radius=4)
        hint = self.small_font.render("按C键关闭配置界面", True, (180, 180, 180))
        hint_x = self.config_rect.x + (self.config_rect.w - hint.get_width()) // 2
        self.screen.blit(hint, (hint_x, self.config_rect.y + y_offset + 5))

    def _draw_chart(self):
        """绘制实时图表"""
        # 图表区域 - 右上角
        chart_rect = pygame.Rect(self.width - 320, 10, 300, 200)
        
        # 绘制图表背景
        pygame.draw.rect(self.screen, (40, 40, 50), chart_rect, border_radius=5)
        pygame.draw.rect(self.screen, (80, 80, 100), chart_rect, 1, border_radius=5)
        
        # 绘制标题
        chart_title = self.font.render("编队性能指标", True, (255, 255, 255))
        self.screen.blit(chart_title, (chart_rect.x + 10, chart_rect.y + 5))
        
        # 绘制平均速度图表
        self._draw_line_chart(chart_rect, 'speed', (0, 255, 0), "平均速度 (km/h)", 0, 120)
        
        # 绘制平均车头时距图表
        self._draw_line_chart(chart_rect, 'headway', (0, 120, 255), "平均车头时距 (s)", 0, 10, offset_y=60)
        
        # 绘制编队一致性图表（速度差异）
        self._draw_line_chart(chart_rect, 'speed_variance', (255, 165, 0), "速度一致性", 0, 20, offset_y=120)

    def _draw_line_chart(self, chart_rect, data_key, color, label, min_val, max_val, offset_y=0):
        """绘制折线图"""
        data = self.chart_data.get(data_key, [])
        if not data:
            return
        
        # 图表区域
        chart_width = chart_rect.w - 60
        chart_height = 30
        chart_x = chart_rect.x + 50
        chart_y = chart_rect.y + 30 + offset_y
        
        # 绘制标签
        label_surf = self.small_font.render(label, True, (200, 200, 200))
        self.screen.blit(label_surf, (chart_rect.x + 10, chart_y + 5))
        
        # 绘制坐标轴
        pygame.draw.line(self.screen, (100, 100, 120), (chart_x, chart_y), (chart_x + chart_width, chart_y), 1)
        pygame.draw.line(self.screen, (100, 100, 120), (chart_x, chart_y), (chart_x, chart_y + chart_height), 1)
        
        # 动态调整Y轴范围
        if data_key == 'headway' and max(data) > 10:
            # 车头时距超过10秒，动态调整范围
            max_val = min(max(data) * 1.2, 60)  # 最大60秒
        
        # 绘制数据点和线
        if len(data) > 1:
            points = []
            for i, value in enumerate(data):
                # 归一化数据，确保值在范围内
                clamped_value = max(min_val, min(value, max_val))
                normalized_value = (clamped_value - min_val) / (max_val - min_val)
                # 转换为屏幕坐标
                x = chart_x + (i / (len(data) - 1)) * chart_width
                y = chart_y + chart_height - (normalized_value * chart_height)
                points.append((x, y))
            
            # 绘制折线
            pygame.draw.lines(self.screen, color, False, points, 2)
            
            # 绘制最后一个数据点
            if points:
                last_x, last_y = points[-1]
                pygame.draw.circle(self.screen, color, (int(last_x), int(last_y)), 3)
                
                # 显示当前值 - 右对齐
                value_text = self.small_font.render(f"{data[-1]:.2f}", True, color)
                # 计算右对齐位置
                text_x = chart_rect.x + chart_rect.w - value_text.get_width() - 10
                self.screen.blit(value_text, (text_x, chart_y + 5))

    def _draw_ui(self, processor):
        # 绘制信息面板背景 - 优化布局
        info_panel_rect = pygame.Rect(10, 10, 280, 180)
        # 半透背景
        pygame.draw.rect(self.screen, (40, 40, 50, 220), info_panel_rect, border_radius=5)
        # 边框
        pygame.draw.rect(self.screen, (80, 80, 100), info_panel_rect, 2, border_radius=5)

        # 时间信息
        time_str = self.current_sim_time.strftime("%Y-%m-%d %H:%M:%S")
        time_surf = self.font.render(f"时间: {time_str}", True, (255, 255, 255))
        self.screen.blit(time_surf, (20, 25))

        # 播放状态
        status = "暂停" if not self.is_playing else "播放"
        speed_surf = self.font.render(f"速度: {self.play_speed:.1f} x ({status})", True, (255, 255, 255))
        self.screen.blit(speed_surf, (20, 55))

        # 显示缩放比例
        zoom_surf = self.font.render(f"缩放: {self.view_zoom:.2f} x", True, (255, 255, 255))
        self.screen.blit(zoom_surf, (20, 85))

        # 编队信息
        if hasattr(processor, 'current_platoon') and processor.current_platoon:
            # 提取编队名称中的关键信息
            platoon_name = processor.current_platoon
            if 'trucks' in platoon_name:
                # 格式如 "8mins_4trucks_27"
                parts = platoon_name.split('_')
                if len(parts) >= 3:
                    time_info = parts[0]
                    truck_count = parts[1]
                    platoon_id = parts[2]
                    platoon_surf = self.font.render(f"编队: {truck_count} {time_info}", True, (255, 255, 255))
                else:
                    platoon_surf = self.font.render(f"编队: {platoon_name}", True, (255, 255, 255))
            else:
                platoon_surf = self.font.render(f"编队: {platoon_name}", True, (255, 255, 255))
            self.screen.blit(platoon_surf, (20, 115))
        
        # 卡车数量
        trucks_count = len(processor.trucks)
        trucks_surf = self.font.render(f"卡车数量: {trucks_count}", True, (255, 255, 255))
        self.screen.blit(trucks_surf, (20, 145))

        # 绘制操作提示面板
        help_panel_rect = pygame.Rect(10, self.height - 60, self.width - 20, 40)
        pygame.draw.rect(self.screen, (40, 40, 50), help_panel_rect, border_radius=5)
        pygame.draw.rect(self.screen, (80, 80, 100), help_panel_rect, 1, border_radius=5)
        
        # 操作提示 - 分两行显示，用竖线分隔，调整字体大小，文字居中对齐
        help_text1 = "空格: 暂停 | 上/下: 调速 | R: 重置 | 滚轮: 缩放 | 左键拖动: 平移"
        help_text2 = "左右箭头: 切换编队 | C: 配置 | E: 导出当前 | F: 导出所有"
        # 创建更小的字体
        small_font = pygame.font.Font(None, 11)
        help_surf1 = small_font.render(help_text1, True, (150, 150, 150))
        help_surf2 = small_font.render(help_text2, True, (150, 150, 150))
        # 计算居中位置
        text_x1 = (self.width - help_surf1.get_width()) // 2
        text_x2 = (self.width - help_surf2.get_width()) // 2
        self.screen.blit(help_surf1, (text_x1, self.height - 50))
        self.screen.blit(help_surf2, (text_x2, self.height - 30))

        # 进度条
        pygame.draw.rect(self.screen, (50, 50, 60), self.progress_bar_rect, border_radius=10)
        total_seconds = (processor.max_time - processor.min_time).total_seconds()
        if total_seconds > 0:
            current_seconds = (self.current_sim_time - processor.min_time).total_seconds()
            ratio = current_seconds / total_seconds
            fill_width = int(self.progress_bar_rect.w * ratio)
            fill_rect = pygame.Rect(self.progress_bar_rect.x, self.progress_bar_rect.y, fill_width,
                                    self.progress_bar_rect.h)
            # 进度条渐变色
            blue_component = 120 + int(135 * ratio)
            blue_component = max(0, min(255, blue_component))  # 确保颜色值在有效范围内
            fill_color = (0, blue_component, 215)
            pygame.draw.rect(self.screen, fill_color, fill_rect, border_radius=10)
        pygame.draw.rect(self.screen, (100, 100, 120), self.progress_bar_rect, 2, border_radius=10)
