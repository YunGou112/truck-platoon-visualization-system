import pygame
from .ui_overlays import draw_config_panel, draw_progress_bar, draw_progress_bar_minimal, draw_warning_feed
from .ui_panels import draw_help_panel, draw_kpi_bar, draw_left_sidebar, draw_status_panel
from .ui_tiles import draw_bottom_tiles, draw_vehicle_tiles

class UIElementsSystem:
    """界面元素系统：负责处理界面上的各种UI元素"""
    
    def __init__(self, config):
        """初始化界面元素系统
        
        Args:
            config: 配置对象，包含界面元素相关的配置参数
        """
        self.config = config
        
        # 初始化字体
        try:
            self.font = pygame.font.SysFont("SimHei", 24)
            self.small_font = pygame.font.SysFont("SimHei", 18)
            self.tiny_font = pygame.font.SysFont("SimHei", 11)
        except Exception:
            self.font = pygame.font.Font(None, 24)
            self.small_font = pygame.font.Font(None, 18)
            self.tiny_font = pygame.font.Font(None, 11)
    
    def draw_status_panel(self, screen, width, height, current_sim_time, play_speed, is_playing, view_zoom, current_platoon, truck_count, latest_warning_text=""):
        return draw_status_panel(self, screen, width, height, current_sim_time, play_speed, is_playing, view_zoom, current_platoon, truck_count, latest_warning_text)

    def draw_left_sidebar(self, screen, width, height, sidebar_bottom_y, sidebar_data, chart_data, chart_max_points):
        return draw_left_sidebar(self, screen, width, height, sidebar_bottom_y, sidebar_data, chart_data, chart_max_points)

    def _draw_metric_cards(self, screen, row_rect, chart_data):
        """绘制三项当前值卡片。"""
        gap = 8
        card_w = int((row_rect.w - gap * 2) / 3)
        card_h = row_rect.h
        keys = [
            ("speed", "平均速度", "km/h", (80, 230, 120)),
            ("headway", "平均时距", "s", (80, 180, 255)),
            ("speed_variance", "速度一致性", "", (255, 190, 80)),
        ]
        for i, (k, title, unit, color) in enumerate(keys):
            x = row_rect.x + i * (card_w + gap)
            r = pygame.Rect(x, row_rect.y, card_w, card_h)
            pygame.draw.rect(screen, (18, 20, 30), r, border_radius=8)
            pygame.draw.rect(screen, (55, 70, 105), r, 1, border_radius=8)
            # 顶部高光
            pygame.draw.rect(screen, color, (r.x, r.y, r.w, 4), border_radius=8)

            value = chart_data.get(k, [])[-1] if chart_data.get(k) else None
            value_text = "-" if value is None else f"{value:.2f}"

            t1 = self.tiny_font.render(title, True, (170, 180, 200))
            t2 = self.small_font.render(value_text, True, (235, 245, 255))
            screen.blit(t1, (r.x + 8, r.y + 8))
            screen.blit(t2, (r.x + 8, r.y + 24))
            if unit:
                u = self.tiny_font.render(unit, True, (150, 160, 175))
                screen.blit(u, (r.right - u.get_width() - 8, r.bottom - u.get_height() - 6))

    def _draw_trend_panel(self, screen, trend_rect, chart_data):
        """绘制三指标合并趋势图，避免图表区空荡。"""
        if trend_rect.h < 60 or trend_rect.w < 80:
            return

        pygame.draw.rect(screen, (16, 18, 26), trend_rect, border_radius=8)
        pygame.draw.rect(screen, (50, 62, 90), trend_rect, 1, border_radius=8)

        # 网格
        for i in range(1, 4):
            y = trend_rect.y + int(trend_rect.h * i / 4)
            pygame.draw.line(screen, (34, 42, 62), (trend_rect.x + 6, y), (trend_rect.right - 6, y), 1)
        for i in range(1, 5):
            x = trend_rect.x + int(trend_rect.w * i / 5)
            pygame.draw.line(screen, (30, 36, 52), (x, trend_rect.y + 6), (x, trend_rect.bottom - 6), 1)

        series_cfg = [
            ("speed", 120.0, (80, 230, 120), "速度"),
            ("headway", 10.0, (80, 180, 255), "时距"),
            ("speed_variance", 20.0, (255, 190, 80), "一致性"),
        ]

        # 留边
        x0 = trend_rect.x + 8
        y0 = trend_rect.y + 8
        w = trend_rect.w - 16
        h = trend_rect.h - 24

        for key, vmax, color, _label in series_cfg:
            data = chart_data.get(key, [])
            if len(data) < 2:
                continue
            pts = []
            n = len(data)
            # 取最近 80 点，避免过密
            if n > 80:
                data = data[-80:]
                n = len(data)
            for i, v in enumerate(data):
                vv = max(0.0, min(float(v), float(vmax)))
                nx = i / (n - 1) if n > 1 else 0.0
                ny = vv / float(vmax) if vmax > 0 else 0.0
                px = x0 + int(nx * w)
                py = y0 + int((1.0 - ny) * h)
                pts.append((px, py))
            if len(pts) >= 2:
                pygame.draw.lines(screen, color, False, pts, 2)
                pygame.draw.circle(screen, color, pts[-1], 3)

        # 图例（同一行）
        lx = trend_rect.x + 10
        ly = trend_rect.bottom - 12
        for _, _, color, label in series_cfg:
            pygame.draw.circle(screen, color, (lx, ly), 3)
            t = self.tiny_font.render(label, True, (170, 180, 200))
            screen.blit(t, (lx + 8, ly - 6))
            lx += t.get_width() + 26
    
    def draw_help_panel(self, screen, width, height):
        draw_help_panel(self, screen, width, height)
    
    def draw_progress_bar(self, screen, width, height, current_sim_time, min_time, max_time):
        draw_progress_bar(self, screen, width, height, current_sim_time, min_time, max_time)
    
    def draw_config_panel(self, screen, width, height, show_config, config):
        draw_config_panel(self, screen, width, height, show_config, config)
    
    def draw_chart(self, screen, width, height, chart_data, chart_max_points, anchor_rect=None):
        """绘制实时图表
        
        Args:
            screen: Pygame屏幕对象
            width: 屏幕宽度
            height: 屏幕高度
            chart_data: 图表数据
            chart_max_points: 图表最大数据点数量
        """
        chart_w = 320
        chart_h = 200
        if anchor_rect is None:
            # 默认放左上（避免与右上预警面板冲突）
            chart_rect = pygame.Rect(10, 320, chart_w, chart_h)
        else:
            # 放到左侧控制面板下方紧挨着
            chart_y = anchor_rect.bottom + 10
            chart_rect = pygame.Rect(anchor_rect.x, chart_y, chart_w, chart_h)
        
        # 绘制图表背景
        pygame.draw.rect(screen, (40, 40, 50), chart_rect, border_radius=5)
        pygame.draw.rect(screen, (80, 80, 100), chart_rect, 1, border_radius=5)
        
        # 绘制标题
        chart_title = self.font.render("编队性能指标", True, (255, 255, 255))
        screen.blit(chart_title, (chart_rect.x + 10, chart_rect.y + 5))
        
        # 绘制平均速度图表
        self._draw_line_chart(screen, chart_rect, chart_data, 'speed', (0, 255, 0), "平均速度 (km/h)", 0, 120)
        
        # 绘制平均车头时距图表
        self._draw_line_chart(screen, chart_rect, chart_data, 'headway', (0, 120, 255), "平均车头时距 (s)", 0, 10, offset_y=60)
        
        # 绘制编队一致性图表（速度差异）
        self._draw_line_chart(screen, chart_rect, chart_data, 'speed_variance', (255, 165, 0), "速度一致性", 0, 20, offset_y=120)

    def draw_kpi_bar(self, screen, width, height, kpis):
        draw_kpi_bar(self, screen, width, height, kpis)

    def draw_warning_feed(self, screen, width, height, events, scroll_offset_px=0):
        return draw_warning_feed(self, screen, width, height, events, scroll_offset_px)

    def draw_bottom_tiles(self, screen, width, height, tiles):
        draw_bottom_tiles(self, screen, width, height, tiles)

    def draw_vehicle_tiles(self, screen, width, height, vehicle_tiles, start_x=0, bottom_padding=0):
        return draw_vehicle_tiles(self, screen, width, height, vehicle_tiles, start_x=start_x, bottom_padding=bottom_padding)

    def draw_progress_bar_minimal(self, screen, width, height, current_time, min_time, max_time, bar_h=10, margin=0):
        return draw_progress_bar_minimal(self, screen, width, height, current_time, min_time, max_time, bar_h=bar_h, margin=margin)
    
    def _draw_line_chart(self, screen, chart_rect, chart_data, data_key, color, label, min_val, max_val, offset_y=0):
        """绘制折线图
        
        Args:
            screen: Pygame屏幕对象
            chart_rect: 图表区域
            chart_data: 图表数据
            data_key: 数据键
            color: 线条颜色
            label: 标签
            min_val: 最小值
            max_val: 最大值
            offset_y: Y轴偏移
        """
        data = chart_data.get(data_key, [])
        if not data:
            return
        
        # 图表区域
        chart_width = chart_rect.w - 60
        chart_height = 30
        chart_x = chart_rect.x + 50
        chart_y = chart_rect.y + 30 + offset_y
        
        # 提取单位
        unit = ""
        if "km/h" in label:
            unit = " km/h"
        elif "s" in label:
            unit = " s"
        
        # 绘制标签和当前值（右对齐）
        if data:
            current_value = data[-1]
            # 格式为"指标名称：数值 单位"
            display_text = f"{label.split('(')[0].strip()}: {current_value:.2f}{unit}"
            text_surf = self.small_font.render(display_text, True, (200, 200, 200))
            # 右对齐
            text_x = chart_rect.x + chart_rect.w - text_surf.get_width() - 10
            screen.blit(text_surf, (text_x, chart_y + 5))
        else:
            # 没有数据时只显示标签
            label_surf = self.small_font.render(label, True, (200, 200, 200))
            screen.blit(label_surf, (chart_rect.x + 10, chart_y + 5))
        
        # 绘制坐标轴
        pygame.draw.line(screen, (100, 100, 120), (chart_x, chart_y), (chart_x + chart_width, chart_y), 1)
        pygame.draw.line(screen, (100, 100, 120), (chart_x, chart_y), (chart_x, chart_y + chart_height), 1)
        
        # 动态调整Y轴范围
        if data_key == 'headway' and data:
            max_data = max(data)
            if max_data > 10:
                # 车头时距超过10秒，动态调整范围
                max_val = min(max_data * 1.2, 60)  # 最大60秒
        
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
            pygame.draw.lines(screen, color, False, points, 2)
            
            # 绘制最后一个数据点
            if points:
                last_x, last_y = points[-1]
                pygame.draw.circle(screen, color, (int(last_x), int(last_y)), 3)
