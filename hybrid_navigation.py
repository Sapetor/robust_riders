"""
QCar 2 Hybrid Navigation - ACC 2026
Combines Waypoint Navigation + Lane Following

Two modes:
1. WAYPOINT: Drive toward target coordinates (when no lanes)
2. LANE: Follow detected lanes (when on road with markings)

Run in CITYSCAPE workspace!
"""

import os
import time
import cv2
import numpy as np
import keyboard
import math

from qvl.qlabs import QuanserInteractiveLabs
from qvl.qcar2 import QLabsQCar2


class LaneDetector:
    """Edge-based lane detection (tuned for QLabs based on debug)."""
    
    def __init__(self):
        self.lane_confidence = 0.0
        self.steering_history = []
    
    def detect(self, image):
        """
        Detect lanes using improved edge detection.
        Returns: steering, confidence (0-1), annotated image
        """
        h, w = image.shape[:2]
        
        # Better preprocessing
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Enhance contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Blur and edge detect with lower thresholds (more sensitive)
        blur = cv2.GaussianBlur(enhanced, (5, 5), 0)
        edges = cv2.Canny(blur, 20, 80)  # Lower thresholds
        
        # Wider ROI to catch more lanes
        roi_mask = np.zeros_like(edges)
        roi_vertices = np.array([[
            (int(w * 0.05), h),
            (int(w * 0.30), int(h * 0.50)),
            (int(w * 0.70), int(h * 0.50)),
            (int(w * 0.95), h)
        ]], dtype=np.int32)
        cv2.fillPoly(roi_mask, roi_vertices, 255)
        masked = cv2.bitwise_and(edges, roi_mask)
        
        # More sensitive Hough parameters
        lines = cv2.HoughLinesP(masked, 1, np.pi/180, 20,
                                minLineLength=20, maxLineGap=150)
        
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
                
                # More lenient slope filter
                if abs(slope) < 0.2:
                    continue
                
                mid_x = (x1 + x2) / 2
                if slope < 0 and mid_x < w * 0.55:
                    left_lines.append((x1, y1, x2, y2))
                    cv2.line(output, (x1, y1), (x2, y2), (255, 0, 0), 3)
                elif slope > 0 and mid_x > w * 0.45:
                    right_lines.append((x1, y1, x2, y2))
                    cv2.line(output, (x1, y1), (x2, y2), (0, 0, 255), 3)
        
        # Calculate steering and confidence
        steering = 0.0
        confidence = 0.0
        
        total_lines = len(left_lines) + len(right_lines)
        
        if left_lines and right_lines:
            # Use bottom points for steering calculation
            left_x = np.mean([max(x1, x2) for x1, y1, x2, y2 in left_lines])
            right_x = np.mean([min(x1, x2) for x1, y1, x2, y2 in right_lines])
            center = (left_x + right_x) / 2
            offset = (center - w / 2) / (w / 2)
            steering = np.clip(offset * 0.5, -0.35, 0.35)
            confidence = min(1.0, total_lines / 6.0)
            
            # Draw center guide
            cv2.line(output, (int(center), h), (int(center), int(h * 0.7)), (0, 255, 0), 3)
        elif left_lines:
            steering = 0.15  # Steer right if only left lane visible
            confidence = min(0.6, len(left_lines) / 4.0)
        elif right_lines:
            steering = -0.15  # Steer left if only right lane visible
            confidence = min(0.6, len(right_lines) / 4.0)
        
        # Smooth steering
        self.steering_history.append(steering)
        if len(self.steering_history) > 5:
            self.steering_history.pop(0)
        smooth_steering = np.mean(self.steering_history)
        
        # Smooth confidence
        self.lane_confidence = 0.6 * self.lane_confidence + 0.4 * confidence
        
        return smooth_steering, self.lane_confidence, output


class WaypointNavigator:
    """Navigate toward target coordinates."""
    
    def __init__(self):
        self.current_pos = [0, 0]
        self.current_heading = 0  # radians
        self.target = None
    
    def set_target(self, x, y):
        """Set target waypoint."""
        self.target = [x, y]
    
    def update_position(self, x, y, z, heading):
        """Update current position from QCar state."""
        self.current_pos = [x, y]
        self.current_heading = heading
    
    def calculate_steering(self):
        """
        Calculate steering to reach target.
        Returns: steering, distance_to_target
        """
        if self.target is None:
            return 0.0, float('inf')
        
        # Vector to target
        dx = self.target[0] - self.current_pos[0]
        dy = self.target[1] - self.current_pos[1]
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < 0.5:  # Close enough
            return 0.0, distance
        
        # Angle to target
        target_angle = math.atan2(dy, dx)
        
        # Heading error
        error = target_angle - self.current_heading
        
        # Normalize to [-pi, pi]
        while error > math.pi:
            error -= 2 * math.pi
        while error < -math.pi:
            error += 2 * math.pi
        
        # Proportional steering
        steering = np.clip(error * 0.5, -0.4, 0.4)
        
        return steering, distance


