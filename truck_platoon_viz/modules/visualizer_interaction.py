import pygame
import logging


logger = logging.getLogger(__name__)


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
        elif event.key == pygame.K_n:
            if not viz._navigate_warning_event(processor, +1):
                logger.info("没有下一条预警事件。")
        elif event.key == pygame.K_p:
            if not viz._navigate_warning_event(processor, -1):
                logger.info("没有上一条预警事件。")
        elif event.key == pygame.K_r:
            viz.current_sim_time = processor.min_time
            viz.play_speed = 1
            viz.is_playing = True
            viz._warning_nav_index = None
            viz._active_warning_event_key = None
            viz.warning_feed_truck_filter = "all"
            viz.warning_feed_type_filter = 0
            viz.warning_feed_group_by = "time"
            viz.warning_feed_sort_desc = True
            for truck in processor.trucks.values():
                truck.reset()
            viz.view_zoom = 1.0
            viz.view_offset_x = 0
            viz.view_offset_y = 0
            logger.info("已重置时间、速度与视图状态。")
        elif event.key == pygame.K_e:
            viz._export_data(processor)
        elif event.key == pygame.K_f:
            viz._export_all_data(processor)
        elif event.key == pygame.K_c:
            viz.show_config = not viz.show_config
            logger.info("配置界面%s。", "显示" if viz.show_config else "隐藏")
        elif event.key == pygame.K_x:
            viz.selected_truck_id = None
            viz._warning_nav_index = None
            viz._active_warning_event_key = None
            if hasattr(viz, "ui_elements_system"):
                viz.ui_elements_system.selected_truck_id = None
                viz.ui_elements_system._active_warning_event_key = None

    elif event.type == pygame.VIDEORESIZE:
        viz.width = max(640, int(event.w))
        viz.height = max(480, int(event.h))
        viz.screen = pygame.display.set_mode((viz.width, viz.height), pygame.RESIZABLE)
        viz.background_surface = viz._build_background_surface()
        viz._warning_feed_rect = pygame.Rect(viz.width - 260 - 10, 10, 260, min(320, max(220, viz.height - 120)))
        viz.dragging_warning_scrollbar = False
        viz._text_cache.clear()
        return

    elif event.type == pygame.MOUSEWHEEL:
        mx, my = pygame.mouse.get_pos()
        if viz._warning_feed_rect.collidepoint((mx, my)):
            max_scroll = viz._warning_feed_get_max_scroll_px()
            viz._warning_feed_scroll_px = max(0, min(max_scroll, viz._warning_feed_scroll_px + event.y * 40))
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
                control = viz._pick_warning_feed_control_at(event.pos)
                if control is not None:
                    viz._cycle_warning_feed_action(control)
                    viz.dragging_map = False
                    return
                scrollbar_part = viz._pick_warning_feed_scrollbar_part_at(event.pos)
                if scrollbar_part == "thumb":
                    thumb = getattr(viz.ui_elements_system, "_warning_feed_scrollbar_thumb_rect", None)
                    viz.dragging_warning_scrollbar = True
                    viz.dragging_map = False
                    viz._warning_scrollbar_drag_offset_y = event.pos[1] - thumb.y if thumb is not None else 0
                    return
                if scrollbar_part == "track":
                    viz.dragging_warning_scrollbar = True
                    viz.dragging_map = False
                    thumb = getattr(viz.ui_elements_system, "_warning_feed_scrollbar_thumb_rect", None)
                    viz._warning_scrollbar_drag_offset_y = (thumb.h / 2.0) if thumb is not None else 0
                    viz._set_warning_feed_scroll_from_pointer(event.pos[1], keep_thumb_center=True)
                    return
                picked = viz._pick_warning_event_at(event.pos)
                if picked:
                    if not viz._jump_to_warning_event(processor, picked, pause=True):
                        logger.debug("根据预警事件时间跳转失败。")
                viz.dragging_map = False
                return

            tile_truck_id = viz._pick_vehicle_tile_at(event.pos)
            if tile_truck_id is not None:
                viz.selected_truck_id = tile_truck_id
                viz._warning_nav_index = None
                viz._active_warning_event_key = None
                if hasattr(viz, "ui_elements_system"):
                    viz.ui_elements_system.selected_truck_id = tile_truck_id
                    viz.ui_elements_system._active_warning_event_key = None
                viz.dragging_map = False
                return

            selected = viz._pick_truck_at(event.pos, processor)
            if selected is not None:
                viz.selected_truck_id = selected.id
                viz._warning_nav_index = None
                viz._active_warning_event_key = None
                if hasattr(viz, "ui_elements_system"):
                    viz.ui_elements_system.selected_truck_id = selected.id
                    viz.ui_elements_system._active_warning_event_key = None
                viz.dragging_map = False
            else:
                viz.dragging_map = True
                viz.last_mouse_pos = event.pos

    elif event.type == pygame.MOUSEBUTTONUP:
        if event.button == 1:
            viz.dragging_progress = False
            viz.dragging_map = False
            viz.dragging_warning_scrollbar = False

    elif event.type == pygame.MOUSEMOTION:
        if viz.dragging_progress:
            viz._seek_to_progress(processor, event.pos[0])
        elif viz.dragging_warning_scrollbar:
            viz._set_warning_feed_scroll_from_pointer(event.pos[1], keep_thumb_center=False)
        elif viz.dragging_map:
            dx = event.pos[0] - viz.last_mouse_pos[0]
            dy = event.pos[1] - viz.last_mouse_pos[1]
            viz.view_offset_x += dx
            viz.view_offset_y += dy
            viz.last_mouse_pos = event.pos
