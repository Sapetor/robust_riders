"""Traffic light detection using HSV color detection."""

import cv2
import numpy as np
from enum import Enum, auto
from typing import Tuple


class TrafficLightState(Enum):
    """Detected traffic light state."""
    NONE = auto()
    RED = auto()
    YELLOW = auto()
    GREEN = auto()


class TrafficLightDetector:
    """Detect traffic light state using HSV color detection."""

    def __init__(self):
        # HSV ranges for traffic light colors
        # Red (wraps around 0, so two ranges)
        self.red_low1 = np.array([0, 100, 100])
        self.red_high1 = np.array([10, 255, 255])
        self.red_low2 = np.array([160, 100, 100])
        self.red_high2 = np.array([180, 255, 255])

        # Yellow
        self.yellow_low = np.array([15, 100, 100])
        self.yellow_high = np.array([35, 255, 255])

        # Green
        self.green_low = np.array([40, 100, 100])
        self.green_high = np.array([80, 255, 255])

        self.min_area = 50  # Minimum contour area for detection
        self.last_state = TrafficLightState.NONE
        self.state_history = []

    def detect(self, image: np.ndarray) -> Tuple[TrafficLightState, float, np.ndarray]:
        """
        Detect traffic light state.
        Returns: (state, confidence, annotated_image)

        Traffic lights are:
        - Small circular lights (not large signs)
        - Usually at top of frame, on poles
        - Have specific size range (not too big like stop signs)
        """
        h, w = image.shape[:2]

        output = image.copy()

        # Look only in upper-center region where traffic lights appear
        # Exclude sides where signs typically are
        roi_top = int(h * 0.1)
        roi_bottom = int(h * 0.45)
        roi_left = int(w * 0.25)
        roi_right = int(w * 0.75)

        roi = image[roi_top:roi_bottom, roi_left:roi_right]

        if roi.size == 0:
            return TrafficLightState.NONE, 0.0, output

        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        # Draw ROI for debugging (light blue rectangle)
        cv2.rectangle(output, (roi_left, roi_top), (roi_right, roi_bottom), (255, 255, 0), 1)

        # Detect each color with stricter size requirements
        detections = []

        # Red detection (two ranges) - traffic light red is bright
        red_mask1 = cv2.inRange(hsv, self.red_low1, self.red_high1)
        red_mask2 = cv2.inRange(hsv, self.red_low2, self.red_high2)
        red_mask = cv2.bitwise_or(red_mask1, red_mask2)
        red_area = self._find_traffic_light_circles(red_mask, output, (0, 0, 255), "TL-RED", roi_left, roi_top)
        if red_area > 0:
            detections.append((TrafficLightState.RED, red_area, 1.0))

        # Yellow detection
        yellow_mask = cv2.inRange(hsv, self.yellow_low, self.yellow_high)
        yellow_area = self._find_traffic_light_circles(yellow_mask, output, (0, 255, 255), "TL-YEL", roi_left, roi_top)
        if yellow_area > 0:
            detections.append((TrafficLightState.YELLOW, yellow_area, 0.8))

        # Green detection
        green_mask = cv2.inRange(hsv, self.green_low, self.green_high)
        green_area = self._find_traffic_light_circles(green_mask, output, (0, 255, 0), "TL-GRN", roi_left, roi_top)
        if green_area > 0:
            detections.append((TrafficLightState.GREEN, green_area, 0.6))

        # Priority: RED > YELLOW > GREEN
        if detections:
            detections.sort(key=lambda x: x[2], reverse=True)
            state = detections[0][0]
            confidence = min(1.0, detections[0][1] / 300.0)
        else:
            state = TrafficLightState.NONE
            confidence = 0.0

        # Smooth state (require 5 consecutive frames for more stability)
        self.state_history.append(state)
        if len(self.state_history) > 5:
            self.state_history.pop(0)

        if len(self.state_history) >= 5 and all(s == state for s in self.state_history[-5:]):
            self.last_state = state
        else:
            state = self.last_state

        return state, confidence, output

    def _find_circles(self, mask: np.ndarray, output: np.ndarray,
                      color: Tuple[int, int, int], label: str, y_offset: int) -> float:
        """Find circular contours in mask and annotate."""
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        total_area = 0

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.min_area:
                continue

            # Check circularity
            perimeter = cv2.arcLength(contour, True)
            if perimeter == 0:
                continue
            circularity = 4 * np.pi * area / (perimeter * perimeter)

            if circularity > 0.5:  # Reasonably circular
                total_area += area
                (x, y), radius = cv2.minEnclosingCircle(contour)
                cv2.circle(output, (int(x), int(y + y_offset)), int(radius), color, 2)
                cv2.putText(output, label, (int(x - 20), int(y + y_offset - radius - 5)),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        return total_area

    def _find_traffic_light_circles(self, mask: np.ndarray, output: np.ndarray,
                                     color: Tuple[int, int, int], label: str,
                                     x_offset: int, y_offset: int) -> float:
        """
        Find traffic light circles with strict size requirements.
        Traffic lights are SMALL circles, not big signs.
        """
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        total_area = 0

        for contour in contours:
            area = cv2.contourArea(contour)

            # Traffic lights should be small (20-500 pixels)
            # Stop signs are much larger (500+ pixels)
            if area < 20 or area > 400:
                continue

            # Check circularity - traffic lights are very circular
            perimeter = cv2.arcLength(contour, True)
            if perimeter == 0:
                continue
            circularity = 4 * np.pi * area / (perimeter * perimeter)

            # Require high circularity for traffic lights
            if circularity > 0.7:
                total_area += area
                (x, y), radius = cv2.minEnclosingCircle(contour)

                # Draw at correct position (add offset for ROI)
                draw_x = int(x + x_offset)
                draw_y = int(y + y_offset)
                cv2.circle(output, (draw_x, draw_y), int(radius), color, 2)
                cv2.putText(output, label, (draw_x - 20, draw_y - int(radius) - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

        return total_area
