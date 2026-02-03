"""
Capture Training Data for YOLO Road Sign Detection - ACC 2026

Drive around QLabs and press keys to label signs with bounding boxes.
Images are saved to datasets/signs/images/
Labels are saved to datasets/signs/labels/ (YOLO detection format)

Sign Classes:
- 1 key: STOP sign
- 2 key: YIELD sign
- 3 key: ROUNDABOUT sign

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
from qvl.stop_sign import QLabsStopSign
from qvl.yield_sign import QLabsYieldSign
from qvl.roundabout_sign import QLabsRoundaboutSign


# Dataset directories
BASE_DIR = os.path.dirname(__file__)
IMAGES_DIR = os.path.join(BASE_DIR, "datasets", "signs", "images")
LABELS_DIR = os.path.join(BASE_DIR, "datasets", "signs", "labels")

# Sign classes (YOLO detection format: class_id, not name)
SIGN_CLASSES = {
    '1': {'id': 0, 'name': 'stop'},
    '2': {'id': 1, 'name': 'yield'},
    '3': {'id': 2, 'name': 'roundabout'},
}

# Mouse callback state
mouse_state = {
    'labeling': False,
    'current_class': None,
    'start_point': None,
    'end_point': None,
    'drawing': False,
    'temp_image': None,
}


def setup_directories():
    """Create dataset directories."""
    os.makedirs(IMAGES_DIR, exist_ok=True)
    os.makedirs(LABELS_DIR, exist_ok=True)
    print(f"Images: {IMAGES_DIR}")
    print(f"Labels: {LABELS_DIR}")


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

    # --- SIGNS ---
    print("  Spawning signs...")

    # Yield Sign
    myYieldSign = QLabsYieldSign(qlabs)
    myYieldSign.spawn_degrees(location=[0.0, -1.3, 0.006], rotation=[0, 0, -180], scale=[0.1, 0.1, 0.1], waitForConfirmation=False)

    # Stop Signs
    myStopSign = QLabsStopSign(qlabs)
    myStopSign.spawn_degrees(location=[-1.5, 3.6, 0.006], rotation=[0, 0, -35], scale=[0.1, 0.1, 0.1], waitForConfirmation=False)
    myStopSign.spawn_degrees(location=[-1.5, 2.2, 0.006], rotation=[0, 0, 35], scale=[0.1, 0.1, 0.1], waitForConfirmation=False)
    myStopSign.spawn_degrees(location=[2.410, 0.206, 0.006], rotation=[0, 0, -90], scale=[0.1, 0.1, 0.1], waitForConfirmation=False)
    myStopSign.spawn_degrees(location=[1.766, 1.697, 0.006], rotation=[0, 0, 90], scale=[0.1, 0.1, 0.1], waitForConfirmation=False)

    # Roundabout Signs
    myRoundaboutSign = QLabsRoundaboutSign(qlabs)
    myRoundaboutSign.spawn_degrees(location=[2.392, 2.522, 0.006], rotation=[0, 0, -90], scale=[0.1, 0.1, 0.1], waitForConfirmation=False)
    myRoundaboutSign.spawn_degrees(location=[0.698, 2.483, 0.006], rotation=[0, 0, -145], scale=[0.1, 0.1, 0.1], waitForConfirmation=False)
    myRoundaboutSign.spawn_degrees(location=[0.007, 3.973, 0.006], rotation=[0, 0, 135], scale=[0.1, 0.1, 0.1], waitForConfirmation=False)

    print("  Signs spawned: 1 yield, 4 stop, 3 roundabout")

    cam = QLabsFreeCamera(qlabs)
    cam.spawn_degrees(location=[0.15, 1.7, 5], rotation=[0, 90, 0])
    cam.possess()

    print("  Environment ready!")


def mouse_callback(event, x, y, flags, param):
    """Handle mouse events for bounding box drawing."""
    global mouse_state

    if not mouse_state['labeling']:
        return

    if event == cv2.EVENT_LBUTTONDOWN:
        mouse_state['drawing'] = True
        mouse_state['start_point'] = (x, y)
        mouse_state['end_point'] = None

    elif event == cv2.EVENT_MOUSEMOVE:
        if mouse_state['drawing']:
            mouse_state['end_point'] = (x, y)

    elif event == cv2.EVENT_LBUTTONUP:
        mouse_state['drawing'] = False
        mouse_state['end_point'] = (x, y)


def save_yolo_label(filename_base, bbox, class_id, img_width, img_height):
    """
    Save YOLO detection format label.

    Format: class_id x_center y_center width height (all normalized 0-1)
    """
    x1, y1, x2, y2 = bbox

    # Calculate center and size (normalized)
    x_center = ((x1 + x2) / 2) / img_width
    y_center = ((y1 + y2) / 2) / img_height
    width = abs(x2 - x1) / img_width
    height = abs(y2 - y1) / img_height

    # Clamp to [0, 1]
    x_center = max(0, min(1, x_center))
    y_center = max(0, min(1, y_center))
    width = max(0, min(1, width))
    height = max(0, min(1, height))

    label_path = os.path.join(LABELS_DIR, f"{filename_base}.txt")

    # Append to file (allows multiple boxes per image)
    with open(label_path, 'a') as f:
        f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")


def count_images():
    """Count labeled images."""
    if not os.path.exists(IMAGES_DIR):
        return 0
    images = [f for f in os.listdir(IMAGES_DIR) if f.endswith('.jpg')]
    return len(images)


def count_labels():
    """Count labels by class."""
    counts = {info['name']: 0 for info in SIGN_CLASSES.values()}

    if not os.path.exists(LABELS_DIR):
        return counts

    for label_file in os.listdir(LABELS_DIR):
        if not label_file.endswith('.txt'):
            continue

        label_path = os.path.join(LABELS_DIR, label_file)
        with open(label_path, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if parts:
                    class_id = int(parts[0])
                    for info in SIGN_CLASSES.values():
                        if info['id'] == class_id:
                            counts[info['name']] += 1

    return counts


def main():
    global mouse_state

    os.system('cls' if os.name == 'nt' else 'clear')
    print("=" * 60)
    print("  YOLO Sign Detection Training Data Capture")
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
    print("  LABEL SIGNS (two-step process):")
    print("    1. Press 1/2/3 to select sign type")
    print("    2. Click and drag to draw bounding box")
    print("    3. Box is saved when you release mouse")
    print("")
    print("  Sign Types:")
    print("    1 = STOP")
    print("    2 = YIELD")
    print("    3 = ROUNDABOUT")
    print("")
    print("  ESC = Cancel current box")
    print("  Q = Quit")
    print("=" * 60)

    # Create window and set mouse callback
    cv2.namedWindow("Sign Capture", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Sign Capture", 800, 600)
    cv2.setMouseCallback("Sign Capture", mouse_callback)

    speed = 0.0
    turn = 0.0
    running = True

    while running:
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
                turn = -0.4
            elif keyboard.is_pressed('right'):
                turn = 0.4
            else:
                turn *= 0.8


        # Get camera image
        success, image = car.get_image(camera=car.CAMERA_CSI_FRONT)

        if success and image is not None:
            display = image.copy()
            h, w = display.shape[:2]

            # If labeling, store original for saving
            if mouse_state['labeling'] and mouse_state['temp_image'] is None:
                mouse_state['temp_image'] = image.copy()

            # Show current counts
            counts = count_labels()
            total_labels = sum(counts.values())
            y = 25
            cv2.putText(display, f"Labels: {total_labels}", (10, y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            for name, count in counts.items():
                y += 22
                cv2.putText(display, f"  {name}: {count}", (10, y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

            # Show labeling status
            if mouse_state['labeling']:
                class_name = mouse_state['current_class']['name']
                cv2.putText(display, f"LABELING: {class_name.upper()}",
                           (w//2 - 100, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                cv2.putText(display, "Draw box with mouse",
                           (w//2 - 100, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)

                # Draw current bounding box
                if mouse_state['start_point'] and mouse_state['end_point']:
                    cv2.rectangle(display,
                                mouse_state['start_point'],
                                mouse_state['end_point'],
                                (0, 255, 0), 2)

            cv2.imshow("Sign Capture", display)

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

        # Check for labeling mode activation via number keys (1, 2, 3)
        # Using cv2.waitKey instead of keyboard library to avoid arrow key conflicts
        if key in [ord('1'), ord('2'), ord('3')]:
            key_char = chr(key)
            if key_char in SIGN_CLASSES and not mouse_state['labeling']:
                info = SIGN_CLASSES[key_char]
                mouse_state['labeling'] = True
                mouse_state['current_class'] = info
                mouse_state['start_point'] = None
                mouse_state['end_point'] = None
                print(f"\nLabeling mode: {info['name'].upper()}")
                print("  Draw bounding box with mouse...")

        if key == 27:  # ESC - cancel labeling or quit
            if mouse_state['labeling']:
                print("  Cancelled.")
                mouse_state['labeling'] = False
                mouse_state['temp_image'] = None
            else:
                running = False

        # Check if box is complete
        if (mouse_state['labeling'] and
            mouse_state['start_point'] and
            mouse_state['end_point'] and
            not mouse_state['drawing']):

            # Save image and label
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename_base = f"sign_{timestamp}"

            # Save image
            img_path = os.path.join(IMAGES_DIR, f"{filename_base}.jpg")
            cv2.imwrite(img_path, mouse_state['temp_image'])

            # Save label
            x1, y1 = mouse_state['start_point']
            x2, y2 = mouse_state['end_point']
            bbox = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))

            save_yolo_label(
                filename_base,
                bbox,
                mouse_state['current_class']['id'],
                mouse_state['temp_image'].shape[1],
                mouse_state['temp_image'].shape[0]
            )

            print(f"  Saved: {filename_base}.jpg + label")

            # Reset labeling state
            mouse_state['labeling'] = False
            mouse_state['temp_image'] = None
            mouse_state['start_point'] = None
            mouse_state['end_point'] = None

    # Final counts
    print("\n" + "=" * 60)
    print("  Final label counts:")
    for name, count in count_labels().items():
        print(f"    {name}: {count}")
    print(f"  Total images: {count_images()}")
    print("=" * 60)

    car.set_velocity_and_request_state(0, 0, False, False, False, True, False)
    cv2.destroyAllWindows()
    qlabs.close()
    print("Done!")


if __name__ == '__main__':
    main()
