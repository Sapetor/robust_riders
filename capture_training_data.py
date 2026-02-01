"""
Capture Training Data for YOLO Road Feature Detection - ACC 2026

Drive around the competition floor and press keys to save labeled images.
Images are saved to datasets/road_features/{class_name}/

Classes:
- STRAIGHT (S key)
- CURVE_LEFT (L key)
- CURVE_RIGHT (R key)
- INTERSECTION (I key)
- ROUNDABOUT (O key)

*** Run in PLANE workspace ***
"""

import os
import time
import cv2
import numpy as np
from datetime import datetime

try:
    import keyboard
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False
    print("Warning: 'keyboard' module not found.")

from qvl.qlabs import QuanserInteractiveLabs
from qvl.qcar2 import QLabsQCar2
from qvl.free_camera import QLabsFreeCamera
from qvl.qcar_flooring import QLabsQCarFlooring
from qvl.walls import QLabsWalls


# Dataset directory
DATASET_DIR = os.path.join(os.path.dirname(__file__), "datasets", "road_features")

# Classes for YOLO
CLASSES = {
    's': 'straight',
    'l': 'curve_left',
    'r': 'curve_right',
    'i': 'intersection',
    'o': 'roundabout',
}


def setup_directories():
    """Create dataset directories for each class."""
    for class_name in CLASSES.values():
        class_dir = os.path.join(DATASET_DIR, class_name)
        os.makedirs(class_dir, exist_ok=True)
    print(f"Dataset directory: {DATASET_DIR}")


def setup_environment(qlabs):
    """Spawn competition floor (same as hybrid_navigation.py)."""
    print("  Spawning competition floor...")

    x_offset = 0.13
    y_offset = 1.67

    hFloor = QLabsQCarFlooring(qlabs)
    hFloor.spawn_degrees([x_offset, y_offset, 0.001], rotation=[0, 0, -90])

    hWall = QLabsWalls(qlabs)
    hWall.set_enable_dynamics(False)

    for y in range(5):
        hWall.spawn_degrees(location=[-2.4 + x_offset, (-y*1.0)+2.55 + y_offset, 0.001], rotation=[0, 0, 0])
    for x in range(5):
        hWall.spawn_degrees(location=[-1.9+x + x_offset, 3.05+ y_offset, 0.001], rotation=[0, 0, 90])
    for y in range(6):
        hWall.spawn_degrees(location=[2.4+ x_offset, (-y*1.0)+2.55 + y_offset, 0.001], rotation=[0, 0, 0])
    for x in range(4):
        hWall.spawn_degrees(location=[-0.9+x+ x_offset, -3.05+ y_offset, 0.001], rotation=[0, 0, 90])

    hWall.spawn_degrees(location=[-2.03 + x_offset, -2.275+ y_offset, 0.001], rotation=[0, 0, 48])
    hWall.spawn_degrees(location=[-1.575+ x_offset, -2.7+ y_offset, 0.001], rotation=[0, 0, 48])

    cam = QLabsFreeCamera(qlabs)
    cam.spawn_degrees(location=[0.15, 1.7, 5], rotation=[0, 90, 0])
    cam.possess()

    print("  Environment ready!")


