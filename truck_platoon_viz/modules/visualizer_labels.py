import pygame


def draw_compact_labels(viz, ordered_trucks):
    """绘制紧凑标签，降低遮挡。"""
    existing = []
    for truck in ordered_trucks:
        sx = truck.current_pos_data.get("screen_x")
        sy = truck.current_pos_data.get("screen_y")
        if sx is None or sy is None:
            continue

        compact = f"{str(truck.id)[-4:]} {truck.get_speed():.0f}km/h"
        text = viz._render_text_cached(compact, (245, 245, 245), "small")
        width = text.get_width() + 8
        height = text.get_height() + 4
        candidates = [
            pygame.Rect(sx + 12, sy - 26, width, height),
            pygame.Rect(sx + 12, sy + 10, width, height),
            pygame.Rect(sx - width - 12, sy - 26, width, height),
            pygame.Rect(sx - width - 12, sy + 10, width, height),
        ]
        label_rect = candidates[0]
        for candidate in candidates:
            if candidate.left < 0 or candidate.top < 0 or candidate.right > viz.width or candidate.bottom > viz.height:
                continue
            if any(candidate.colliderect(rect) for rect in existing):
                continue
            label_rect = candidate
            break

        bg = (140, 50, 50) if truck.warning else (38, 38, 44)
        pygame.draw.rect(viz.screen, bg, label_rect, border_radius=3)
        pygame.draw.rect(viz.screen, (220, 220, 220), label_rect, 1, border_radius=3)
        viz.screen.blit(text, (label_rect.x + 4, label_rect.y + 2))
        existing.append(label_rect)

        if str(truck.id) == str(viz.selected_truck_id):
            detail_lines = [
                f"ID: {truck.id}",
                f"v: {truck.get_speed():.1f} km/h",
                f"a: {truck.get_acceleration():.2f} m/s2",
                f"warn: {truck.warning_text if truck.warning_text else 'none'}",
            ]
            panel = pygame.Rect(label_rect.x, label_rect.y - 82, 200, 78)
            if panel.top < 0:
                panel.y = label_rect.bottom + 6
            if panel.right > viz.width:
                panel.x = viz.width - panel.width - 8
            pygame.draw.rect(viz.screen, (18, 18, 24), panel, border_radius=5)
            pygame.draw.rect(viz.screen, (255, 230, 120), panel, 2, border_radius=5)
            for idx, line in enumerate(detail_lines):
                line_surf = viz._render_text_cached(line, (245, 245, 245), "small")
                viz.screen.blit(line_surf, (panel.x + 8, panel.y + 6 + idx * 16))
