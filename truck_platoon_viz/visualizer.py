import logging
import pygame
import sys
from datetime import timedelta
import os

try:
    from .modules.label_system import LabelSystem
    from .modules.ui_elements import UIElementsSystem
    from .modules.visualizer_analysis import (
        cycle_warning_feed_action,
        compute_kpis,
        get_warning_feed_events,
        get_warning_feed_summary,
        get_recent_track_segment,
        jump_to_warning_event,
        keep_convoy_in_center_zone,
        navigate_warning_event,
        order_trucks_by_motion,
        pick_warning_event_at,
        record_anomaly_events,
        sample_track,
        sample_track_dynamic,
        seek_seconds,
        update_chart_data,
        warning_feed_get_max_scroll_px,
    )
    from .modules.visualizer_export import export_all_data, export_data
    from .modules.visualizer_interaction import handle_event
    from .modules.visualizer_labels import draw_compact_labels
    from .modules.visualizer_render import render_frame, VEHICLE_MARKER_RADIUS
except ImportError:
    from modules.label_system import LabelSystem
    from modules.ui_elements import UIElementsSystem
    from modules.visualizer_analysis import (
        cycle_warning_feed_action,
        compute_kpis,
        get_warning_feed_events,
        get_warning_feed_summary,
        get_recent_track_segment,
        jump_to_warning_event,
        keep_convoy_in_center_zone,
        navigate_warning_event,
        order_trucks_by_motion,
        pick_warning_event_at,
        record_anomaly_events,
        sample_track,
        sample_track_dynamic,
        seek_seconds,
        update_chart_data,
        warning_feed_get_max_scroll_px,
    )
    from modules.visualizer_export import export_all_data, export_data
    from modules.visualizer_interaction import handle_event
    from modules.visualizer_labels import draw_compact_labels
    from modules.visualizer_render import render_frame, VEHICLE_MARKER_RADIUS


logger = logging.getLogger(__name__)


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
        except Exception:
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
        self.warning_feed_sort_desc = True
        self.warning_feed_group_by = "time"
        self.warning_feed_type_filter = 0
        self.warning_feed_truck_filter = "all"
        self.selected_truck_id = None
        self._warning_nav_index = None
        self._active_warning_event_key = None
        self.dragging_warning_scrollbar = False
        self._warning_scrollbar_drag_offset_y = 0
        self._vehicle_tile_hitboxes = {}
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
        self.ui_elements_system.selected_truck_id = None
        self.ui_elements_system._active_warning_event_key = None
        self.ui_elements_system._warning_feed_control_hitboxes = {}
        self.ui_elements_system._warning_feed_scrollbar_track_rect = None
        self.ui_elements_system._warning_feed_scrollbar_thumb_rect = None
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
            logger.error("未能从数据中获取时间范围，请检查 CSV 是否包含有效的 timestamp 列。")
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
                    logger.info("数据运行结束，已回到初始状态并暂停。")
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
        return order_trucks_by_motion(self, trucks)

    def _keep_convoy_in_center_zone(self, ordered_trucks, focus_truck=None):
        return keep_convoy_in_center_zone(self, ordered_trucks, focus_truck=focus_truck)

    def _pick_warning_event_at(self, pos):
        return pick_warning_event_at(self, pos)

    def _pick_warning_feed_control_at(self, pos):
        for action, rect in getattr(self.ui_elements_system, "_warning_feed_control_hitboxes", {}).items():
            if rect.collidepoint(pos):
                return action
        return None

    def _pick_vehicle_tile_at(self, pos):
        for truck_id, rect in self._vehicle_tile_hitboxes.items():
            if rect.collidepoint(pos):
                return truck_id
        return None

    def _pick_warning_feed_scrollbar_part_at(self, pos):
        thumb = getattr(self.ui_elements_system, "_warning_feed_scrollbar_thumb_rect", None)
        if thumb is not None and thumb.collidepoint(pos):
            return "thumb"
        track = getattr(self.ui_elements_system, "_warning_feed_scrollbar_track_rect", None)
        if track is not None and track.collidepoint(pos):
            return "track"
        return None

    def _warning_feed_get_max_scroll_px(self):
        return warning_feed_get_max_scroll_px(self)

    def _set_warning_feed_scroll_from_pointer(self, pointer_y, keep_thumb_center=False):
        track = getattr(self.ui_elements_system, "_warning_feed_scrollbar_track_rect", None)
        thumb = getattr(self.ui_elements_system, "_warning_feed_scrollbar_thumb_rect", None)
        max_scroll = self._warning_feed_get_max_scroll_px()
        if track is None or thumb is None or max_scroll <= 0:
            return
        thumb_h = max(1, thumb.h)
        if keep_thumb_center:
            top = pointer_y - thumb_h / 2.0
        else:
            top = pointer_y - self._warning_scrollbar_drag_offset_y
        top = max(track.y, min(track.bottom - thumb_h, top))
        usable = max(1, track.h - thumb_h)
        ratio = (top - track.y) / usable
        self._warning_feed_scroll_px = max(0, min(max_scroll, int(round((1.0 - ratio) * max_scroll))))

    def _get_warning_feed_events(self):
        return get_warning_feed_events(self)

    def _get_warning_feed_summary(self):
        return get_warning_feed_summary(self)

    def _cycle_warning_feed_action(self, action):
        cycle_warning_feed_action(self, action)

    def _jump_to_warning_event(self, processor, event_or_index, pause=True):
        return jump_to_warning_event(self, processor, event_or_index, pause=pause)

    def _navigate_warning_event(self, processor, step):
        return navigate_warning_event(self, processor, step)

    def _seek_seconds(self, processor, delta_seconds):
        seek_seconds(self, processor, delta_seconds)

    def _draw_compact_labels(self, ordered_trucks):
        draw_compact_labels(self, ordered_trucks)

    def _sample_track(self, track, max_points=100):
        return sample_track(track, max_points=max_points)

    def _sample_track_dynamic(self, track):
        return sample_track_dynamic(self, track)

    def _get_recent_track_segment(self, track):
        return get_recent_track_segment(self, track)

    def _export_data(self, processor):
        export_data(self, processor)

    def _record_anomaly_events(self, ordered_trucks, neighbor_distance, prev_by_id):
        record_anomaly_events(self, ordered_trucks, neighbor_distance, prev_by_id)

    def _compute_kpis(self, visible_trucks, neighbor_distance):
        return compute_kpis(self, visible_trucks, neighbor_distance)

    def _export_all_data(self, processor):
        export_all_data(self, processor)

    def _update_chart_data(self, processor):
        update_chart_data(self, processor)
