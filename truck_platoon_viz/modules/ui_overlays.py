import pygame


PANEL_BG = (16, 18, 26)
INNER_BG = (14, 16, 24)
BORDER = (52, 60, 82)
TEXT = (184, 192, 206)
MUTED = (126, 136, 152)
SELECTED = (232, 202, 112)
SELECTED_BG = (42, 44, 52)
WARNING = (232, 114, 114)
MEDIUM = (224, 182, 112)


def _fit_text_lines(font, text, max_width, max_lines=2):
    text = (text or "").strip()
    if not text:
        return [""] if max_lines > 0 else []

    lines = []
    remaining = text
    while remaining and len(lines) < max_lines:
        if font.size(remaining)[0] <= max_width:
            lines.append(remaining)
            remaining = ""
            break

        cut = len(remaining)
        while cut > 1 and font.size(remaining[:cut])[0] > max_width:
            cut -= 1

        split = remaining.rfind(" ", 0, cut)
        if split <= 0:
            split = cut

        line = remaining[:split].rstrip()
        if not line:
            line = remaining[:cut].rstrip()
            split = cut
        lines.append(line)
        remaining = remaining[split:].lstrip()

    if remaining and lines:
        suffix = "..."
        last = lines[-1]
        while last and font.size(last + suffix)[0] > max_width:
            last = last[:-1].rstrip()
        lines[-1] = (last + suffix) if last else suffix
    return lines


def draw_progress_bar(ui, screen, width, height, current_sim_time, min_time, max_time):
    progress_bar_rect = pygame.Rect(50, height - 120, width - 100, 20)
    pygame.draw.rect(screen, (50, 50, 60), progress_bar_rect, border_radius=10)
    total_seconds = (max_time - min_time).total_seconds()
    if total_seconds > 0:
        current_seconds = (current_sim_time - min_time).total_seconds()
        ratio = current_seconds / total_seconds
        fill_width = int(progress_bar_rect.w * ratio)
        fill_rect = pygame.Rect(progress_bar_rect.x, progress_bar_rect.y, fill_width, progress_bar_rect.h)
        blue_component = max(0, min(255, 120 + int(135 * ratio)))
        pygame.draw.rect(screen, (0, blue_component, 215), fill_rect, border_radius=10)
    pygame.draw.rect(screen, (100, 100, 120), progress_bar_rect, 2, border_radius=10)


def draw_progress_bar_minimal(ui, screen, width, height, current_time, min_time, max_time, bar_h=10, margin=0):
    if current_time is None or min_time is None or max_time is None:
        return None
    if not hasattr(min_time, "__sub__") or not hasattr(current_time, "__sub__"):
        return None
    total = (max_time - min_time).total_seconds()
    cur = (current_time - min_time).total_seconds()
    if total <= 0:
        return None
    rect = pygame.Rect(0, height - bar_h - margin, width, bar_h)
    pygame.draw.rect(screen, INNER_BG, rect)
    pygame.draw.rect(screen, (86, 120, 178), pygame.Rect(0, rect.y, int(width * max(0.0, min(1.0, cur / total))), bar_h))
    pygame.draw.line(screen, BORDER, (rect.x, rect.y), (rect.right, rect.y), 1)
    return rect