class HybridNavigator:
    """Combines lane following and waypoint navigation."""
    
    def __init__(self):
        self.lane_detector = LaneDetector()
        self.waypoint_nav = WaypointNavigator()
        self.mode = "WAYPOINT"  # or "LANE"
        self.lane_threshold = 0.3  # Switch to lane mode above this
        
        # Competition waypoints
        self.waypoints = [
            {"name": "Taxi Hub", "pos": [-1.205, -0.83]},
            {"name": "Pickup", "pos": [0.125, 4.395]},
            {"name": "Dropoff", "pos": [-0.905, 0.800]},
        ]
        self.current_waypoint_idx = 0
    
    def next_waypoint(self):
        """Move to next waypoint in sequence."""
        self.current_waypoint_idx = (self.current_waypoint_idx + 1) % len(self.waypoints)
        wp = self.waypoints[self.current_waypoint_idx]
        self.waypoint_nav.set_target(wp["pos"][0], wp["pos"][1])
        return wp["name"]
    
    def process(self, image, car_state):
        """
        Process frame and return steering.
        car_state: dict with x, y, z, heading
        """
        # Update position
        self.waypoint_nav.update_position(
            car_state.get('x', 0),
            car_state.get('y', 0),
            car_state.get('z', 0),
            car_state.get('heading', 0)
        )
        
        # Detect lanes
        lane_steering, lane_confidence, annotated = self.lane_detector.detect(image)
        
        # Decide mode
        if lane_confidence > self.lane_threshold:
            self.mode = "LANE"
            steering = lane_steering
        else:
            self.mode = "WAYPOINT"
            steering, distance = self.waypoint_nav.calculate_steering()
        
        # Annotate
        cv2.putText(annotated, f"Mode: {self.mode}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, 
                   (0, 255, 0) if self.mode == "LANE" else (0, 200, 255), 2)
        cv2.putText(annotated, f"Lane conf: {lane_confidence:.2f}", (10, 55),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        cv2.putText(annotated, f"Steer: {steering:.2f}", (10, 80),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 0), 2)
        
        if self.waypoint_nav.target:
            wp = self.waypoints[self.current_waypoint_idx]
            _, dist = self.waypoint_nav.calculate_steering()
            cv2.putText(annotated, f"Target: {wp['name']} ({dist:.1f}m)", (10, 105),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 255), 2)
        
        return steering, annotated


def main():
    os.system('cls')
    print("="*60)
    print("  QCar 2 HYBRID Navigation")
    print("  Waypoint + Lane Following")
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
    
    navigator = HybridNavigator()
    navigator.next_waypoint()  # Set first target
    
    print("\n" + "="*60)
    print("  CONTROLS:")
    print("  Arrow keys = Manual override")
    print("  A = Toggle autonomous")
    print("  N = Next waypoint")
    print("  Q = Quit")
    print("="*60)
    
    cv2.namedWindow("Hybrid Navigation", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Hybrid Navigation", 800, 600)
    
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
                speed = 0.5
            else:
                speed = 0.0
            print(f"  {'🤖 AUTO' if autonomous else '🎮 MANUAL'}")
            time.sleep(0.2)
        elif keyboard.is_pressed('n'):
            wp_name = navigator.next_waypoint()
            print(f"  📍 Target: {wp_name}")
            time.sleep(0.2)
        
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
        
        # Get camera and state
        success, image = car.get_image(camera=car.CAMERA_CSI_FRONT)
        
        # Get car state (position/heading)
        # Note: In QLabs, we need to track this ourselves or use spawn position
        car_state = {
            'x': 0, 'y': 0, 'z': 0, 'heading': 0  # Would come from IMU/odometry
        }
        
        if success and image is not None:
            steering, annotated = navigator.process(image, car_state)
            
            if autonomous:
                turn = steering
            
            # Add mode overlay
            cv2.putText(annotated, f"{'AUTO' if autonomous else 'MANUAL'}", 
                       (annotated.shape[1] - 100, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, 
                       (0, 255, 0) if autonomous else (0, 200, 255), 2)
            cv2.putText(annotated, f"Speed: {speed:.1f}", 
                       (annotated.shape[1] - 120, 55),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 0), 2)
            
            cv2.imshow("Hybrid Navigation", annotated)
            
            car.set_velocity_and_request_state(
                forward=speed,
                turn=turn,
                headlights=True,
                leftTurnSignal=(turn < -0.1),
                rightTurnSignal=(turn > 0.1),
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
