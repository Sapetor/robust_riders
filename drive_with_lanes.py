"""
QCar 2 Drive + Lane Detection - ACC 2026
Drive the car while seeing lane detection in real-time

Run in CITYSCAPE workspace!
"""

import os
import time
import cv2
import numpy as np
import keyboard

from qvl.qlabs import QuanserInteractiveLabs
from qvl.qcar2 import QLabsQCar2


def detect_lanes(image):
    """Detect lane lines and return annotated image."""
    height, width = image.shape[:2]
    
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)
    
    # Region of interest
    roi_vertices = np.array([[
        (0, height),
        (width * 0.4, height * 0.6),
        (width * 0.6, height * 0.6),
        (width, height)
    ]], dtype=np.int32)
    
    mask = np.zeros_like(edges)
    cv2.fillPoly(mask, roi_vertices, 255)
    masked_edges = cv2.bitwise_and(edges, mask)
    
    # Hough lines
    lines = cv2.HoughLinesP(masked_edges, 1, np.pi/180, 50, 
                            minLineLength=50, maxLineGap=150)
    
    output = image.copy()
    cv2.polylines(output, roi_vertices, True, (0, 255, 255), 2)
    
    left_count = 0
    right_count = 0
    
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if x2 - x1 == 0:
                continue
            slope = (y2 - y1) / (x2 - x1)
            if abs(slope) < 0.3:
                continue
            if slope < 0:
                cv2.line(output, (x1, y1), (x2, y2), (255, 0, 0), 3)
                left_count += 1
            else:
                cv2.line(output, (x1, y1), (x2, y2), (0, 0, 255), 3)
                right_count += 1
    
    cv2.putText(output, f"L:{left_count} R:{right_count}", (10, 30),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    return output


def main():
    os.system('cls')
    print("="*60)
    print("  QCar 2 Drive + Lane Detection")
    print("="*60)
    
    qlabs = QuanserInteractiveLabs()
    print("\nConnecting to QLabs...")
    
    if not qlabs.open("localhost"):
        print("❌ Could not connect!")
        return
    
    print("✅ Connected!")
    
    qlabs.destroy_all_spawned_actors()
    time.sleep(0.5)
    
    # Spawn QCar
    print("Spawning QCar...")
    car = QLabsQCar2(qlabs)
    car.spawn_id_degrees(
        actorNumber=0,
        location=[-8.7, 14.643, 0.005],  # From official tutorial - on a road
        rotation=[0, 0, 90],
        scale=[1, 1, 1],
        configuration=0,
        waitForConfirmation=True
    )
    
    print("\n" + "="*60)
    print("  CONTROLS:")
    print("  ↑↓ = Speed    ←→ = Steer")
    print("  Q = Quit")
    print("="*60)
    print("\n🚗 Drive to find lanes! Look at the camera window.")
    
    cv2.namedWindow("Lane Detection", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Lane Detection", 640, 480)
    
    speed = 0.0
    turn = 0.0
    
    running = True
    while running:
        # Handle driving
        if keyboard.is_pressed('q'):
            running = False
        elif keyboard.is_pressed('up'):
            speed = min(speed + 0.05, 2.0)
        elif keyboard.is_pressed('down'):
            speed = max(speed - 0.05, -1.0)
        elif keyboard.is_pressed('left'):
            turn = max(turn - 0.05, -0.5)  # FIXED: swapped direction
        elif keyboard.is_pressed('right'):
            turn = min(turn + 0.05, 0.5)   # FIXED: swapped direction
        elif keyboard.is_pressed('space'):
            speed = 0.0
            turn = 0.0
        
        # Apply velocity
        car.set_velocity_and_request_state(
            forward=speed, turn=turn,
            headlights=True,
            leftTurnSignal=False, rightTurnSignal=False,
            brakeSignal=(speed == 0), reverseSignal=(speed < 0)
        )
        
        # Get camera and detect lanes
        success, image = car.get_image(camera=car.CAMERA_CSI_FRONT)
        
        if success and image is not None:
            output = detect_lanes(image)
            cv2.putText(output, f"Speed:{speed:.1f} Turn:{turn:.1f}", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            cv2.imshow("Lane Detection", output)
        
        key = cv2.waitKey(30) & 0xFF
        if key == 27:  # ESC
            running = False
    
    car.set_velocity_and_request_state(0, 0, False, False, False, True, False)
    cv2.destroyAllWindows()
    print("\n🛑 Stopped!")
    qlabs.close()
    print("✅ Done!")


if __name__ == '__main__':
    main()