def save_image(image, class_name):
    """Save image with timestamp to class directory."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{class_name}_{timestamp}.jpg"
    filepath = os.path.join(DATASET_DIR, class_name, filename)
    cv2.imwrite(filepath, image)
    return filename


def count_images():
    """Count images in each class directory."""
    counts = {}
    for class_name in CLASSES.values():
        class_dir = os.path.join(DATASET_DIR, class_name)
        if os.path.exists(class_dir):
            counts[class_name] = len([f for f in os.listdir(class_dir) if f.endswith('.jpg')])
        else:
            counts[class_name] = 0
    return counts


def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("=" * 60)
    print("  YOLO Training Data Capture - Road Features")
    print("=" * 60)

    setup_directories()

    # Connect to QLabs
    qlabs = QuanserInteractiveLabs()
    print("\nConnecting to QLabs...")

    if not qlabs.open("localhost"):
        print("Could not connect! Make sure QLabs is running with PLANE workspace.")
        return

    print("Connected!")

    qlabs.destroy_all_spawned_actors()
    time.sleep(0.5)

    setup_environment(qlabs)

    # Spawn QCar
    print("Spawning QCar...")
    car = QLabsQCar2(qlabs)
    car.spawn_id_degrees(
        actorNumber=0,
        location=[-1.205, -0.83, 0.005],
        rotation=[0, 0, -44.7],
        scale=[0.1, 0.1, 0.1],
        configuration=0,
        waitForConfirmation=True
    )

    time.sleep(2.0)

    print("\n" + "=" * 60)
    print("  CONTROLS:")
    print("  Arrow keys = Drive")
    print("  SPACE = Stop")
    print("")
    print("  LABEL & SAVE (press while viewing road type):")
    print("    S = STRAIGHT")
    print("    L = CURVE_LEFT")
    print("    R = CURVE_RIGHT")
    print("    I = INTERSECTION")
    print("    O = ROUNDABOUT")
    print("")
    print("  Q = Quit")
    print("=" * 60)

    cv2.namedWindow("Capture", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Capture", 800, 600)

    speed = 0.0
    turn = 0.0
    last_save_time = 0
    save_cooldown = 0.3  # Seconds between saves

    running = True
    while running:
        current_time = time.time()

        # Driving controls
        if HAS_KEYBOARD:
            if keyboard.is_pressed('q'):
                running = False
            elif keyboard.is_pressed('space'):
                speed = 0.0
                turn = 0.0
            elif keyboard.is_pressed('up'):
                speed = min(speed + 0.05, 1.0)
            elif keyboard.is_pressed('down'):
                speed = max(speed - 0.05, -0.5)

            if keyboard.is_pressed('left'):
                turn = 0.4
            elif keyboard.is_pressed('right'):
                turn = -0.4
            else:
                turn *= 0.8  # Decay

        # Get camera image
        success, image = car.get_image(camera=car.CAMERA_CSI_FRONT)

        if success and image is not None:
            display = image.copy()
            h, w = display.shape[:2]

            # Show current counts
            counts = count_images()
            y = 25
            cv2.putText(display, "Images captured:", (10, y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            for class_name, count in counts.items():
                y += 22
                cv2.putText(display, f"  {class_name}: {count}", (10, y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

            # Show speed
            cv2.putText(display, f"Speed: {speed:.2f}", (w - 150, 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 0), 2)

            # Check for label keys (with cooldown)
            if HAS_KEYBOARD and (current_time - last_save_time) > save_cooldown:
                for key, class_name in CLASSES.items():
                    if keyboard.is_pressed(key):
                        filename = save_image(image, class_name)
                        print(f"  Saved: {class_name}/{filename}")
                        last_save_time = current_time

                        # Flash indicator
                        cv2.putText(display, f"SAVED: {class_name.upper()}",
                                   (w//2 - 100, h//2),
                                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
                        break

            cv2.imshow("Capture", display)

            # Apply control
            car.set_velocity_and_request_state(
                forward=speed,
                turn=turn,
                headlights=False,
                leftTurnSignal=False,
                rightTurnSignal=False,
                brakeSignal=(speed == 0),
                reverseSignal=(speed < 0)
            )

        key = cv2.waitKey(30) & 0xFF
        if key == 27:  # ESC
            running = False

    # Final counts
    print("\n" + "=" * 60)
    print("  Final image counts:")
    for class_name, count in count_images().items():
        print(f"    {class_name}: {count}")
    print("=" * 60)

    car.set_velocity_and_request_state(0, 0, False, False, False, True, False)
    cv2.destroyAllWindows()
    qlabs.close()
    print("Done!")


if __name__ == '__main__':
    main()
