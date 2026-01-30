"""
QCar 2 Autonomous Lane Following - ACC 2026
The car automatically steers to follow lane lines!

Uses: Lane detection + PID-style steering control
Run in CITYSCAPE workspace!
"""

import os
import time
import cv2
import numpy as np
import keyboard

from qvl.qlabs import QuanserInteractiveLabs
from qvl.qcar2 import QLabsQCar2


class LaneFollower:
    """Lane detection and following controller."""
    
    def __init__(self):
        self.steering_history = []
        self.last_valid_steering = 0.0
        
    def detect_lane_center(self, image):
        """
        Detect lanes and calculate steering correction.
        Returns: steering value (-0.5 to 0.5), annotated image
        """
        height, width = image.shape[:2]
        
        # Preprocess
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 50, 150)
        
        # Region of interest - lower portion of image
        roi_top = int(height * 0.5)
        roi_vertices = np.array([[
            (0, height),
            (width * 0.3, roi_top),
            (width * 0.7, roi_top),
            (width, height)
        ]], dtype=np.int32)
        
        mask = np.zeros_like(edges)
        cv2.fillPoly(mask, roi_vertices, 255)
        masked_edges = cv2.bitwise_and(edges, mask)
        
        # Detect lines
        lines = cv2.HoughLinesP(masked_edges, 1, np.pi/180, 40,
                                minLineLength=40, maxLineGap=100)
        
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
                
                if abs(slope) < 0.3:  # Skip horizontal lines
                    continue
                
                # Classify as left or right based on position and slope
                mid_x = (x1 + x2) / 2
                if slope < 0 and mid_x < width * 0.5:  # Left lane
                    left_lines.append((x1, y1, x2, y2, slope))
                    cv2.line(output, (x1, y1), (x2, y2), (255, 0, 0), 3)
                elif slope > 0 and mid_x > width * 0.5:  # Right lane
                    right_lines.append((x1, y1, x2, y2, slope))
                    cv2.line(output, (x1, y1), (x2, y2), (0, 0, 255), 3)
        
        # Calculate steering
        steering = 0.0
        lane_center = None
        
        if left_lines and right_lines:
            # Both lanes detected - calculate center
            left_x_bottom = self._extrapolate_line(left_lines, height)
            right_x_bottom = self._extrapolate_line(right_lines, height)
            
            lane_center = (left_x_bottom + right_x_bottom) / 2
            image_center = width / 2
            
            # Steering = proportional to offset from center
            offset = (lane_center - image_center) / (width / 2)
            steering = np.clip(offset * 0.5, -0.3, 0.3)
            
            # Draw lane center
            cv2.line(output, (int(lane_center), height),
                    (int(lane_center), int(height * 0.6)), (0, 255, 0), 4)
            cv2.line(output, (int(image_center), height),
                    (int(image_center), int(height * 0.8)), (255, 255, 0), 2)
            
        elif left_lines:
            # Only left lane - steer slightly right
            steering = 0.15
        elif right_lines:
            # Only right lane - steer slightly left
            steering = -0.15
        else:
            # No lanes - use last known steering
            steering = self.last_valid_steering * 0.8
        
        # Smooth steering with moving average
        self.steering_history.append(steering)
        if len(self.steering_history) > 5:
            self.steering_history.pop(0)
        smooth_steering = np.mean(self.steering_history)
        
        if abs(smooth_steering) > 0.05:
            self.last_valid_steering = smooth_steering
        
        # Display info
        status = "BOTH" if (left_lines and right_lines) else \
                 "LEFT ONLY" if left_lines else \
                 "RIGHT ONLY" if right_lines else "NO LANES"
        
        cv2.putText(output, f"Lanes: {status}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(output, f"Steer: {smooth_steering:.2f}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        return smooth_steering, output
    
    def _extrapolate_line(self, lines, target_y):
        """Extrapolate average line to target_y and return x position."""
        x_positions = []
        for x1, y1, x2, y2, slope in lines:
            # y = slope * x + b  =>  x = (y - b) / slope
            b = y1 - slope * x1
            if slope != 0:
                x_at_target = (target_y - b) / slope
                x_positions.append(x_at_target)
        return np.mean(x_positions) if x_positions else 0


def main():
    os.system('cls')
    print("="*60)
    print("  QCar 2 AUTONOMOUS Lane Following")
    print("="*60)
    
    qlabs = QuanserInteractiveLabs()
    print("\nConnecting to QLabs...")
    
    if not qlabs.open("localhost"):
        print("❌ Could not connect!")
        return
    
    print("✅ Connected!")
    
    qlabs.destroy_all_spawned_actors()
    time.sleep(0.5)
    
    # Spawn QCar on road
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
    
    follower = LaneFollower()
    
    print("\n" + "="*60)
    print("  🚗 MANUAL POSITIONING MODE")
    print("  Use arrow keys to drive to a road with lanes")
    print("  Press 'A' to start AUTONOMOUS mode")
    print("  ")
    print("  SPACE = Stop")
    print("  Q/ESC = Quit")
    print("="*60)
    
    cv2.namedWindow("Lane Following", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Lane Following", 800, 600)
    
    speed = 0.0
    turn = 0.0
    autonomous = False  # Start in manual mode
    
    running = True
    while running:
        # Handle controls
        if keyboard.is_pressed('q'):
            running = False
        elif keyboard.is_pressed('a') and not autonomous:
            autonomous = True
            speed = 0.5
            print("  🤖 AUTONOMOUS MODE ACTIVATED!")
        elif keyboard.is_pressed('space'):
            speed = 0.0
            turn = 0.0
            if autonomous:
                autonomous = False
                print("  ⚠️ MANUAL MODE (emergency stop)")
        
        if not autonomous:
            # Manual driving
            if keyboard.is_pressed('up'):
                speed = min(speed + 0.05, 1.5)
            elif keyboard.is_pressed('down'):
                speed = max(speed - 0.05, -0.5)
            if keyboard.is_pressed('left'):
                turn = max(turn - 0.05, -0.5)
            elif keyboard.is_pressed('right'):
                turn = min(turn + 0.05, 0.5)
        else:
            # Speed control in autonomous
            if keyboard.is_pressed('up'):
                speed = min(speed + 0.05, 1.5)
            elif keyboard.is_pressed('down'):
                speed = max(speed - 0.05, 0.2)
        
        # Get camera image
        success, image = car.get_image(camera=car.CAMERA_CSI_FRONT)
        
        if success and image is not None:
            # Detect lanes and get steering
            steering, output = follower.detect_lane_center(image)
            
            # Add mode indicator
            mode_text = "AUTONOMOUS" if autonomous else "MANUAL - Press A for auto"
            mode_color = (0, 255, 0) if autonomous else (0, 200, 255)
            cv2.putText(output, mode_text, (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, mode_color, 2)
            cv2.putText(output, f"Speed: {speed:.1f}", (10, 120),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 200, 0), 2)
            
            cv2.imshow("Lane Following", output)
            
            # Apply control
            if autonomous:
                car.set_velocity_and_request_state(
                    forward=speed,
                    turn=steering,
                    headlights=True,
                    leftTurnSignal=(steering < -0.1),
                    rightTurnSignal=(steering > 0.1),
                    brakeSignal=False,
                    reverseSignal=False
                )
            else:
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
        if key == 27:  # ESC
            running = False
    
    # Stop car
    car.set_velocity_and_request_state(0, 0, False, False, False, True, False)
    cv2.destroyAllWindows()
    print("\n🛑 Stopped!")
    qlabs.close()
    print("✅ Done!")


if __name__ == '__main__':
    main()
