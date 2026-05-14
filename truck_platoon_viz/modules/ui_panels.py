import pygame


PANEL_BG = (16, 18, 26)
PANEL_BORDER = (52, 60, 82)
PANEL_HEADER_BG = (22, 28, 42)
PANEL_HEADER_TEXT = (230, 235, 242)
SECTION_TEXT = (188, 198, 214)
BODY_TEXT = (166, 174, 188)
MUTED_TEXT = (124, 132, 146)
DIVIDER = (40, 48, 66)
ACCENT = (92, 124, 184)
SELECTED = (232, 202, 112)
WARNING = (232, 114, 114)


def draw_status_panel(ui, screen, width, height, current_sim_time, play_speed, is_playing, view_zoom, current_platoon, truck_count, latest_warning_text=""):
    panel_w = 320
    panel_h = 300
    rect = pygame.Rect(10, 10, panel_w, panel_h)
    pygame.draw.rect(screen, PANEL_BG, rect, border_radius=6)
    pygame.draw.rect(screen, PANEL_BORDER, rect, 1, border_radius=6)

    x = rect.x + 12
    y = rect.y + 10

    title = ui.small_font.render("控制面板", True, PANEL_HEADER_TEXT)
    screen.blit(title, (x, y))
    y += 30

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
        surf = ui.tiny_font.render(line, True, BODY_TEXT)
        screen.blit(surf, (x, y))
        y += 18

    y += 6
    pygame.draw.line(screen, DIVIDER, (x, y), (rect.right - 12, y), 1)
    y += 10

    warning_text = latest_warning_text if latest_warning_text else "无预警"
    screen.blit(ui.tiny_font.render("最新预警", True, MUTED_TEXT), (x, y))
    warning_color = WARNING if latest_warning_text else BODY_TEXT
    surf = ui.small_font.render(warning_text, True, warning_color)
    screen.blit(surf, (x, y + 12))
    y += 40

    try:
        from config import PlatoonConfig
        thresholds = [
            f"阈值  最小车距 {PlatoonConfig.WARNING_MIN_DISTANCE_M:.0f}m",
            f"阈值  最大|a|  {PlatoonConfig.WARNING_MAX_ABS_ACCEL_MPS2:.1f} m/s2",
            f"阈值  最大速度 {PlatoonConfig.WARNING_MAX_SPEED_KMH:.0f} km/h",
            f"阈值  去抖帧数 {int(PlatoonConfig.WARNING_DEBOUNCE_FRAMES)}",
        ]
    except (ImportError, AttributeError, TypeError, ValueError):
        thresholds = []

    for line in thresholds:
        surf = ui.tiny_font.render(line, True, MUTED_TEXT)
        screen.blit(surf, (x, y))
        y += 15
    return rect


