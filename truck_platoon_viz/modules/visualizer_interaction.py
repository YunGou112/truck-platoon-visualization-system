import pandas as pd
import pygame


def handle_event(viz, event, processor):
    # 键盘事件
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_SPACE:
            viz.is_playing = not viz.is_playing
        elif event.key == pygame.K_UP:
            viz.play_speed = int(min(viz.max_play_speed, int(viz.play_speed) + 1))
        elif event.key == pygame.K_DOWN:
            viz.play_speed = int(max(viz.min_play_speed, int(viz.play_speed) - 1))
        elif event.key == pygame.K_RIGHT:
            viz._seek_seconds(processor, +5)
        elif event.key == pygame.K_LEFT:
            viz._seek_seconds(processor, -5)
        elif event.key == pygame.K_r:
            viz.current_sim_time = processor.min_time
            viz.play_speed = 1
            viz.is_playing = True
            for truck in processor.trucks.values():
                truck.reset()
            viz.view_zoom = 1.0
            viz.view_offset_x = 0
            viz.view_offset_y = 0
            print(">>> 重置状态 (时间、速度、视图) <<<")
        elif event.key == pygame.K_e:
            viz._export_data(processor)
        elif event.key == pygame.K_f:
            viz._export_all_data(processor)
        elif event.key == pygame.K_c:
            viz.show_config = not viz.show_config
            print(f"配置界面 {'显示' if viz.show_config else '隐藏'}")
        elif event.key == pygame.K_x:
            viz.selected_truck_id = None

    elif event.type == pygame.VIDEORESIZE:
        viz.width = max(640, int(event.w))
        viz.height = max(480, int(event.h))
        viz.screen = pygame.display.set_mode((viz.width, viz.height), pygame.RESIZABLE)
        viz.background_surface = viz._build_background_surface()
        viz._warning_feed_rect = pygame.Rect(viz.width - 260 - 10, 10, 260, min(320, max(220, viz.height - 120)))
        viz._text_cache.clear()
        return

    elif event.type == pygame.MOUSEWHEEL:
        mx, my = pygame.mouse.get_pos()
        if viz._warning_feed_rect.collidepoint((mx, my)):
            max_scroll = viz._warning_feed_get_max_scroll_px()
            viz._warning_feed_scroll_px = max(0, min(max_scroll, viz._warning_feed_scroll_px - event.y * 40))
            return

        mx, my = pygame.mouse.get_pos()
        screen_cx = viz.width / 2
        screen_cy = viz.height / 2
        mouse_rel_x = mx - screen_cx
        mouse_rel_y = my - screen_cy
        old_zoom = viz.view_zoom
        zoom_factor = 1.1 if event.y > 0 else 0.9
        new_zoom = old_zoom * zoom_factor
        new_zoom = max(0.1, min(20.0, new_zoom))
        ratio = new_zoom / old_zoom
        viz.view_offset_x = mouse_rel_x - (mouse_rel_x - viz.view_offset_x) * ratio
        viz.view_offset_y = mouse_rel_y - (mouse_rel_y - viz.view_offset_y) * ratio
        viz.view_zoom = new_zoom

    elif event.type == pygame.MOUSEBUTTONDOWN:
        if event.button == 1:
            if viz._progress_rect is not None and viz._progress_rect.collidepoint(event.pos):
                viz.dragging_progress = True
                viz.dragging_map = False
                viz.is_playing = False
                viz._seek_to_progress(processor, event.pos[0])
                return

            if viz._warning_feed_rect.collidepoint(event.pos):
                picked = viz._pick_warning_event_at(event.pos)
                if picked:
                    viz.selected_truck_id = picked.get("truck_id")
                    ts = picked.get("timestamp_str")
                    if ts:
                        try:
                            t = pd.to_datetime(ts, errors="coerce")
                            if pd.notna(t):
                                viz.current_sim_time = t.to_pydatetime() if hasattr(t, "to_pydatetime") else t
                                for ttruck in processor.trucks.values():
                                    ttruck.update(viz.current_sim_time)
                        except Exception:
                            pass
                viz.dragging_map = False
                return

            selected = viz._pick_truck_at(event.pos, processor)
            if selected is not None:
                viz.selected_truck_id = selected.id
                viz.dragging_map = False
            else:
                viz.dragging_map = True
                viz.last_mouse_pos = event.pos

    elif event.type == pygame.MOUSEBUTTONUP:
        if event.button == 1:
            viz.dragging_progress = False
            viz.dragging_map = False

    elif event.type == pygame.MOUSEMOTION:
        if viz.dragging_progress:
            viz._seek_to_progress(processor, event.pos[0])
        elif viz.dragging_map:
            dx = event.pos[0] - viz.last_mouse_pos[0]
            dy = event.pos[1] - viz.last_mouse_pos[1]
            viz.view_offset_x += dx
            viz.view_offset_y += dy
            viz.last_mouse_pos = event.pos
