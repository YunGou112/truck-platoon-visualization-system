import os
import sys
import pygame


def main():
    print("Running smoke test...")
    pygame.init()
    print("Pygame initialized successfully")

    try:
        pygame.font.SysFont("Microsoft YaHei", 12)
        print("Microsoft YaHei font loaded successfully")
    except Exception:
        pygame.font.Font(None, 12)
        print("Default font loaded successfully")

    icon_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "assets",
        "truck_normal.png",
    )
    if os.path.exists(icon_path):
        try:
            pygame.image.load(icon_path)
            print(f"Truck icon loaded successfully: {icon_path}")
        except Exception as e:
            print(f"Truck icon load failed: {e}")
    else:
        print(f"Truck icon not found (optional): {icon_path}")

    pygame.quit()
    print("Smoke test completed")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Smoke test failed: {e}")
        sys.exit(1)
