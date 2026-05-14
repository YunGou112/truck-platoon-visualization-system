import pygame


BG_NORMAL = (18, 22, 32)
BG_WARNING = (44, 24, 28)
BOX_BG = (15, 18, 26)
BORDER = (52, 60, 82)
TEXT = (184, 192, 206)
MUTED = (126, 136, 152)
VALUE = (218, 226, 238)
SELECTED = (232, 202, 112)
WARNING = (232, 114, 114)
ACCENT = (82, 116, 176)


def draw_bottom_tiles(ui, screen, width, height, tiles):
    if not tiles:
        return
    gap = 10
    tile_h = 78
    max_tiles = max(1, int((width - 20 + gap) // (160 + gap)))
    tiles = tiles[:max_tiles]
    usable_w = width - 20 - gap * (len(tiles) - 1)
    tile_w = max(140, int(usable_w / len(tiles)))
    y = height - 10 - tile_h
    x = 10
    for tile in tiles:
        rect = pygame.Rect(x, y, tile_w, tile_h)
        pygame.draw.rect(screen, BG_NORMAL, rect, border_radius=8)
        pygame.draw.rect(screen, BORDER, rect, 1, border_radius=8)
        screen.blit(ui.tiny_font.render(str(tile.get("title", "")), True, TEXT), (rect.x + 10, rect.y + 8))
        value = tile.get("value")
        value_str = "-" if value is None else (f"{value:.1f}" if isinstance(value, float) else str(value))
        screen.blit(ui.font.render(value_str, True, tile.get("color", (0, 150, 255))), (rect.x + 10, rect.y + 26))
        unit = tile.get("unit", "")
        if unit:
            unit_surf = ui.small_font.render(unit, True, MUTED)
            screen.blit(unit_surf, (rect.right - unit_surf.get_width() - 10, rect.bottom - unit_surf.get_height() - 8))
        x += tile_w + gap


def draw_vehicle_tiles(ui, screen, width, height, vehicle_tiles, start_x=0, bottom_padding=0):
    if not vehicle_tiles:
        return None
    ui._vehicle_tile_hitboxes = {}
    gap = 8
    tile_h = 100
    min_tile_w = 220
    max_tile_w = 320
    avail_w = max(1, int(width - int(start_x)))
    cols = min(len(vehicle_tiles), max(1, int((avail_w + gap) // (min_tile_w + gap))))
    rows = (len(vehicle_tiles) + cols - 1) // cols
    usable_w = avail_w - gap * (cols - 1)
    tile_w = max(min_tile_w, min(max_tile_w, int(usable_w / cols)))
    start_y = max(0, height - int(bottom_padding) - rows * tile_h - (rows - 1) * gap)

    def fmt_num(value, precision):
        if value is None:
            return "-"
        if isinstance(value, (int, float)):
            return format(value, precision)
        return "-"

    for idx, tile in enumerate(vehicle_tiles):
        row = idx // cols
        col = idx % cols
        rect = pygame.Rect(int(start_x) + col * (tile_w + gap), start_y + row * (tile_h + gap), tile_w, tile_h)
        is_warning = bool(tile.get("warning", False))
        truck_id = str(tile.get("truck_id", ""))
        is_selected = bool(tile.get("selected", False))
        ui._vehicle_tile_hitboxes[truck_id] = rect.copy()

        bg_color = BG_WARNING if is_warning else BG_NORMAL
        border_color = SELECTED if is_selected else BORDER
        top_color = SELECTED if is_selected else (WARNING if is_warning else ACCENT)
        header_color = SELECTED if is_selected else (WARNING if is_warning else TEXT)

        if is_selected:
            glow_rect = rect.inflate(4, 4)
            pygame.draw.rect(screen, (78, 68, 34), glow_rect, border_radius=12)
        pygame.draw.rect(screen, bg_color, rect, border_radius=10)
        pygame.draw.rect(screen, border_color, rect, 2 if is_selected else 1, border_radius=10)
        pygame.draw.rect(screen, top_color, pygame.Rect(rect.x, rect.y, rect.w, 6), border_radius=10)
        screen.blit(ui.small_font.render(f"车 {truck_id[-4:]}", True, header_color), (rect.x + 10, rect.y + 10))

        box_w = int((rect.w - 30) / 2)
        box_y = rect.y + 34
        box1 = pygame.Rect(rect.x + 10, box_y, box_w, 34)
        box2 = pygame.Rect(box1.right + 10, box_y, box_w, 34)
        for box in (box1, box2):
            pygame.draw.rect(screen, BOX_BG, box, border_radius=8)
            pygame.draw.rect(screen, BORDER, box, 1, border_radius=8)

        screen.blit(ui.tiny_font.render("实时车速", True, MUTED), (box1.x + 8, box1.y + 5))
        screen.blit(ui.tiny_font.render("实时车距", True, MUTED), (box2.x + 8, box2.y + 5))
        value_color = SELECTED if is_selected else VALUE
        screen.blit(ui.small_font.render(fmt_num(tile.get("speed_kmh"), ".0f"), True, value_color), (box1.x + 8, box1.y + 16))
        gap_value = tile.get("gap_m")
        gap_color = WARNING if isinstance(gap_value, (int, float)) and gap_value < 20 else value_color
        screen.blit(ui.small_font.render(fmt_num(gap_value, ".1f"), True, gap_color), (box2.x + 8, box2.y + 16))
        unit1 = ui.tiny_font.render("km/h", True, MUTED)
        unit2 = ui.tiny_font.render("m", True, MUTED)
        screen.blit(unit1, (box1.right - unit1.get_width() - 6, box1.y + 18))
        screen.blit(unit2, (box2.right - unit2.get_width() - 6, box2.y + 18))

        drive_time_s = tile.get("drive_time_s")
        if isinstance(drive_time_s, (int, float)):
            tt_int = int(max(0, drive_time_s))
            time_str = f"{tt_int//60:02d}:{tt_int%60:02d}"
        else:
            time_str = "-"
        line3 = ui.tiny_font.render(f"行驶时间  {time_str}", True, TEXT)
        line4 = ui.tiny_font.render(f"行驶距离  {fmt_num(tile.get('drive_dist'), '.2f')} km", True, TEXT)
        screen.blit(line3, (rect.x + 10, box1.bottom + 10))
        screen.blit(line4, (rect.right - line4.get_width() - 10, box1.bottom + 10))
    return start_y
