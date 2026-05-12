import pygame

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
        except:
            self.font = pygame.font.Font(None, 24)
            self.small_font = pygame.font.Font(None, 18)
            self.tiny_font = pygame.font.Font(None, 11)
    
    def draw_status_panel(self, screen, width, height, current_sim_time, play_speed, is_playing, view_zoom, current_platoon, truck_count, latest_warning_text=""):
        """绘制左侧控制面板（整合状态+控制+阈值）
        
        Args:
            screen: Pygame屏幕对象
            width: 屏幕宽度
            height: 屏幕高度
            current_sim_time: 当前模拟时间
            play_speed: 播放速度
            is_playing: 是否正在播放
            view_zoom: 视图缩放比例
            current_platoon: 当前编队名称
            truck_count: 卡车数量
        """
        panel_w = 320
        panel_h = 300
        rect = pygame.Rect(10, 10, panel_w, panel_h)
        pygame.draw.rect(screen, (40, 40, 50, 220), rect, border_radius=6)
        pygame.draw.rect(screen, (80, 80, 100), rect, 2, border_radius=6)

        x = rect.x + 12
        y = rect.y + 10

        title = self.font.render("控制面板", True, (255, 255, 255))
        screen.blit(title, (x, y))
        y += 34

        # 基本状态（竖向排列）
        time_str = current_sim_time.strftime("%Y-%m-%d %H:%M:%S") if current_sim_time else "-"
        status = "播放" if is_playing else "暂停"
        lines = [
            f"时间: {time_str}",
            f"状态: {status}",
            f"速度: {play_speed:.1f}x",
            f"缩放: {view_zoom:.2f}x",
            f"编队: {current_platoon if current_platoon else '-'}",
            f"车辆: {truck_count}",
        ]
        for line in lines:
            surf = self.small_font.render(line, True, (220, 220, 220))
            screen.blit(surf, (x, y))
            y += 22

        y += 6
        pygame.draw.line(screen, (90, 90, 110), (x, y), (rect.right - 12, y), 1)
        y += 10

        # 预警摘要
        warning_text = latest_warning_text if latest_warning_text else "无预警"
        warning_color = (255, 120, 120) if latest_warning_text else (180, 180, 180)
        surf = self.small_font.render(f"最新预警  {warning_text}", True, warning_color)
        screen.blit(surf, (x, y))
        y += 26

        # 阈值（直接展示 config.py 中的关键值，便于答辩说明）
        try:
            from config import PlatoonConfig
            th = [
                f"阈值  最小车距 {PlatoonConfig.WARNING_MIN_DISTANCE_M:.0f}m",
                f"阈值  最大|a|  {PlatoonConfig.WARNING_MAX_ABS_ACCEL_MPS2:.1f} m/s2",
                f"阈值  最大速度 {PlatoonConfig.WARNING_MAX_SPEED_KMH:.0f} km/h",
                f"阈值  去抖帧数 {int(PlatoonConfig.WARNING_DEBOUNCE_FRAMES)}",
            ]
        except Exception:
            th = []
        for line in th:
            surf = self.tiny_font.render(line, True, (170, 170, 170))
            screen.blit(surf, (x, y))
            y += 16
        return rect

    def draw_left_sidebar(self, screen, width, height, sidebar_bottom_y, sidebar_data, chart_data, chart_max_points):
        """绘制贯穿左侧的侧边栏：驾驶舱信息墙 + 性能指标图表。"""
        # 左侧贯通：尽量无缝贴边（更像大屏侧栏）
        sidebar_w = 320
        x0 = 0
        y0 = 0
        y1 = max(220, int(sidebar_bottom_y))
        rect = pygame.Rect(x0, y0, sidebar_w, y1 - y0)

        # 背景与边框（更统一）
        pygame.draw.rect(screen, (18, 18, 26), rect)
        pygame.draw.line(screen, (70, 85, 115), (rect.right - 1, rect.top), (rect.right - 1, rect.bottom), 2)

        # 顶部标题条
        header_h = 46
        header = pygame.Rect(rect.x, rect.y, rect.w, header_h)
        pygame.draw.rect(screen, (28, 38, 62), header)
        pygame.draw.line(screen, (0, 180, 255), (header.x, header.bottom - 2), (header.right, header.bottom - 2), 2)
        title = self.font.render("控制与指标", True, (245, 245, 245))
        screen.blit(title, (rect.x + 12, rect.y + 11))

        # 信息区
        x = rect.x + 14
        y = rect.y + header_h + 12
        overview = (sidebar_data or {}).get("overview") or {}
        safety = (sidebar_data or {}).get("safety") or {}
        selected = (sidebar_data or {}).get("selected")
        controls = (sidebar_data or {}).get("controls") or []

        def _sec_to_mmss(sec):
            if sec is None:
                return "-"
            try:
                s = int(max(0, sec))
                return f"{s//60:02d}:{s%60:02d}"
            except Exception:
                return "-"

        def _section(title_text):
            nonlocal y
            y += 6
            t = self.small_font.render(title_text, True, (235, 235, 235))
            screen.blit(t, (x, y))
            y += 20
            pygame.draw.line(screen, (55, 65, 90), (x, y), (rect.right - 14, y), 1)
            y += 10

        # 编队概览
        _section("编队概览")
        dur = _sec_to_mmss(overview.get("duration_s"))
        items = [
            f"编队: {overview.get('platoon', '-')}",
            f"车辆: {overview.get('visible_count', 0)}/{overview.get('total_count', 0)}",
            f"头车/尾车: {overview.get('head', '-')}/{overview.get('tail', '-')}",
            f"片段时长: {dur}",
        ]
        for line in items:
            surf = self.tiny_font.render(line, True, (200, 200, 210))
            screen.blit(surf, (x, y))
            y += 16

        # 安全与异常
        _section("安全与异常")
        by_type = safety.get("by_type") or {}
        items = [
            f"当前预警车辆: {safety.get('warning_now', 0)}",
            f"累计预警事件: {safety.get('warnings_total', 0)}",
            f"车距/加速度/超速/多规则: {by_type.get(1,0)}/{by_type.get(2,0)}/{by_type.get(3,0)}/{by_type.get(4,0)}",
        ]
        for line in items:
            surf = self.tiny_font.render(line, True, (200, 200, 210))
            screen.blit(surf, (x, y))
            y += 16

        # 选中车辆
        _section("选中车辆")
        if not selected:
            surf = self.tiny_font.render("提示：点击车辆或预警事件以查看详情", True, (170, 170, 170))
            screen.blit(surf, (x, y))
            y += 16
        else:
            tid = str(selected.get("truck_id", ""))[-4:]
            v = selected.get("speed_kmh")
            gap = selected.get("gap_m")
            t_str = _sec_to_mmss(selected.get("drive_time_s"))
            dist = selected.get("drive_dist_km")
            warn = selected.get("warning_text") or "无"
            lines = [
                f"车ID: {tid}",
                f"实时车速: {('-' if v is None else f'{v:.0f}')} km/h",
                f"实时车距: {('-' if gap is None else f'{gap:.1f}')} m",
                f"行驶时间/距离: {t_str} / {('-' if dist is None else f'{dist:.2f}')} km",
                f"预警: {warn}",
            ]
            for line in lines:
                surf = self.tiny_font.render(line, True, (200, 200, 210))
                screen.blit(surf, (x, y))
                y += 16

        # 操作提示
        _section("操作提示")
        left_x = x
        right_x = rect.right - 14
        row_h = 16
        i = 0
        while i < len(controls):
            left_text = controls[i]
            right_text = controls[i + 1] if i + 1 < len(controls) else ""

            left_surf = self.tiny_font.render(left_text, True, (170, 170, 170))
            screen.blit(left_surf, (left_x, y))

            if right_text:
                right_surf = self.tiny_font.render(right_text, True, (170, 170, 170))
                screen.blit(right_surf, (right_x - right_surf.get_width(), y))

            y += row_h
            i += 2

        # 图表区（紧贴控制区下方，占满剩余空间）
        chart_rect = pygame.Rect(rect.x + 12, y, rect.w - 24, rect.bottom - y - 12)
        pygame.draw.rect(screen, (24, 24, 34), chart_rect, border_radius=10)
        pygame.draw.rect(screen, (60, 72, 100), chart_rect, 1, border_radius=10)

        chart_title = self.small_font.render("编队性能指标", True, (235, 235, 235))
        screen.blit(chart_title, (chart_rect.x + 10, chart_rect.y + 8))

        # 1) 顶部当前值卡片（填充空白，提升信息密度）
        metrics_row = pygame.Rect(chart_rect.x + 8, chart_rect.y + 30, chart_rect.w - 16, 58)
        self._draw_metric_cards(screen, metrics_row, chart_data)

        # 2) 下方趋势图（三线合一 + 网格 + 图例）
        trend_rect = pygame.Rect(chart_rect.x + 8, metrics_row.bottom + 8, chart_rect.w - 16, chart_rect.bottom - metrics_row.bottom - 16)
        self._draw_trend_panel(screen, trend_rect, chart_data)

        return rect

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
        """绘制底部快捷键说明面板
        
        Args:
            screen: Pygame屏幕对象
            width: 屏幕宽度
            height: 屏幕高度
        """
        # 绘制操作提示面板
        help_panel_rect = pygame.Rect(10, height - 60, width - 20, 40)
        pygame.draw.rect(screen, (40, 40, 50), help_panel_rect, border_radius=5)
        pygame.draw.rect(screen, (80, 80, 100), help_panel_rect, 1, border_radius=5)
        
        # 操作提示 - 分两行显示，用竖线分隔，调整字体大小，文字居中对齐
        help_text1 = "空格: 暂停 | 上下/左右/+/-: 调速 | R: 重置 | 滚轮: 缩放 | 左键拖动: 平移"
        help_text2 = "A/D: 切换编队 | C: 配置 | E: 导出当前(含预警事件) | F: 导出所有"
        # 绘制文字
        help_surf1 = self.tiny_font.render(help_text1, True, (150, 150, 150))
        help_surf2 = self.tiny_font.render(help_text2, True, (150, 150, 150))
        # 计算居中位置
        text_x1 = (width - help_surf1.get_width()) // 2
        text_x2 = (width - help_surf2.get_width()) // 2
        screen.blit(help_surf1, (text_x1, height - 50))
        screen.blit(help_surf2, (text_x2, height - 30))
    
    def draw_progress_bar(self, screen, width, height, current_sim_time, min_time, max_time):
        """绘制进度条
        
        Args:
            screen: Pygame屏幕对象
            width: 屏幕宽度
            height: 屏幕高度
            current_sim_time: 当前模拟时间
            min_time: 最小时间
            max_time: 最大时间
        """
        # 进度条
        progress_bar_rect = pygame.Rect(50, height - 120, width - 100, 20)
        pygame.draw.rect(screen, (50, 50, 60), progress_bar_rect, border_radius=10)
        total_seconds = (max_time - min_time).total_seconds()
        if total_seconds > 0:
            current_seconds = (current_sim_time - min_time).total_seconds()
            ratio = current_seconds / total_seconds
            fill_width = int(progress_bar_rect.w * ratio)
            fill_rect = pygame.Rect(progress_bar_rect.x, progress_bar_rect.y, fill_width,
                                    progress_bar_rect.h)
            # 进度条渐变色
            blue_component = 120 + int(135 * ratio)
            blue_component = max(0, min(255, blue_component))  # 确保颜色值在有效范围内
            fill_color = (0, blue_component, 215)
            pygame.draw.rect(screen, fill_color, fill_rect, border_radius=10)
        pygame.draw.rect(screen, (100, 100, 120), progress_bar_rect, 2, border_radius=10)
    
    def draw_config_panel(self, screen, width, height, show_config, config):
        """绘制配置界面
        
        Args:
            screen: Pygame屏幕对象
            width: 屏幕宽度
            height: 屏幕高度
            show_config: 是否显示配置界面
            config: 配置对象
        """
        if not show_config:
            return
        
        # 绘制配置面板 - 带圆角和阴影效果
        reserved_right = 380  # 预留给右侧预警事件面板
        config_w = 250
        config_h = 300
        config_x = max(10, width - reserved_right - config_w - 10)
        config_rect = pygame.Rect(config_x, 50, config_w, config_h)
        pygame.draw.rect(screen, (30, 30, 30), (config_rect.x + 5, config_rect.y + 5, config_rect.w, config_rect.h), border_radius=8)
        pygame.draw.rect(screen, (50, 50, 60), config_rect, border_radius=8)
        pygame.draw.rect(screen, (100, 100, 120), config_rect, 2, border_radius=8)
        
        # 绘制标题 - 带背景
        title_rect = pygame.Rect(config_rect.x, config_rect.y, config_rect.w, 40)
        pygame.draw.rect(screen, (60, 60, 80), title_rect, border_radius=8)
        title = self.font.render("配置", True, (255, 255, 255))
        title_x = config_rect.x + (config_rect.w - title.get_width()) // 2
        screen.blit(title, (title_x, config_rect.y + 10))
        
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
            screen.blit(text, (config_rect.x + 20, config_rect.y + y_offset))
            
            # 绘制开关或滑块
            if isinstance(config.get(key, False), bool):
                # 绘制开关 - 更美观的设计
                switch_rect = pygame.Rect(config_rect.x + 160, config_rect.y + y_offset - 2, 60, 24)
                pygame.draw.rect(screen, (80, 80, 90), switch_rect, border_radius=12)
                if config.get(key, False):
                    pygame.draw.rect(screen, (0, 150, 255), switch_rect, border_radius=12)
                    # 开关按钮
                    pygame.draw.circle(screen, (255, 255, 255), (switch_rect.x + 48, switch_rect.y + 12), 8)
                else:
                    pygame.draw.circle(screen, (200, 200, 200), (switch_rect.x + 12, switch_rect.y + 12), 8)
            else:
                # 绘制值 - 带背景
                value_rect = pygame.Rect(config_rect.x + 160, config_rect.y + y_offset - 2, 60, 24)
                pygame.draw.rect(screen, (80, 80, 90), value_rect, border_radius=4)
                value_text = self.small_font.render(str(config.get(key, 0)), True, (255, 255, 255))
                value_x = value_rect.x + (value_rect.w - value_text.get_width()) // 2
                screen.blit(value_text, (value_x, value_rect.y + 3))
            
            y_offset += 35
        
        # 绘制提示 - 带背景
        hint_rect = pygame.Rect(config_rect.x, config_rect.y + y_offset, config_rect.w, 30)
        pygame.draw.rect(screen, (60, 60, 80), hint_rect, border_radius=4)
        hint = self.small_font.render("按C键关闭配置界面", True, (180, 180, 180))
        hint_x = config_rect.x + (config_rect.w - hint.get_width()) // 2
        screen.blit(hint, (hint_x, config_rect.y + y_offset + 5))
    
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
        """绘制底部 KPI 条（位于进度条上方）"""
        if not kpis:
            return

        panel_h = 44
        panel_y = height - 170
        panel_rect = pygame.Rect(10, panel_y, width - 20, panel_h)
        pygame.draw.rect(screen, (32, 32, 40), panel_rect, border_radius=6)
        pygame.draw.rect(screen, (80, 80, 100), panel_rect, 1, border_radius=6)

        items = [
            ("最小相邻车距", kpis.get("min_neighbor_distance_m"), "m", (200, 200, 200)),
            ("超速车辆数", kpis.get("overspeed_count"), "", (255, 200, 120) if (kpis.get("overspeed_count") or 0) > 0 else (200, 200, 200)),
            ("加速度异常数", kpis.get("accel_anomaly_count"), "", (255, 200, 120) if (kpis.get("accel_anomaly_count") or 0) > 0 else (200, 200, 200)),
        ]

        x = panel_rect.x + 14
        y = panel_rect.y + 12
        for title, value, unit, color in items:
            if value is None:
                text = f"{title}: -"
            elif isinstance(value, float):
                text = f"{title}: {value:.1f}{unit}"
            else:
                text = f"{title}: {value}{unit}"
            surf = self.small_font.render(text, True, color)
            screen.blit(surf, (x, y))
            x += max(220, surf.get_width() + 30)

    def draw_warning_feed(self, screen, width, height, events, scroll_offset_px=0):
        """绘制右侧预警事件流面板（仅展示预警）。"""
        # 右上角小面板（不占满右侧）
        panel_w = 260
        panel_h = min(320, max(220, height - 120))
        panel_x = width - panel_w - 10
        panel_y = 10
        rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)

        pygame.draw.rect(screen, (28, 28, 36), rect, border_radius=6)
        pygame.draw.rect(screen, (90, 90, 110), rect, 1, border_radius=6)

        title = self.font.render("预警", True, (255, 255, 255))
        screen.blit(title, (rect.x + 12, rect.y + 10))

        content_rect = pygame.Rect(rect.x + 10, rect.y + 46, rect.w - 20, rect.h - 58)
        pygame.draw.rect(screen, (24, 24, 32), content_rect, border_radius=6)

        if not events:
            empty = self.small_font.render("暂无预警事件", True, (170, 170, 170))
            screen.blit(empty, (content_rect.x + 12, content_rect.y + 12))
            return rect

        line_h = 34
        max_lines = max(1, content_rect.h // line_h)

        # events 默认按时间追加，这里从最新开始展示
        total = len(events)
        max_scroll = max(0, (total - max_lines) * line_h)
        scroll_offset_px = max(0, min(int(scroll_offset_px), int(max_scroll)))

        first_idx_from_bottom = scroll_offset_px // line_h
        start = max(0, total - max_lines - first_idx_from_bottom)
        end = total - first_idx_from_bottom

        y = content_rect.y + 8
        for ev in events[start:end]:
            ts = ev.get("timestamp_str", "")
            truck = str(ev.get("truck_id", ""))[-4:]
            msg = ev.get("message") or ev.get("warning_text") or ""
            val = ev.get("value_str") or ""
            sev = ev.get("severity", "info")

            color = (255, 120, 120) if sev in ("high", "critical") else (255, 200, 120) if sev == "medium" else (200, 200, 200)

            line1 = self.tiny_font.render(f"{ts}  #{truck}", True, (170, 170, 170))
            line2 = self.small_font.render(f"{msg} {val}".strip(), True, color)
            screen.blit(line1, (content_rect.x + 10, y))
            screen.blit(line2, (content_rect.x + 10, y + 14))
            y += line_h

        # 滚动条（可选的简易显示）
        if max_scroll > 0:
            bar_w = 6
            track = pygame.Rect(content_rect.right - bar_w - 4, content_rect.y + 6, bar_w, content_rect.h - 12)
            pygame.draw.rect(screen, (60, 60, 75), track, border_radius=3)
            ratio = content_rect.h / float(content_rect.h + max_scroll)
            thumb_h = max(18, int(track.h * ratio))
            thumb_y = track.y + int((scroll_offset_px / max_scroll) * (track.h - thumb_h))
            thumb = pygame.Rect(track.x, thumb_y, track.w, thumb_h)
            pygame.draw.rect(screen, (120, 120, 150), thumb, border_radius=3)

        return rect

    def draw_bottom_tiles(self, screen, width, height, tiles):
        """绘制底部 n 个小窗口卡片（从左到右并排）。"""
        if not tiles:
            return

        # 布局参数
        margin_x = 10
        margin_bottom = 10
        gap = 10
        tile_h = 78
        max_tiles = max(1, int((width - margin_x * 2 + gap) // (160 + gap)))
        tiles = tiles[:max_tiles]

        n = len(tiles)
        usable_w = width - margin_x * 2 - gap * (n - 1)
        tile_w = max(140, int(usable_w / n))

        y = height - margin_bottom - tile_h
        x = margin_x

        for t in tiles:
            title = t.get("title", "")
            value = t.get("value", None)
            unit = t.get("unit", "")
            color = t.get("color", (0, 150, 255))

            rect = pygame.Rect(x, y, tile_w, tile_h)
            pygame.draw.rect(screen, (28, 28, 36), rect, border_radius=8)
            pygame.draw.rect(screen, (90, 90, 110), rect, 1, border_radius=8)

            # 左上标题
            title_surf = self.tiny_font.render(str(title), True, (190, 190, 190))
            screen.blit(title_surf, (rect.x + 10, rect.y + 8))

            # 大号数值（居左）
            if value is None:
                value_str = "-"
            elif isinstance(value, float):
                value_str = f"{value:.1f}"
            else:
                value_str = str(value)

            value_surf = self.font.render(value_str, True, color)
            screen.blit(value_surf, (rect.x + 10, rect.y + 26))

            # 右下单位
            if unit:
                unit_surf = self.small_font.render(unit, True, (170, 170, 170))
                screen.blit(unit_surf, (rect.right - unit_surf.get_width() - 10, rect.bottom - unit_surf.get_height() - 8))

            x += tile_w + gap

    def draw_vehicle_tiles(self, screen, width, height, vehicle_tiles, start_x=0, bottom_padding=0):
        """绘制底部车辆卡片：有几辆车画几张（自动换行贴底）。

        Args:
            start_x: 底部卡片区域的起始 X（用于避开左侧侧边栏）
        """
        if not vehicle_tiles:
            return None

        # 尽量贴边铺满整个底部（但为进度条预留 bottom_padding）
        margin_x = int(start_x)
        margin_bottom = int(bottom_padding)
        gap = 8
        tile_h = 100
        min_tile_w = 220
        max_tile_w = 320

        # 让卡片尽量铺满整个底部
        avail_w = max(1, int(width - margin_x))
        max_cols = max(1, int((avail_w + gap) // (min_tile_w + gap)))
        n = len(vehicle_tiles)
        cols = min(n, max_cols)
        rows = (n + cols - 1) // cols

        usable_w = avail_w - gap * (cols - 1)
        tile_w = int(usable_w / cols) if cols > 0 else min_tile_w
        tile_w = max(min_tile_w, min(max_tile_w, tile_w))

        # 从底部往上叠行
        start_y = height - margin_bottom - rows * tile_h - (rows - 1) * gap
        start_y = max(0, start_y)

        for idx, t in enumerate(vehicle_tiles):
            r = idx // cols
            c = idx % cols
            x = margin_x + c * (tile_w + gap)
            y = start_y + r * (tile_h + gap)

            rect = pygame.Rect(x, y, tile_w, tile_h)
            is_warning = bool(t.get("warning", False))
            bg = (22, 28, 44) if not is_warning else (54, 22, 28)
            pygame.draw.rect(screen, bg, rect, border_radius=10)
            pygame.draw.rect(screen, (70, 90, 130), rect, 1, border_radius=10)

            # 顶部高光条
            strip = pygame.Rect(rect.x, rect.y, rect.w, 6)
            strip_color = (0, 180, 255) if not is_warning else (255, 90, 90)
            pygame.draw.rect(screen, strip_color, strip, border_radius=10)

            truck_id = str(t.get("truck_id", ""))
            header_color = (255, 120, 120) if is_warning else (200, 200, 200)

            # header
            header = self.small_font.render(f"车 {truck_id[-4:]}", True, header_color)
            screen.blit(header, (rect.x + 10, rect.y + 10))

            # 两个“指标框”（更贴近示例图）
            v = t.get("speed_kmh")
            d = t.get("gap_m")
            tt = t.get("drive_time_s")
            md = t.get("drive_dist")

            def fmt_num(val, fmt):
                if val is None:
                    return "-"
                try:
                    return fmt.format(val)
                except Exception:
                    return "-"

            # 时间格式化为 mm:ss
            if tt is None:
                t_str = "-"
            else:
                try:
                    tt_int = int(max(0, tt))
                    t_str = f"{tt_int//60:02d}:{tt_int%60:02d}"
                except Exception:
                    t_str = "-"

            box_h = 34
            box_w = int((rect.w - 30) / 2)
            box_y = rect.y + 34
            box1 = pygame.Rect(rect.x + 10, box_y, box_w, box_h)
            box2 = pygame.Rect(box1.right + 10, box_y, box_w, box_h)
            pygame.draw.rect(screen, (18, 20, 30), box1, border_radius=8)
            pygame.draw.rect(screen, (18, 20, 30), box2, border_radius=8)
            pygame.draw.rect(screen, (50, 70, 110), box1, 1, border_radius=8)
            pygame.draw.rect(screen, (50, 70, 110), box2, 1, border_radius=8)

            # box labels + values
            lab1 = self.tiny_font.render("实时车速", True, (160, 180, 210))
            lab2 = self.tiny_font.render("实时车距", True, (160, 180, 210))
            screen.blit(lab1, (box1.x + 8, box1.y + 5))
            screen.blit(lab2, (box2.x + 8, box2.y + 5))

            val1 = self.small_font.render(f"{fmt_num(v, '{:.0f}')}", True, (200, 240, 255))
            val2_color = (255, 120, 120) if (d is not None and d < 20) else (200, 240, 255)
            val2 = self.small_font.render(f"{fmt_num(d, '{:.1f}')}", True, val2_color)
            screen.blit(val1, (box1.x + 8, box1.y + 16))
            screen.blit(val2, (box2.x + 8, box2.y + 16))

            unit1 = self.tiny_font.render("km/h", True, (150, 160, 175))
            unit2 = self.tiny_font.render("m", True, (150, 160, 175))
            screen.blit(unit1, (box1.right - unit1.get_width() - 6, box1.y + 18))
            screen.blit(unit2, (box2.right - unit2.get_width() - 6, box2.y + 18))

            # 下方列表（更像示例图的条目行）
            y0 = box1.bottom + 10
            line3 = self.tiny_font.render(f"行驶时间  {t_str}", True, (205, 205, 210))
            line4 = self.tiny_font.render(f"行驶距离  {fmt_num(md, '{:.2f}')} km", True, (205, 205, 210))
            screen.blit(line3, (rect.x + 10, y0))
            # 同一行右对齐
            screen.blit(line4, (rect.right - line4.get_width() - 10, y0))

        return start_y

    def draw_progress_bar_minimal(self, screen, width, height, current_time, min_time, max_time, bar_h=10, margin=0):
        """绘制底部纯进度条（无文字）。"""
        if current_time is None or min_time is None or max_time is None:
            return None
        try:
            total = (max_time - min_time).total_seconds()
            cur = (current_time - min_time).total_seconds()
        except Exception:
            return None
        if total <= 0:
            return None

        w = width
        x = 0
        y = height - bar_h - margin
        rect = pygame.Rect(x, y, w, bar_h)
        # 背景
        pygame.draw.rect(screen, (20, 22, 30), rect)
        # 进度
        ratio = max(0.0, min(1.0, cur / total))
        fill = pygame.Rect(x, y, int(w * ratio), bar_h)
        pygame.draw.rect(screen, (0, 180, 255), fill)
        # 边线
        pygame.draw.line(screen, (70, 85, 115), (rect.x, rect.y), (rect.right, rect.y), 1)
        return rect
    
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