def draw_config_panel(ui, screen, width, height, show_config, config):
    if not show_config:
        return
    reserved_right = 380
    config_rect = pygame.Rect(max(10, width - reserved_right - 250 - 10), 50, 250, 300)
    pygame.draw.rect(screen, (12, 14, 22), (config_rect.x + 5, config_rect.y + 5, config_rect.w, config_rect.h), border_radius=8)
    pygame.draw.rect(screen, PANEL_BG, config_rect, border_radius=8)
    pygame.draw.rect(screen, BORDER, config_rect, 1, border_radius=8)

    title_rect = pygame.Rect(config_rect.x, config_rect.y, config_rect.w, 40)
    pygame.draw.rect(screen, (22, 28, 42), title_rect, border_radius=8)
    title = ui.small_font.render("配置", True, TEXT)
    screen.blit(title, (config_rect.x + (config_rect.w - title.get_width()) // 2, config_rect.y + 10))

    y_offset = 60
    for key, label in [
        ("show_speed_vector", "速度向量"),
        ("show_acceleration", "加速度指示器"),
        ("show_headway", "车头时距"),
        ("show_platoon_lines", "编队连接线"),
        ("max_track_points", "轨迹点数量"),
        ("vehicle_size", "车辆大小"),
        ("line_width", "线条宽度"),
    ]:
        text = ui.small_font.render(label, True, TEXT)
        screen.blit(text, (config_rect.x + 20, config_rect.y + y_offset))
        if isinstance(config.get(key, False), bool):
            switch_rect = pygame.Rect(config_rect.x + 160, config_rect.y + y_offset - 2, 60, 24)
            pygame.draw.rect(screen, (38, 42, 54), switch_rect, border_radius=12)
            if config.get(key, False):
                pygame.draw.rect(screen, (86, 120, 178), switch_rect, border_radius=12)
                pygame.draw.circle(screen, (255, 255, 255), (switch_rect.x + 48, switch_rect.y + 12), 8)
            else:
                pygame.draw.circle(screen, (200, 200, 200), (switch_rect.x + 12, switch_rect.y + 12), 8)
        else:
            value_rect = pygame.Rect(config_rect.x + 160, config_rect.y + y_offset - 2, 60, 24)
            pygame.draw.rect(screen, (38, 42, 54), value_rect, border_radius=4)
            value_text = ui.small_font.render(str(config.get(key, 0)), True, TEXT)
            screen.blit(value_text, (value_rect.x + (value_rect.w - value_text.get_width()) // 2, value_rect.y + 3))
        y_offset += 35

    hint_rect = pygame.Rect(config_rect.x, config_rect.y + y_offset, config_rect.w, 30)
    pygame.draw.rect(screen, (22, 28, 42), hint_rect, border_radius=4)
    hint = ui.small_font.render("按C键关闭配置界面", True, MUTED)
    screen.blit(hint, (config_rect.x + (config_rect.w - hint.get_width()) // 2, config_rect.y + y_offset + 5))


def draw_warning_feed(ui, screen, width, height, events, scroll_offset_px=0):
    panel_w = 260
    panel_h = min(320, max(220, height - 120))
    rect = pygame.Rect(width - panel_w - 10, 10, panel_w, panel_h)
    ui._warning_feed_control_hitboxes = {}
    ui._warning_feed_scrollbar_track_rect = None
    ui._warning_feed_scrollbar_thumb_rect = None
    pygame.draw.rect(screen, PANEL_BG, rect, border_radius=6)
    pygame.draw.rect(screen, BORDER, rect, 1, border_radius=6)
    title = ui.small_font.render("预警事件", True, TEXT)
    screen.blit(title, (rect.x + 12, rect.y + 12))

    state = getattr(ui, "warning_feed_state", {}) or {}
    controls_rect = pygame.Rect(rect.x + 10, rect.y + 42, rect.w - 20, 46)
    labels = [
        ("sort", state.get("sort_label", "时间:新→旧")),
        ("group", state.get("group_label", "分组:时间")),
        ("type", state.get("type_label", "类型:全部")),
        ("truck", state.get("truck_label", "车辆:全部")),
    ]
    button_w = (controls_rect.w - 8) // 2
    button_h = 18
    for idx, (action, label) in enumerate(labels):
        row = idx // 2
        col = idx % 2
        button_rect = pygame.Rect(
            controls_rect.x + col * (button_w + 8),
            controls_rect.y + row * (button_h + 8),
            button_w,
            button_h,
        )
        ui._warning_feed_control_hitboxes[action] = button_rect
        pygame.draw.rect(screen, (22, 26, 36), button_rect, border_radius=5)
        pygame.draw.rect(screen, BORDER, button_rect, 1, border_radius=5)
        text = ui.tiny_font.render(label, True, TEXT)
        screen.blit(text, (button_rect.x + 6, button_rect.y + 3))

    content_rect = pygame.Rect(rect.x + 10, rect.y + 96, rect.w - 20, rect.h - 108)
    pygame.draw.rect(screen, INNER_BG, content_rect, border_radius=6)
    if not events:
        empty = ui.small_font.render("暂无预警事件", True, MUTED)
        screen.blit(empty, (content_rect.x + 12, content_rect.y + 12))
        return rect

    line_h = 48
    max_lines = max(1, content_rect.h // line_h)
    total = len(events)
    max_scroll = max(0, (total - max_lines) * line_h)
    scroll_offset_px = max(0, min(int(scroll_offset_px), int(max_scroll)))
    first_idx_from_bottom = scroll_offset_px // line_h
    start = max(0, total - max_lines - first_idx_from_bottom)
    end = total - first_idx_from_bottom
    scrollbar_w = 8 if max_scroll > 0 else 0
    text_right_padding = 18 if max_scroll > 0 else 8
    text_max_width = max(60, content_rect.w - text_right_padding - 12)

    y = content_rect.y + 8
    for ev in events[start:end]:
        ts = ev.get("timestamp_str", "")
        truck_id = str(ev.get("truck_id", ""))
        truck = truck_id[-4:]
        type_label = ev.get("warning_type_label") or "预警"
        msg = ev.get("message") or ev.get("warning_text") or ""
        val = ev.get("value_str") or ""
        sev = ev.get("severity", "info")
        event_key = (
            ev.get("timestamp_str", ""),
            truck_id,
            int(ev.get("warning_type", 0) or 0),
        )
        is_selected_truck = str(getattr(ui, "selected_truck_id", "")) == truck_id
        is_active_event = getattr(ui, "_active_warning_event_key", None) == event_key
        if is_active_event:
            row_rect = pygame.Rect(content_rect.x + 4, y - 2, content_rect.w - 12, line_h - 4)
            pygame.draw.rect(screen, SELECTED_BG, row_rect, border_radius=6)
            pygame.draw.rect(screen, SELECTED, row_rect, 2, border_radius=6)
        elif is_selected_truck:
            row_rect = pygame.Rect(content_rect.x + 4, y - 2, content_rect.w - 12, line_h - 4)
            pygame.draw.rect(screen, (26, 32, 46), row_rect, border_radius=6)
            pygame.draw.rect(screen, BORDER, row_rect, 1, border_radius=6)
        color = WARNING if sev in ("high", "critical") else MEDIUM if sev == "medium" else TEXT
        head_color = SELECTED if is_active_event else (TEXT if is_selected_truck else MUTED)
        screen.blit(ui.tiny_font.render(f"{ts}  #{truck}", True, head_color), (content_rect.x + 10, y))
        line_text = f"[{type_label}] {msg} {val}".strip()
        wrapped = _fit_text_lines(ui.small_font, line_text, text_max_width, max_lines=2)
        for line_idx, line in enumerate(wrapped):
            line_y = y + 14 + line_idx * 15
            screen.blit(ui.small_font.render(line, True, color), (content_rect.x + 10, line_y))
        y += line_h

    if max_scroll > 0:
        track = pygame.Rect(content_rect.right - scrollbar_w - 6, content_rect.y + 6, scrollbar_w, content_rect.h - 12)
        pygame.draw.rect(screen, (34, 38, 48), track, border_radius=3)
        thumb_h = max(18, int(track.h * (content_rect.h / float(content_rect.h + max_scroll))))
        thumb_y = track.y + int(((max_scroll - scroll_offset_px) / max_scroll) * (track.h - thumb_h))
        thumb = pygame.Rect(track.x, thumb_y, track.w, thumb_h)
        pygame.draw.rect(screen, (88, 96, 116), thumb, border_radius=3)
        ui._warning_feed_scrollbar_track_rect = track
        ui._warning_feed_scrollbar_thumb_rect = thumb
    return rect
