"""Lane detection using Hough lines with curvature estimation."""

import cv2
import numpy as np
from typing import Tuple


class LaneDetector:
    """
    Lane detection using Hough lines with curvature estimation.

    Uses edge detection + Hough transform to find lane lines,
    calculates curvature to predict curves, and adjusts speed accordingly.
    """

    def __init__(self, img_width: int = 820, img_height: int = 410):
        self.img_width = img_width
        self.img_height = img_height
        self.lane_confidence = 0.0
        self.steering_history = []

        # Debug mode
        self.debug_mode = False

        # Store detected lines for visualization
        self.left_lines = []
        self.right_lines = []
        self.center_x = None

        # Curvature estimation
        self.curvature = 0.0  # 0 = straight, higher = sharper curve
        self.curvature_history = []

        # PID steering controller
        self.pid_integral = 0.0
        self.pid_last_error = 0.0
        self.pid_kp = 0.8   # Proportional gain
        self.pid_ki = 0.05  # Integral gain
        self.pid_kd = 0.3   # Derivative gain

    def detect(self, image: np.ndarray) -> Tuple[float, float, np.ndarray]:
        """
        Detect lanes using Hough lines.
        Returns: steering, confidence (0-1), annotated image
        """
        h, w = image.shape[:2]
        self.img_width = w
        self.img_height = h

        output = image.copy()

        # Step 1: Define ROI - bottom 45% of image, center 70% width
        roi_top = int(h * 0.55)
        roi_left = int(w * 0.15)
        roi_right = int(w * 0.85)

        # ROI rectangle (only show in debug mode)
        if self.debug_mode:
            roi_pts = np.array([
                [roi_left, h],
                [roi_left, roi_top],
                [roi_right, roi_top],
                [roi_right, h]
            ], np.int32)
            cv2.polylines(output, [roi_pts], True, (0, 255, 255), 2)

        # Step 2: Extract and process ROI
        roi = image[roi_top:h, roi_left:roi_right]

        # Convert to grayscale and detect edges
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 50, 150)

        # Step 3: Detect lines using Hough transform
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180,
            threshold=30,
            minLineLength=20,
            maxLineGap=100
        )

        # Step 4: Separate left and right lines based on slope
        left_lines = []
        right_lines = []
        roi_center = (roi_right - roi_left) // 2

        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]

                # Skip near-horizontal lines
                if abs(y2 - y1) < 10:
                    continue

                slope = (y2 - y1) / (x2 - x1 + 0.001)

                # Left lane: negative slope (going up-left), on left side
                # Right lane: positive slope (going up-right), on right side
                mid_x = (x1 + x2) / 2

                if slope < -0.3 and mid_x < roi_center:
                    left_lines.append((x1 + roi_left, y1 + roi_top,
                                       x2 + roi_left, y2 + roi_top))
                elif slope > 0.3 and mid_x > roi_center:
                    right_lines.append((x1 + roi_left, y1 + roi_top,
                                        x2 + roi_left, y2 + roi_top))

        self.left_lines = left_lines
        self.right_lines = right_lines

        # Step 5: Calculate average lane positions and steering with curvature
        steering, confidence, status = self._calculate_steering_from_lines(
            left_lines, right_lines, w, h, roi_top
        )

        # Smooth steering
        self.steering_history.append(steering)
        if len(self.steering_history) > 5:
            self.steering_history.pop(0)
        smooth_steering = np.mean(self.steering_history)

        # Smooth confidence
        self.lane_confidence = 0.7 * self.lane_confidence + 0.3 * confidence

        # Draw detected lines
        for x1, y1, x2, y2 in left_lines:
            cv2.line(output, (x1, y1), (x2, y2), (255, 0, 0), 2)  # Blue for left

        for x1, y1, x2, y2 in right_lines:
            cv2.line(output, (x1, y1), (x2, y2), (0, 0, 255), 2)  # Red for right

        # Draw steering target as arrow at bottom of screen
        if self.center_x is not None:
            # Small triangle/arrow pointing up at target position
            arrow_y = h - 20
            arrow_size = 15
            pts = np.array([
                [int(self.center_x), arrow_y - arrow_size],
                [int(self.center_x) - arrow_size//2, arrow_y],
                [int(self.center_x) + arrow_size//2, arrow_y]
            ], np.int32)
            cv2.fillPoly(output, [pts], (0, 255, 0))
            # Small dot at image center for reference
            cv2.circle(output, (w // 2, arrow_y), 4, (255, 255, 0), -1)

        # Debug visualization
        if self.debug_mode:
            self._show_debug_windows(edges, roi_left, roi_top)

        return smooth_steering, self.lane_confidence, output

    def _calculate_steering_from_lines(self, left_lines: list, right_lines: list,
                                        w: int, h: int, roi_top: int) -> Tuple[float, float, str]:
        """Calculate steering from detected Hough lines with curvature estimation."""

        left_x_bottom = None
        right_x_bottom = None
        left_x_top = None
        right_x_top = None
        left_slope_avg = 0
        right_slope_avg = 0

        # Get lane positions at BOTH bottom and top of ROI for curvature
        if left_lines:
            left_x_bottom_vals = []
            left_x_top_vals = []
            left_slopes = []
            for x1, y1, x2, y2 in left_lines:
                if y2 != y1:
                    slope = (x2 - x1) / (y2 - y1)
                    left_slopes.append(slope)
                    x_at_bottom = x1 + slope * (h - y1)
                    x_at_top = x1 + slope * (roi_top - y1)
                    left_x_bottom_vals.append(x_at_bottom)
                    left_x_top_vals.append(x_at_top)
            if left_x_bottom_vals:
                left_x_bottom = np.mean(left_x_bottom_vals)
                left_x_top = np.mean(left_x_top_vals)
                left_slope_avg = np.mean(left_slopes)

        if right_lines:
            right_x_bottom_vals = []
            right_x_top_vals = []
            right_slopes = []
            for x1, y1, x2, y2 in right_lines:
                if y2 != y1:
                    slope = (x2 - x1) / (y2 - y1)
                    right_slopes.append(slope)
                    x_at_bottom = x1 + slope * (h - y1)
                    x_at_top = x1 + slope * (roi_top - y1)
                    right_x_bottom_vals.append(x_at_bottom)
                    right_x_top_vals.append(x_at_top)
            if right_x_bottom_vals:
                right_x_bottom = np.mean(right_x_bottom_vals)
                right_x_top = np.mean(right_x_top_vals)
                right_slope_avg = np.mean(right_slopes)

        # Calculate curvature from lane convergence/divergence
        # Higher curvature = lanes converging more (sharper turn ahead)
        self._estimate_curvature(left_x_bottom, left_x_top, right_x_bottom, right_x_top,
                                  left_slope_avg, right_slope_avg, w)

        # Calculate steering based on detected lanes
        # PRIORITY: Right edge is critical - it's the road boundary
        image_center = w / 2

        # Safety margin from right edge (in pixels)
        right_margin = w * 0.25  # Stay at least 25% of image width from right edge

        if left_x_bottom is not None and right_x_bottom is not None:
            # Both lanes detected - bias toward left (away from right edge)
            # Weight the center calculation to stay away from right edge
            lane_center = (left_x_bottom * 0.4 + right_x_bottom * 0.6) / 1.0
            # Apply safety margin - shift target left
            target_x = lane_center - right_margin * 0.3
            self.center_x = target_x
            error = (target_x - image_center) / (w / 2)
            steering = self._pid_steering(error)
            confidence = min(1.0, (len(left_lines) + len(right_lines)) / 6.0)
            return steering, confidence, "BOTH"

        elif right_x_bottom is not None:
            # RIGHT EDGE ONLY - Stay at safe distance from edge
            # Target position: fixed offset from right edge (stay in lane)
            safe_distance = w * 0.30  # Stay 30% of image width from right edge
            self.center_x = right_x_bottom - safe_distance

            # Always use PID for smooth steering (no urgency override)
            error = (self.center_x - image_center) / (w / 2)
            steering = self._pid_steering(error)

            confidence = min(0.8, len(right_lines) / 3.0)
            return steering, confidence, "RIGHT EDGE"

        elif left_x_bottom is not None:
            # Only left/center line - less critical but useful
            self.center_x = left_x_bottom + w * 0.25
            error = (self.center_x - image_center) / (w / 2)
            steering = self._pid_steering(error)
            confidence = min(0.5, len(left_lines) / 3.0)
            return steering, confidence, "LEFT ONLY"

        else:
            # No lanes detected - reset PID
            self.center_x = None
            self.pid_integral = 0.0
            return 0.0, 0.0, "NO LANES"

    def _estimate_curvature(self, left_bottom, left_top, right_bottom, right_top,
                            left_slope, right_slope, w):
        """Estimate road curvature from lane geometry."""
        curvature = 0.0

        if left_bottom is not None and right_bottom is not None:
            # Method 1: Lane width change (convergence = curve)
            width_bottom = right_bottom - left_bottom
            if left_top is not None and right_top is not None:
                width_top = right_top - left_top
                if width_bottom > 0:
                    width_ratio = width_top / width_bottom
                    # Ratio < 1 means lanes converge = curve ahead
                    curvature = abs(1.0 - width_ratio) * 2.0

            # Method 2: Slope difference indicates curve direction
            slope_diff = abs(left_slope - right_slope)
            curvature = max(curvature, slope_diff * 0.5)

        elif left_bottom is not None:
            # Single lane - use slope to estimate curvature
            curvature = abs(left_slope) * 0.3

        elif right_bottom is not None:
            curvature = abs(right_slope) * 0.3

        # Smooth curvature over time
        self.curvature_history.append(curvature)
        if len(self.curvature_history) > 10:
            self.curvature_history.pop(0)
        self.curvature = np.mean(self.curvature_history)

    def _pid_steering(self, error: float) -> float:
        """PID controller for smooth steering."""
        # Proportional
        p_term = self.pid_kp * error

        # Integral (with anti-windup)
        self.pid_integral += error
        self.pid_integral = np.clip(self.pid_integral, -2.0, 2.0)
        i_term = self.pid_ki * self.pid_integral

        # Derivative
        d_term = self.pid_kd * (error - self.pid_last_error)
        self.pid_last_error = error

        # Combined output
        steering = p_term + i_term + d_term
        return np.clip(steering, -0.5, 0.5)

    def get_recommended_speed(self, base_speed: float = 0.5) -> float:
        """Get recommended speed based on curvature."""
        # Reduce speed on curves: higher curvature = slower
        # curvature 0 = full speed, curvature 1+ = minimum speed
        speed_factor = max(0.3, 1.0 - self.curvature * 0.7)
        return base_speed * speed_factor

    def _show_debug_windows(self, edges: np.ndarray, roi_left: int, roi_top: int):
        """Show debug visualization windows."""
        # Window 1: Edge detection result
        edges_color = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        cv2.putText(edges_color, "Canny Edges (ROI)", (10, 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.imshow("Debug: Edges", cv2.resize(edges_color, (400, 300)))

        # Window 2: Detected lines visualization
        h, w = edges.shape
        lines_viz = np.zeros((h, w, 3), dtype=np.uint8)

        for x1, y1, x2, y2 in self.left_lines:
            cv2.line(lines_viz, (x1 - roi_left, y1 - roi_top),
                    (x2 - roi_left, y2 - roi_top), (255, 0, 0), 2)

        for x1, y1, x2, y2 in self.right_lines:
            cv2.line(lines_viz, (x1 - roi_left, y1 - roi_top),
                    (x2 - roi_left, y2 - roi_top), (0, 0, 255), 2)

        cv2.putText(lines_viz, f"Hough Lines L:{len(self.left_lines)} R:{len(self.right_lines)}",
                   (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.imshow("Debug: Lines", cv2.resize(lines_viz, (400, 300)))

    def toggle_debug(self):
        """Toggle debug mode on/off."""
        self.debug_mode = not self.debug_mode
        if not self.debug_mode:
            cv2.destroyWindow("Debug: Edges")
            cv2.destroyWindow("Debug: Lines")
        return self.debug_mode
