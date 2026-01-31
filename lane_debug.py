"""
QCar 2 Lane Detection DEBUG - ACC 2026
Shows each stage of the pipeline to debug what's failing

Run in CITYSCAPE workspace!
"""

import os
import time
import cv2
import numpy as np
import keyboard

from qvl.qlabs import QuanserInteractiveLabs
from qvl.qcar2 import QLabsQCar2


class LaneDetectorDebug:
    """Debug version - shows all stages."""
    
    def __init__(self):
        # HSV thresholds - TUNABLE
        # White lanes
        self.white_low = np.array([0, 0, 180])
        self.white_high = np.array([180, 50, 255])
        
        # Yellow lanes  
        self.yellow_low = np.array([15, 50, 100])
        self.yellow_high = np.array([40, 255, 255])
        
        # Gray road detection (to find lane-like lines on gray road)
        self.gray_low = np.array([0, 0, 100])
        self.gray_high = np.array([180, 30, 200])
        
        self.left_fit = None
        self.right_fit = None
    
    def process(self, image):
        """
        Returns dictionary of debug images + steering value.
        """
        h, w = image.shape[:2]
        results = {}
        
        # Original
        results['original'] = image.copy()
        
        # Convert to HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # White mask
        white_mask = cv2.inRange(hsv, self.white_low, self.white_high)
        results['white'] = white_mask
        
        # Yellow mask
        yellow_mask = cv2.inRange(hsv, self.yellow_low, self.yellow_high)
        results['yellow'] = yellow_mask
        
        # Combined color
        color_mask = cv2.bitwise_or(white_mask, yellow_mask)
        results['color_combined'] = color_mask
        
        # Edge detection
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 30, 100)
        results['edges'] = edges
        
        # Combined: color OR edges
        combined = cv2.bitwise_or(color_mask, edges)
        results['combined'] = combined
        
        # Region of Interest
        roi_mask = np.zeros_like(combined)
        roi_vertices = np.array([[
            (0, h),
            (w * 0.35, h * 0.55),
            (w * 0.65, h * 0.55),
            (w, h)
        ]], dtype=np.int32)
        cv2.fillPoly(roi_mask, roi_vertices, 255)
        
        masked = cv2.bitwise_and(combined, roi_mask)
        results['masked'] = masked
        
        # Hough Lines (simpler than polynomial for debug)
        lines = cv2.HoughLinesP(masked, 1, np.pi/180, 30,
                                minLineLength=30, maxLineGap=100)
        
        # Draw on original
        output = image.copy()
        cv2.polylines(output, roi_vertices, True, (0, 255, 255), 2)
        
        left_lines = []
        right_lines = []
        
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                if x2 - x1 == 0:
                    continue
                slope = (y2 - y1) / (x2 - x1)
                
                if abs(slope) < 0.3:
                    continue
                
                mid_x = (x1 + x2) / 2
                if slope < 0 and mid_x < w * 0.5:
                    left_lines.append((x1, y1, x2, y2))
                    cv2.line(output, (x1, y1), (x2, y2), (255, 0, 0), 2)
                elif slope > 0 and mid_x > w * 0.5:
                    right_lines.append((x1, y1, x2, y2))
                    cv2.line(output, (x1, y1), (x2, y2), (0, 0, 255), 2)
        
        # Calculate steering
        steering = 0.0
        status = "NO LANES"
        
        if left_lines and right_lines:
            left_x = np.mean([x1 for x1, y1, x2, y2 in left_lines])
            right_x = np.mean([x1 for x1, y1, x2, y2 in right_lines])
            center = (left_x + right_x) / 2
            offset = (center - w / 2) / (w / 2)
            steering = np.clip(offset * 0.4, -0.3, 0.3)
            status = f"BOTH ({len(left_lines)}L/{len(right_lines)}R)"
        elif left_lines:
            steering = 0.1
            status = f"LEFT ONLY ({len(left_lines)})"
        elif right_lines:
            steering = -0.1
            status = f"RIGHT ONLY ({len(right_lines)})"
        
        cv2.putText(output, status, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(output, f"Steer: {steering:.2f}", (10, 55),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        results['output'] = output
        
        return results, steering, status


def create_debug_grid(results, scale=0.5):
    """Arrange debug images in a grid."""
    # Convert grayscale to color
    def to_color(img):
        if len(img.shape) == 2:
            return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        return img
    
    # Resize
    def resize(img):
        return cv2.resize(to_color(img), None, fx=scale, fy=scale)
    
    # Create labeled images
    def label(img, text):
        img = resize(img)
        cv2.putText(img, text, (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        return img
    
    row1 = np.hstack([
        label(results['original'], "Original"),
        label(results['white'], "White Mask"),
        label(results['yellow'], "Yellow Mask"),
    ])
    
    row2 = np.hstack([
        label(results['edges'], "Edges"),
        label(results['combined'], "Color+Edges"),
        label(results['masked'], "ROI Masked"),
    ])
    
    output = label(results['output'], "Result")
    output_full = cv2.resize(to_color(results['output']), 
                             (row1.shape[1], int(row1.shape[1] * results['output'].shape[0] / results['output'].shape[1])))
    
    grid = np.vstack([row1, row2])
    
    return grid, output_full


def main():
    os.system('cls')
    print("="*60)
    print("  QCar 2 Lane Detection DEBUG")
    print("  See each processing stage!")
    print("="*60)
    
    qlabs = QuanserInteractiveLabs()
    print("\nConnecting to QLabs...")
    
    if not qlabs.open("localhost"):
        print("❌ Could not connect!")
        return
    
    print("✅ Connected!")
    
    qlabs.destroy_all_spawned_actors()
    time.sleep(0.5)
    
    print("Spawning QCar...")
    car = QLabsQCar2(qlabs)
    car.spawn_id_degrees(
        actorNumber=0,
        location=[-8.7, 14.643, 0.005],
        rotation=[0, 0, 90],
        scale=[1, 1, 1],
        configuration=0,
        waitForConfirmation=True
    )
    
    detector = LaneDetectorDebug()
    
    print("\n" + "="*60)
    print("  CONTROLS:")
    print("  Arrow keys = Drive")
    print("  A = Autonomous")
    print("  1/2 = Adjust white threshold")
    print("  3/4 = Adjust canny threshold")
    print("  Q = Quit")
    print("="*60)
    
    cv2.namedWindow("Debug Grid", cv2.WINDOW_NORMAL)
    cv2.namedWindow("Result", cv2.WINDOW_NORMAL)
    
    speed = 0.0
    turn = 0.0
    autonomous = False
    
    running = True
    while running:
        if keyboard.is_pressed('q'):
            running = False
        elif keyboard.is_pressed('a'):
            autonomous = not autonomous
            if autonomous:
                speed = 0.4
            print(f"  {'🤖 AUTO' if autonomous else '🎮 MANUAL'}")
            time.sleep(0.2)
        
        # Threshold adjustments
        if keyboard.is_pressed('1'):
            detector.white_low[2] = max(0, detector.white_low[2] - 10)
            print(f"  White low V: {detector.white_low[2]}")
            time.sleep(0.1)
        if keyboard.is_pressed('2'):
            detector.white_low[2] = min(255, detector.white_low[2] + 10)
            print(f"  White low V: {detector.white_low[2]}")
            time.sleep(0.1)
        
        if not autonomous:
            if keyboard.is_pressed('up'):
                speed = min(speed + 0.05, 1.5)
            elif keyboard.is_pressed('down'):
                speed = max(speed - 0.05, -0.5)
            if keyboard.is_pressed('left'):
                turn = max(turn - 0.05, -0.5)
            elif keyboard.is_pressed('right'):
                turn = min(turn + 0.05, 0.5)
            elif keyboard.is_pressed('space'):
                speed = 0.0
                turn = 0.0
        
        # Get camera
        success, image = car.get_image(camera=car.CAMERA_CSI_FRONT)
        
        if success and image is not None:
            results, steering, status = detector.process(image)
            
            if autonomous:
                turn = steering
            
            # Create debug display
            grid, output = create_debug_grid(results)
            
            cv2.putText(output, f"Mode: {'AUTO' if autonomous else 'MANUAL'}", 
                       (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, 
                       (0, 255, 0) if autonomous else (0, 200, 255), 2)
            cv2.putText(output, f"Speed: {speed:.1f}", 
                       (10, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 0), 2)
            
            cv2.imshow("Debug Grid", grid)
            cv2.imshow("Result", output)
            
            # Drive
            car.set_velocity_and_request_state(
                forward=speed,
                turn=turn,
                headlights=True,
                leftTurnSignal=False,
                rightTurnSignal=False,
                brakeSignal=(speed == 0),
                reverseSignal=(speed < 0)
            )
        
        key = cv2.waitKey(30) & 0xFF
        if key == 27:
            running = False
    
    car.set_velocity_and_request_state(0, 0, False, False, False, True, False)
    cv2.destroyAllWindows()
    print("\n🛑 Stopped!")
    qlabs.close()
    print("✅ Done!")


if __name__ == '__main__':
    main()