def draw_left_sidebar(ui, screen, width, height, sidebar_bottom_y, sidebar_data, chart_data, chart_max_points):
    sidebar_w = 320
    rect = pygame.Rect(0, 0, sidebar_w, max(220, int(sidebar_bottom_y)))

    pygame.draw.rect(screen, PANEL_BG, rect)
    pygame.draw.line(screen, PANEL_BORDER, (rect.right - 1, rect.top), (rect.right - 1, rect.bottom), 1)

    header_h = 46
    header = pygame.Rect(rect.x, rect.y, rect.w, header_h)
    pygame.draw.rect(screen, PANEL_HEADER_BG, header)
    pygame.draw.line(screen, PANEL_BORDER, (header.x, header.bottom - 1), (header.right, header.bottom - 1), 1)
    title = ui.small_font.render("控制与指标", True, PANEL_HEADER_TEXT)
    screen.blit(title, (rect.x + 12, rect.y + 13))

    x = rect.x + 14
    y = rect.y + header_h + 12
    overview = (sidebar_data or {}).get("overview") or {}
    safety = (sidebar_data or {}).get("safety") or {}
    selected = (sidebar_data or {}).get("selected")
    controls = (sidebar_data or {}).get("controls") or []

    def sec_to_mmss(sec):
        if sec is None:
            return "-"
        if isinstance(sec, (int, float)):
            s = int(max(0, sec))
            return f"{s//60:02d}:{s%60:02d}"
        return "-"

    def section(title_text, y_value):
        y_value += 5
        t = ui.tiny_font.render(title_text, True, SECTION_TEXT)
        screen.blit(t, (x, y_value))
        y_value += 18
        pygame.draw.line(screen, DIVIDER, (x, y_value), (rect.right - 14, y_value), 1)
        y_value += 8
        return y_value

    y = section("编队概览", y)
    for line in [
        f"编队: {overview.get('platoon', '-')}",
        f"车辆: {overview.get('visible_count', 0)}/{overview.get('total_count', 0)}",
        f"头车/尾车: {overview.get('head', '-')}/{overview.get('tail', '-')}",
        f"片段时长: {sec_to_mmss(overview.get('duration_s'))}",
    ]:
        surf = ui.tiny_font.render(line, True, BODY_TEXT)
        screen.blit(surf, (x, y))
        y += 15

    y = section("安全与异常", y)
    by_type = safety.get("by_type") or {}
    warning_now = safety.get("warning_now", 0)
    safety_lines = [
        (f"当前预警车辆: {warning_now}", WARNING if warning_now else BODY_TEXT),
        (f"累计预警事件: {safety.get('warnings_total', 0)}", BODY_TEXT),
        (f"车距/加速度/超速/多规则: {by_type.get(1,0)}/{by_type.get(2,0)}/{by_type.get(3,0)}/{by_type.get(4,0)}", MUTED_TEXT),
    ]
    for line, color in safety_lines:
        surf = ui.tiny_font.render(line, True, color)
        screen.blit(surf, (x, y))
        y += 15

    y = section("选中车辆", y)
    if not selected:
        surf = ui.tiny_font.render("提示：点击车辆或预警事件以查看详情", True, MUTED_TEXT)
        screen.blit(surf, (x, y))
        y += 15
    else:
        speed_kmh = selected.get("speed_kmh")
        gap_m = selected.get("gap_m")
        drive_dist_km = selected.get("drive_dist_km")
        selected_lines = [
            (f"车ID: {str(selected.get('truck_id', ''))[-4:]}", SELECTED),
            (f"实时车速: {'-' if speed_kmh is None else f'{speed_kmh:.0f}'} km/h", BODY_TEXT),
            (f"实时车距: {'-' if gap_m is None else f'{gap_m:.1f}'} m", WARNING if isinstance(gap_m, (int, float)) and gap_m < 20 else BODY_TEXT),
            (f"行驶时间/距离: {sec_to_mmss(selected.get('drive_time_s'))} / {'-' if drive_dist_km is None else f'{drive_dist_km:.2f}'} km", BODY_TEXT),
            (f"预警: {selected.get('warning_text') or '无'}", WARNING if selected.get("warning_text") else MUTED_TEXT),
        ]
        for line, color in selected_lines:
            surf = ui.tiny_font.render(line, True, color)
            screen.blit(surf, (x, y))
            y += 15

    y = section("操作提示", y)
    left_x = x
    right_x = rect.right - 14
    idx = 0
    while idx < len(controls):
        left_text = controls[idx]
        right_text = controls[idx + 1] if idx + 1 < len(controls) else ""
        left_surf = ui.tiny_font.render(left_text, True, MUTED_TEXT)
        screen.blit(left_surf, (left_x, y))
        if right_text:
            right_surf = ui.tiny_font.render(right_text, True, MUTED_TEXT)
            screen.blit(right_surf, (right_x - right_surf.get_width(), y))
        y += 15
        idx += 2

    chart_rect = pygame.Rect(rect.x + 12, y, rect.w - 24, rect.bottom - y - 12)
    pygame.draw.rect(screen, (18, 20, 28), chart_rect, border_radius=10)
    pygame.draw.rect(screen, DIVIDER, chart_rect, 1, border_radius=10)
    chart_title = ui.tiny_font.render("编队性能指标", True, SECTION_TEXT)
    screen.blit(chart_title, (chart_rect.x + 10, chart_rect.y + 8))

    metrics_row = pygame.Rect(chart_rect.x + 8, chart_rect.y + 30, chart_rect.w - 16, 58)
    ui._draw_metric_cards(screen, metrics_row, chart_data)
    trend_rect = pygame.Rect(chart_rect.x + 8, metrics_row.bottom + 8, chart_rect.w - 16, chart_rect.bottom - metrics_row.bottom - 16)
    ui._draw_trend_panel(screen, trend_rect, chart_data)
    return rect


def draw_help_panel(ui, screen, width, height):
    help_panel_rect = pygame.Rect(10, height - 60, width - 20, 40)
    pygame.draw.rect(screen, (18, 20, 28), help_panel_rect, border_radius=5)
    pygame.draw.rect(screen, DIVIDER, help_panel_rect, 1, border_radius=5)
    help_text1 = "空格: 暂停 | 上下/左右/+/-: 调速 | R: 重置 | 滚轮: 缩放 | 左键拖动: 平移"
    help_text2 = "N/P: 下一条/上一条预警 | C: 配置 | E: 导出当前 | F: 导出所有"
    help_surf1 = ui.tiny_font.render(help_text1, True, MUTED_TEXT)
    help_surf2 = ui.tiny_font.render(help_text2, True, MUTED_TEXT)
    screen.blit(help_surf1, ((width - help_surf1.get_width()) // 2, height - 50))
    screen.blit(help_surf2, ((width - help_surf2.get_width()) // 2, height - 30))


def draw_kpi_bar(ui, screen, width, height, kpis):
    if not kpis:
        return
    panel_rect = pygame.Rect(10, height - 170, width - 20, 44)
    pygame.draw.rect(screen, (18, 20, 28), panel_rect, border_radius=6)
    pygame.draw.rect(screen, DIVIDER, panel_rect, 1, border_radius=6)
    items = [
        ("最小相邻车距", kpis.get("min_neighbor_distance_m"), "m", BODY_TEXT),
        ("超速车辆数", kpis.get("overspeed_count"), "", WARNING if (kpis.get("overspeed_count") or 0) > 0 else BODY_TEXT),
        ("加速度异常数", kpis.get("accel_anomaly_count"), "", WARNING if (kpis.get("accel_anomaly_count") or 0) > 0 else BODY_TEXT),
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
        surf = ui.small_font.render(text, True, color)
        screen.blit(surf, (x, y))
        x += max(220, surf.get_width() + 30)
