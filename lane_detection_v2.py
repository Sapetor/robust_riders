"""
QCar 2 Improved Lane Detection - ACC 2026
Uses recommended approach: HSV filtering + Perspective Transform + Polynomial Fit

Run in CITYSCAPE workspace!
"""

import os
import time
import cv2
import numpy as np
import keyboard

from qvl.qlabs import QuanserInteractiveLabs
from qvl.qcar2 import QLabsQCar2


class ImprovedLaneDetector:
    """
    Improved lane detection using:
    1. HSV color filtering for white/yellow lanes
    2. Bird's eye view perspective transform
    3. Sliding window for lane pixel detection
    4. Polynomial fitting for smooth lanes
    """
    
    def __init__(self, img_width=640, img_height=480):
        self.img_width = img_width
        self.img_height = img_height
        
        # Perspective transform points
        # Source points (camera view) - trapezoid on road
        self.src_points = np.float32([
            [img_width * 0.1, img_height],      # Bottom left
            [img_width * 0.4, img_height * 0.6], # Top left
            [img_width * 0.6, img_height * 0.6], # Top right
            [img_width * 0.9, img_height],       # Bottom right
        ])
        
        # Destination points (bird's eye view) - rectangle
        self.dst_points = np.float32([
            [img_width * 0.2, img_height],       # Bottom left
            [img_width * 0.2, 0],                # Top left
            [img_width * 0.8, 0],                # Top right
            [img_width * 0.8, img_height],       # Bottom right
        ])
        
        # Compute perspective transform matrices
        self.M = cv2.getPerspectiveTransform(self.src_points, self.dst_points)
        self.M_inv = cv2.getPerspectiveTransform(self.dst_points, self.src_points)
        
        # Lane tracking
        self.left_fit = None
        self.right_fit = None
        self.left_fit_history = []
        self.right_fit_history = []
        
    def color_threshold(self, image):
        """Apply HSV color thresholding for white and yellow lanes."""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # White lane detection (high value, low saturation)
        white_low = np.array([0, 0, 200])
        white_high = np.array([180, 30, 255])
        white_mask = cv2.inRange(hsv, white_low, white_high)
        
        # Yellow lane detection
        yellow_low = np.array([15, 80, 100])
        yellow_high = np.array([35, 255, 255])
        yellow_mask = cv2.inRange(hsv, yellow_low, yellow_high)
        
        # Combine masks
        combined = cv2.bitwise_or(white_mask, yellow_mask)
        
        # Also apply edge detection for robustness
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 50, 150)
        
        # Combine color and edges
        result = cv2.bitwise_or(combined, edges)
        
        return result
    
    def warp_perspective(self, image):
        """Transform to bird's eye view."""
        return cv2.warpPerspective(image, self.M, 
                                   (self.img_width, self.img_height))
    
    def unwarp_perspective(self, image):
        """Transform back to camera view."""
        return cv2.warpPerspective(image, self.M_inv,
                                   (self.img_width, self.img_height))
    
    def sliding_window_fit(self, binary_warped):
        """
        Use sliding window to find lane pixels and fit polynomial.
        Returns left and right polynomial coefficients.
        """
        # Histogram of bottom half
        histogram = np.sum(binary_warped[binary_warped.shape[0]//2:, :], axis=0)
        
        # Find left and right peaks
        midpoint = len(histogram) // 2
        left_base = np.argmax(histogram[:midpoint])
        right_base = np.argmax(histogram[midpoint:]) + midpoint
        
        # Sliding window parameters
        n_windows = 9
        window_height = binary_warped.shape[0] // n_windows
        margin = 80
        min_pixels = 40
        
        # Find nonzero pixels
        nonzero = binary_warped.nonzero()
        nonzero_y = np.array(nonzero[0])
        nonzero_x = np.array(nonzero[1])
        
        # Current positions
        left_current = left_base
        right_current = right_base
        
        # Lists for lane pixel indices
        left_lane_inds = []
        right_lane_inds = []
        
        # Step through windows
        for window in range(n_windows):
            # Window boundaries
            win_y_low = binary_warped.shape[0] - (window + 1) * window_height
            win_y_high = binary_warped.shape[0] - window * window_height
            
            win_xleft_low = left_current - margin
            win_xleft_high = left_current + margin
            win_xright_low = right_current - margin
            win_xright_high = right_current + margin
            
            # Find pixels in window
            good_left_inds = ((nonzero_y >= win_y_low) & (nonzero_y < win_y_high) &
                             (nonzero_x >= win_xleft_low) & (nonzero_x < win_xleft_high)).nonzero()[0]
            good_right_inds = ((nonzero_y >= win_y_low) & (nonzero_y < win_y_high) &
                              (nonzero_x >= win_xright_low) & (nonzero_x < win_xright_high)).nonzero()[0]
            
            left_lane_inds.append(good_left_inds)
            right_lane_inds.append(good_right_inds)
            
            # Recenter if enough pixels found
            if len(good_left_inds) > min_pixels:
                left_current = int(np.mean(nonzero_x[good_left_inds]))
            if len(good_right_inds) > min_pixels:
                right_current = int(np.mean(nonzero_x[good_right_inds]))
        
        # Concatenate indices
        left_lane_inds = np.concatenate(left_lane_inds) if left_lane_inds else np.array([])
        right_lane_inds = np.concatenate(right_lane_inds) if right_lane_inds else np.array([])
        
        # Extract pixel positions
        left_fit = None
        right_fit = None
        
        if len(left_lane_inds) > 100:
            leftx = nonzero_x[left_lane_inds]
            lefty = nonzero_y[left_lane_inds]
            left_fit = np.polyfit(lefty, leftx, 2)
        
        if len(right_lane_inds) > 100:
            rightx = nonzero_x[right_lane_inds]
            righty = nonzero_y[right_lane_inds]
            right_fit = np.polyfit(righty, rightx, 2)
        
        return left_fit, right_fit, left_lane_inds, right_lane_inds, nonzero_x, nonzero_y
    
    def calculate_steering(self, left_fit, right_fit, img_height):
        """Calculate steering based on lane position."""
        if left_fit is None and right_fit is None:
            return 0.0, "NO LANES"
        
        # Generate y values
        y_eval = img_height - 1  # Bottom of image
        
        if left_fit is not None and right_fit is not None:
            # Both lanes detected
            left_x = left_fit[0] * y_eval**2 + left_fit[1] * y_eval + left_fit[2]
            right_x = right_fit[0] * y_eval**2 + right_fit[1] * y_eval + right_fit[2]
            lane_center = (left_x + right_x) / 2
            image_center = self.img_width / 2
            offset = (lane_center - image_center) / (self.img_width / 2)
            steering = np.clip(offset * 0.5, -0.4, 0.4)
            return steering, "BOTH LANES"
        elif left_fit is not None:
            # Only left lane - steer right
            return 0.1, "LEFT ONLY"
        else:
            # Only right lane - steer left
            return -0.1, "RIGHT ONLY"
    
    def process(self, image):
        """
        Full pipeline: color filter -> warp -> detect -> fit -> draw
        Returns: annotated image, bird's eye view, steering value
        """
        h, w = image.shape[:2]
        self.img_height = h
        self.img_width = w
        
        # Recalculate transform if size changed
        self.src_points = np.float32([
            [w * 0.1, h], [w * 0.4, h * 0.6],
            [w * 0.6, h * 0.6], [w * 0.9, h]
        ])
        self.dst_points = np.float32([
            [w * 0.2, h], [w * 0.2, 0],
            [w * 0.8, 0], [w * 0.8, h]
        ])
        self.M = cv2.getPerspectiveTransform(self.src_points, self.dst_points)
        self.M_inv = cv2.getPerspectiveTransform(self.dst_points, self.src_points)
        
        # Step 1: Color threshold
        binary = self.color_threshold(image)
        
        # Step 2: Perspective transform
        binary_warped = self.warp_perspective(binary)
        
        # Step 3: Find lanes
        left_fit, right_fit, left_inds, right_inds, nonzero_x, nonzero_y = \
            self.sliding_window_fit(binary_warped)
        
        # Step 4: Calculate steering
        steering, status = self.calculate_steering(left_fit, right_fit, h)
        
        # Step 5: Draw visualization
        output = image.copy()
        
        # Draw ROI
        roi_pts = self.src_points.astype(int)
        cv2.polylines(output, [roi_pts], True, (0, 255, 255), 2)
        
        # Draw detected lanes on warped image
        warped_color = cv2.cvtColor(binary_warped, cv2.COLOR_GRAY2BGR)
        if len(left_inds) > 0:
            warped_color[nonzero_y[left_inds], nonzero_x[left_inds]] = [255, 0, 0]
        if len(right_inds) > 0:
            warped_color[nonzero_y[right_inds], nonzero_x[right_inds]] = [0, 0, 255]
        
        # Draw fitted polynomials
        if left_fit is not None or right_fit is not None:
            plot_y = np.linspace(0, h - 1, h)
            
            if left_fit is not None:
                left_x = left_fit[0] * plot_y**2 + left_fit[1] * plot_y + left_fit[2]
                pts_left = np.array([np.column_stack((left_x, plot_y))], dtype=np.int32)
                cv2.polylines(warped_color, pts_left, False, (255, 255, 0), 3)
            
            if right_fit is not None:
                right_x = right_fit[0] * plot_y**2 + right_fit[1] * plot_y + right_fit[2]
                pts_right = np.array([np.column_stack((right_x, plot_y))], dtype=np.int32)
                cv2.polylines(warped_color, pts_right, False, (0, 255, 255), 3)
        
        # Text overlay
        cv2.putText(output, f"Status: {status}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(output, f"Steer: {steering:.2f}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        return output, warped_color, steering, status


def main():
    os.system('cls')
    print("="*60)
    print("  QCar 2 IMPROVED Lane Detection")
    print("  (HSV + Perspective Transform + Polynomial Fit)")
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
        location=[-8.7, 14.643, 0.005],
        rotation=[0, 0, 90],
        scale=[1, 1, 1],
        configuration=0,
        waitForConfirmation=True
    )
    
    detector = ImprovedLaneDetector()
    
    print("\n" + "="*60)
    print("  CONTROLS:")
    print("  Arrow keys = Manual drive")
    print("  A = Toggle AUTONOMOUS mode")
    print("  B = Toggle bird's eye view")
    print("  Q = Quit")
    print("="*60)
    
    cv2.namedWindow("Lane Detection", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Lane Detection", 1200, 500)
    
    speed = 0.0
    turn = 0.0
    autonomous = False
    show_birdseye = True
    
    running = True
    while running:
        # Controls
        if keyboard.is_pressed('q'):
            running = False
        elif keyboard.is_pressed('a'):
            autonomous = not autonomous
            if autonomous:
                speed = 0.5
            print(f"  {'🤖 AUTONOMOUS' if autonomous else '🎮 MANUAL'}")
            time.sleep(0.2)
        elif keyboard.is_pressed('b'):
            show_birdseye = not show_birdseye
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
        else:
            if keyboard.is_pressed('up'):
                speed = min(speed + 0.05, 1.5)
            elif keyboard.is_pressed('down'):
                speed = max(speed - 0.05, 0.2)
        
        # Get camera
        success, image = car.get_image(camera=car.CAMERA_CSI_FRONT)
        
        if success and image is not None:
            # Process
            output, birdseye, steering, status = detector.process(image)
            
            if autonomous:
                turn = steering
            
            # Mode indicator
            mode = "AUTO" if autonomous else "MANUAL"
            cv2.putText(output, f"Mode: {mode}", (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                       (0, 255, 0) if autonomous else (0, 200, 255), 2)
            cv2.putText(output, f"Speed: {speed:.1f}", (10, 120),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 200, 0), 2)
            
            # Display
            if show_birdseye:
                # Resize birdseye to match height
                birdseye_resized = cv2.resize(birdseye, (output.shape[1], output.shape[0]))
                combined = np.hstack([output, birdseye_resized])
                cv2.imshow("Lane Detection", combined)
            else:
                cv2.imshow("Lane Detection", output)
            
            # Apply control
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
