"""
QCar 2 Hybrid Navigation - ACC 2026
Combines Waypoint Navigation + Lane Following

Two modes:
1. WAYPOINT: Drive toward target coordinates (when no lanes)
2. LANE: Follow detected lanes (when on road with markings)

Features:
- State machine for taxi operations (LED colors, wait times)
- Hysteresis-based mode switching (prevents flickering)
- Smooth speed control (gradual acceleration/deceleration)
- HSV + perspective transform lane detection
- Multi-camera support (side awareness)
- Traffic light/stop sign detection

*** Run in OPEN WORLD workspace (not Cityscape) ***
"""

import os
import time
import cv2
import numpy as np
import keyboard
import math
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, List

from qvl.qlabs import QuanserInteractiveLabs
from qvl.qcar2 import QLabsQCar2
from qvl.free_camera import QLabsFreeCamera
from qvl.walls import QLabsWalls
from qvl.qcar_flooring import QLabsQCarFlooring
from qvl.crosswalk import QLabsCrosswalk
from qvl.basic_shape import QLabsBasicShape
from qvl.stop_sign import QLabsStopSign
from qvl.yield_sign import QLabsYieldSign
from qvl.roundabout_sign import QLabsRoundaboutSign
from qvl.traffic_light import QLabsTrafficLight
from qvl.animal import QLabsAnimal

# Road feature detection (Phase 3)
from road_features import NavigationAdvisor, RoadType


# =============================================================================
# ENUMS AND CONSTANTS
# =============================================================================

# Toggle cow spawning (disabled by default to reduce visual clutter)
SPAWN_COWS = False

class TaxiState(Enum):
    """Taxi operation states with corresponding LED colors."""
    WAITING_AT_HUB = auto()      # Magenta - waiting for ride
    EN_ROUTE_TO_PICKUP = auto()  # Green - driving to pickup
    AT_PICKUP = auto()           # Blue - stopped at pickup
    EN_ROUTE_TO_DROPOFF = auto() # Green - driving with passenger
    AT_DROPOFF = auto()          # Orange - stopped at dropoff
    RETURNING_TO_HUB = auto()    # Green - returning
    STOPPED = auto()             # Red - stopped at sign/light


class NavigationMode(Enum):
    """Navigation mode for driving."""
    WAYPOINT = auto()  # Follow waypoints
    LANE = auto()      # Follow lane markings


class TrafficLightState(Enum):
    """Detected traffic light state."""
    NONE = auto()
    RED = auto()
    YELLOW = auto()
    GREEN = auto()


# LED colors (RGB normalized 0-1)
LED_COLORS = {
    TaxiState.WAITING_AT_HUB: [1.0, 0.0, 1.0],      # Magenta
    TaxiState.EN_ROUTE_TO_PICKUP: [0.0, 1.0, 0.0],  # Green
    TaxiState.AT_PICKUP: [0.0, 0.0, 1.0],           # Blue
    TaxiState.EN_ROUTE_TO_DROPOFF: [0.0, 1.0, 0.0], # Green
    TaxiState.AT_DROPOFF: [1.0, 0.5, 0.0],          # Orange
    TaxiState.RETURNING_TO_HUB: [0.0, 1.0, 0.0],    # Green
    TaxiState.STOPPED: [1.0, 0.0, 0.0],             # Red
}

# Path waypoints for road curves (intermediate points to follow road layout)
# Each path is a list of [x, y] coordinates to follow sequentially
PATHS = {
    'hub_to_pickup': [
        [-1.205, -0.83],   # Hub start
        [-1.0, 0.5],       # Curve point 1
        [-0.5, 2.0],       # Curve point 2
        [0.0, 3.5],        # Approach to pickup
        [0.125, 4.395],    # Pickup location
    ],
    'pickup_to_dropoff': [
        [0.125, 4.395],    # Pickup start
        [0.5, 3.0],        # Curve point 1
        [0.0, 1.5],        # Curve point 2
        [-0.5, 1.0],       # Approach to dropoff
        [-0.905, 0.800],   # Dropoff location
    ],
    'dropoff_to_hub': [
        [-0.905, 0.800],   # Dropoff start
        [-1.0, 0.0],       # Curve point
        [-1.205, -0.83],   # Hub location
    ],
}


# =============================================================================
# SPEED CONTROLLER
# =============================================================================

class SpeedController:
    """Smooth speed control with acceleration/deceleration ramps."""

    def __init__(self, max_speed: float = 0.35, min_speed: float = 0.0,
                 accel_rate: float = 0.15, decel_rate: float = 0.25):
        self.max_speed = max_speed
        self.min_speed = min_speed
        self.accel_rate = accel_rate  # units per second
        self.decel_rate = decel_rate
        self.current_speed = 0.0
        self.target_speed = 0.0
        self.last_update = time.time()

    def set_target(self, target: float):
        """Set target speed."""
        self.target_speed = np.clip(target, self.min_speed, self.max_speed)

    def update(self) -> float:
        """Update and return current speed."""
        now = time.time()
        dt = now - self.last_update
        self.last_update = now

        if self.current_speed < self.target_speed:
            # Accelerating
            self.current_speed = min(
                self.current_speed + self.accel_rate * dt,
                self.target_speed
            )
        elif self.current_speed > self.target_speed:
            # Decelerating
            self.current_speed = max(
                self.current_speed - self.decel_rate * dt,
                self.target_speed
            )

        return self.current_speed

    def stop(self):
        """Immediate stop."""
        self.target_speed = 0.0
        self.current_speed = 0.0

    def slow_approach(self, distance: float, slow_distance: float = 0.5):
        """Reduce speed when approaching target."""
        if distance < slow_distance:
            factor = distance / slow_distance
            self.target_speed = max(0.15, self.max_speed * factor)


# =============================================================================
# SAFETY MONITOR
# =============================================================================

class SafetyMonitor:
    """Monitor for stuck detection - checks total movement over time window."""

    def __init__(self, stuck_threshold: float = 5.0, min_total_movement: float = 0.1):
        self.stuck_threshold = stuck_threshold  # seconds to check
        self.min_total_movement = min_total_movement  # min meters over that period
        self.position_history = []  # list of (time, x, y)
        self.is_stuck = False

    def update(self, x: float, y: float) -> bool:
        """Check if car is stuck. Returns True if stuck."""
        now = time.time()

        # Add current position to history
        self.position_history.append((now, x, y))

        # Remove old entries (older than stuck_threshold)
        cutoff = now - self.stuck_threshold
        self.position_history = [(t, px, py) for t, px, py in self.position_history if t > cutoff]

        # Need at least 2 points and enough time elapsed
        if len(self.position_history) < 2:
            self.is_stuck = False
            return False

        oldest = self.position_history[0]
        time_elapsed = now - oldest[0]

        if time_elapsed < self.stuck_threshold * 0.8:  # Wait for ~80% of threshold
            self.is_stuck = False
            return False

        # Calculate total distance from oldest to newest position
        total_distance = np.sqrt((x - oldest[1])**2 + (y - oldest[2])**2)

        self.is_stuck = total_distance < self.min_total_movement
        return self.is_stuck

    def reset(self):
        """Reset stuck detection."""
        self.position_history = []
        self.is_stuck = False


# =============================================================================
# MULTI-CAMERA MANAGER
# =============================================================================

class MultiCameraManager:
    """Manage multiple cameras with caching."""

    def __init__(self, car, cache_ttl: float = 0.05):
        self.car = car
        self.cache_ttl = cache_ttl  # 50ms cache
        self.cache = {}
        self.cache_times = {}

    def _safe_get_image(self, camera_id: int) -> Tuple[bool, Optional[np.ndarray]]:
        """Safely get image from camera, handling errors."""
        try:
            success, img = self.car.get_image(camera=camera_id)
            return success, img
        except cv2.error:
            return False, None

    def get_camera(self, name: str, size: Tuple[int, int] = (200, 150)) -> np.ndarray:
        """Get camera image with caching."""
        camera_map = {
            'front': self.car.CAMERA_CSI_FRONT,
            'right': self.car.CAMERA_CSI_RIGHT,
            'back': self.car.CAMERA_CSI_BACK,
            'left': self.car.CAMERA_CSI_LEFT,
        }

        if name not in camera_map:
            return np.zeros((size[1], size[0], 3), dtype=np.uint8)

        now = time.time()
        cache_key = f"{name}_{size[0]}x{size[1]}"

        # Check cache
        if cache_key in self.cache:
            if now - self.cache_times[cache_key] < self.cache_ttl:
                return self.cache[cache_key]

        # Fetch new image
        success, img = self._safe_get_image(camera_map[name])
        if success and img is not None:
            img = cv2.resize(img, size)
        else:
            img = np.zeros((size[1], size[0], 3), dtype=np.uint8)

        # Add label
        cv2.putText(img, name.upper(), (5, 15),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

        # Cache
        self.cache[cache_key] = img
        self.cache_times[cache_key] = now

        return img

    def get_surround_cameras(self, size: Tuple[int, int] = (200, 150)) -> Dict[str, np.ndarray]:
        """Get all 4 CSI cameras."""
        return {
            'front': self.get_camera('front', size),
            'right': self.get_camera('right', size),
            'back': self.get_camera('back', size),
            'left': self.get_camera('left', size),
        }

    def create_surround_strip(self, size: Tuple[int, int] = (200, 150)) -> np.ndarray:
        """Create horizontal strip: [LEFT][BACK][RIGHT]."""
        cameras = self.get_surround_cameras(size)
        return np.hstack([cameras['left'], cameras['back'], cameras['right']])

    def check_side_obstacles(self, threshold: float = 0.3) -> Dict[str, bool]:
        """Check for obstacles in side cameras using dark pixel ratio."""
        result = {'left': False, 'right': False}

        for side in ['left', 'right']:
            img = self.get_camera(side, (100, 75))
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            dark_ratio = np.sum(gray < 50) / gray.size
            result[side] = dark_ratio > threshold

        return result


# Legacy functions for backward compatibility
def get_surround_cameras(car, size=(200, 150)):
    """Get all 4 CSI cameras for surround view."""
    cameras = {}

    for name, cam_id in [('front', car.CAMERA_CSI_FRONT),
                         ('right', car.CAMERA_CSI_RIGHT),
                         ('back', car.CAMERA_CSI_BACK),
                         ('left', car.CAMERA_CSI_LEFT)]:
        try:
            success, img = car.get_image(camera=cam_id)
            if success and img is not None:
                img = cv2.resize(img, size)
            else:
                img = np.zeros((size[1], size[0], 3), dtype=np.uint8)
        except cv2.error:
            img = np.zeros((size[1], size[0], 3), dtype=np.uint8)
        # Add label
        cv2.putText(img, name.upper(), (5, 15),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
        cameras[name] = img

    return cameras


def create_surround_strip(cameras):
    """Create horizontal strip: [LEFT][BACK][RIGHT] for bottom of display."""
    return np.hstack([cameras['left'], cameras['back'], cameras['right']])


def setup_environment(qlabs):
    """Spawn the competition environment (Walls, Floors, Signs)."""
    print("  🏗️ Spawning Taxi Hub Environment (Floors, Walls, Signs)...")
    
    # Offsets from base scenario
    x_offset = 0.13
    y_offset = 1.67
    
    # Flooring (the competition mat - no scale, it's already correct size)
    hFloor = QLabsQCarFlooring(qlabs)
    hFloor.spawn_degrees([x_offset, y_offset, 0.001], rotation=[0, 0, -90])

    # Walls (boundaries - no scale needed)
    hWall = QLabsWalls(qlabs)
    hWall.set_enable_dynamics(False)

    # Wall loops
    for y in range(5):
        hWall.spawn_degrees(location=[-2.4 + x_offset, (-y*1.0)+2.55 + y_offset, 0.001], rotation=[0, 0, 0])
    for x in range(5):
        hWall.spawn_degrees(location=[-1.9+x + x_offset, 3.05+ y_offset, 0.001], rotation=[0, 0, 90])
    for y in range(6):
        hWall.spawn_degrees(location=[2.4+ x_offset, (-y*1.0)+2.55 + y_offset, 0.001], rotation=[0, 0, 0])
    for x in range(4):
        hWall.spawn_degrees(location=[-0.9+x+ x_offset, -3.05+ y_offset, 0.001], rotation=[0, 0, 90])

    # Angled walls
    hWall.spawn_degrees(location=[-2.03 + x_offset, -2.275+ y_offset, 0.001], rotation=[0, 0, 48])
    hWall.spawn_degrees(location=[-1.575+ x_offset, -2.7+ y_offset, 0.001], rotation=[0, 0, 48])

    # Crosswalk
    myCrossWalk = QLabsCrosswalk(qlabs)
    myCrossWalk.spawn_degrees(location=[-2 + x_offset, -1.475 + y_offset, 0.01],
                             rotation=[0,0,0], scale=[0.1,0.1,0.075], configuration=0)

    # --- SIGNS (from Setup_Real_Scenario.py) ---
    print("  🛑 Spawning Signs & Lights...")
    
    # Yield Sign (The one near start)
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
    
    # Traffic Lights (Spawn only, no cycling logic to avoid blocking)
    tl = QLabsTrafficLight(qlabs)
    tl.spawn_id_degrees(actorNumber=1, location=[0.6, 1.55, 0.006], rotation=[0,0,0], scale=[0.1, 0.1, 0.1], configuration=0, waitForConfirmation=False)
    tl.spawn_id_degrees(actorNumber=2, location=[-0.6, 1.28, 0.006], rotation=[0,0,90], scale=[0.1, 0.1, 0.1], configuration=0, waitForConfirmation=False)
    tl.spawn_id_degrees(actorNumber=3, location=[-0.37, 0.3, 0.006], rotation=[0,0,180], scale=[0.1, 0.1, 0.1], configuration=0, waitForConfirmation=False)
    tl.spawn_id_degrees(actorNumber=4, location=[0.75, 0.48, 0.006], rotation=[0,0,-90], scale=[0.1, 0.1, 0.1], configuration=0, waitForConfirmation=False)

    # --- COWS! ---
    if SPAWN_COWS:
        print("  🐄 Spawning Cows...")
        cow = QLabsAnimal(qlabs)
        # Spawn a few cows near the road (configuration 0 = cow)
        cow.spawn_degrees(location=[1.5, 2.5, 0.01], rotation=[0, 0, 45], scale=[0.1, 0.1, 0.1], configuration=0, waitForConfirmation=False)
        cow.spawn_degrees(location=[1.8, 2.2, 0.01], rotation=[0, 0, -30], scale=[0.1, 0.1, 0.1], configuration=0, waitForConfirmation=False)
        cow.spawn_degrees(location=[-1.8, 3.0, 0.01], rotation=[0, 0, 120], scale=[0.1, 0.1, 0.1], configuration=0, waitForConfirmation=False)

    print("  ✅ Environment & Signs Spawned")
    
    # Spawn Birds Eye Camera to verify setup
    print("  📷 Spawning Overhead Camera...")
    camera_loc = [0.15, 1.7, 5]   # From official setup
    camera_rot = [0, 90, 0]       # Looking down
    cam = QLabsFreeCamera(qlabs)
    cam.spawn_degrees(location=camera_loc, rotation=camera_rot)
    # Start with overhead view for better visualization
    cam.possess()
    
    return cam


# =============================================================================
# TRAFFIC LIGHT DETECTOR
# =============================================================================

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


# =============================================================================
# SIGN DETECTOR
# =============================================================================

class SignDetector:
    """Detect stop signs using color and shape."""

    def __init__(self):
        # Red color range for stop signs
        self.red_low1 = np.array([0, 100, 100])
        self.red_high1 = np.array([10, 255, 255])
        self.red_low2 = np.array([160, 100, 100])
        self.red_high2 = np.array([180, 255, 255])

        self.min_area = 200
        self.last_detection_time = 0
        self.stop_duration = 2.0  # seconds to stop at sign

    def detect_stop_sign(self, image: np.ndarray) -> Tuple[bool, float, np.ndarray]:
        """
        Detect stop sign.
        Returns: (detected, distance_estimate, annotated_image)
        """
        h, w = image.shape[:2]
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        output = image.copy()

        # Red mask
        red_mask1 = cv2.inRange(hsv, self.red_low1, self.red_high1)
        red_mask2 = cv2.inRange(hsv, self.red_low2, self.red_high2)
        red_mask = cv2.bitwise_or(red_mask1, red_mask2)

        contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.min_area:
                continue

            # Approximate polygon
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            # Stop signs are octagonal (8 sides)
            if 6 <= len(approx) <= 10:
                x, y, box_w, box_h = cv2.boundingRect(contour)

                # Aspect ratio check (should be roughly square)
                aspect = box_w / box_h if box_h > 0 else 0
                if 0.7 < aspect < 1.3:
                    # Estimate distance from apparent size
                    # Larger area = closer
                    distance = max(0.2, 500.0 / area)

                    cv2.drawContours(output, [approx], -1, (0, 0, 255), 3)
                    cv2.putText(output, f"STOP {distance:.1f}m",
                               (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                               0.6, (0, 0, 255), 2)

                    return True, distance, output

        return False, float('inf'), output

    def should_stop(self, detected: bool, distance: float) -> bool:
        """Determine if car should stop for sign."""
        if detected and distance < 0.5:
            now = time.time()
            if now - self.last_detection_time > self.stop_duration + 1.0:
                self.last_detection_time = now
                return True
        return False


# =============================================================================
# IMPROVED LANE DETECTOR
# =============================================================================

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


# =============================================================================
# WAYPOINT NAVIGATOR
# =============================================================================

class WaypointNavigator:
    """Navigate toward target coordinates with PID steering control and path following."""

    def __init__(self):
        self.current_pos = np.array([0.0, 0.0])
        self.current_heading = 0.0  # radians
        self.target = None
        self.position_history = []  # For arrival stability check

        # Path following (list of waypoints)
        self.path = []  # List of [x, y] waypoints
        self.path_index = 0  # Current waypoint in path
        self.waypoint_threshold = 0.3  # Distance to consider waypoint reached

        # PID steering controller for smooth waypoint approach
        self.pid_integral = 0.0
        self.pid_last_error = 0.0
        self.pid_kp = 0.6   # Proportional gain (lower than lane for smoother turns)
        self.pid_ki = 0.02  # Integral gain
        self.pid_kd = 0.2   # Derivative gain

    def set_target(self, target_pos: List[float]):
        """Set single target waypoint [x, y]."""
        self.target = np.array(target_pos)
        self.position_history = []
        self.path = []
        self.path_index = 0
        self.reset_pid()

    def set_path(self, path: List[List[float]]):
        """Set a path of waypoints to follow sequentially."""
        self.path = [np.array(p) for p in path]
        self.path_index = 0
        self.position_history = []
        self.reset_pid()
        # Set first waypoint as target
        if self.path:
            self.target = self.path[0]

    def advance_waypoint(self) -> bool:
        """
        Advance to next waypoint in path if close enough to current.
        Returns True if advanced, False if at end or no path.
        """
        if not self.path or self.path_index >= len(self.path) - 1:
            return False

        # Check distance to current waypoint
        if self.target is not None:
            dist = np.linalg.norm(self.current_pos - self.target)
            if dist < self.waypoint_threshold:
                self.path_index += 1
                self.target = self.path[self.path_index]
                self.reset_pid()
                return True
        return False

    def is_final_waypoint(self) -> bool:
        """Check if current target is the final waypoint in path."""
        if not self.path:
            return True
        return self.path_index >= len(self.path) - 1

    def get_path_progress(self) -> Tuple[int, int]:
        """Get current progress through path (current_index, total)."""
        if not self.path:
            return 0, 0
        return self.path_index, len(self.path)

    def update_position(self, x: float, y: float, z: float, heading: float):
        """Update current position from QCar state."""
        self.current_pos = np.array([x, y])
        self.current_heading = heading

        # Track position for stability check
        self.position_history.append(self.current_pos.copy())
        if len(self.position_history) > 10:
            self.position_history.pop(0)

    def calculate_steering(self) -> Tuple[float, float]:
        """
        Calculate steering to reach target using PID control.
        Returns: steering, distance_to_target
        """
        if self.target is None:
            return 0.0, float('inf')

        # Vector to target
        delta = self.target - self.current_pos
        distance = np.linalg.norm(delta)

        if distance < 0.25:  # Close enough (tightened from 0.5)
            # Reset PID when at target
            self.pid_integral = 0.0
            self.pid_last_error = 0.0
            return 0.0, distance

        # Angle to target
        target_angle = math.atan2(delta[1], delta[0])

        # Heading error (normalized to [-pi, pi])
        error = target_angle - self.current_heading
        while error > math.pi:
            error -= 2 * math.pi
        while error < -math.pi:
            error += 2 * math.pi

        # Normalize error to [-1, 1] range for PID
        normalized_error = error / math.pi

        # PID control
        # Proportional term
        p_term = self.pid_kp * normalized_error

        # Integral term (with anti-windup)
        self.pid_integral += normalized_error
        self.pid_integral = np.clip(self.pid_integral, -2.0, 2.0)
        i_term = self.pid_ki * self.pid_integral

        # Derivative term
        d_term = self.pid_kd * (normalized_error - self.pid_last_error)
        self.pid_last_error = normalized_error

        # Combined PID output
        steering = p_term + i_term + d_term

        # Distance-based gain adjustment (tighter control when close)
        if distance < 0.5:
            steering *= 1.2  # Slightly more aggressive when close

        return np.clip(steering, -0.5, 0.5), distance

    def reset_pid(self):
        """Reset PID controller state."""
        self.pid_integral = 0.0
        self.pid_last_error = 0.0

    def check_heading_alignment(self, target_heading: float = None, tolerance: float = 0.3) -> bool:
        """Check if heading is aligned with target direction."""
        if self.target is None:
            return True

        delta = self.target - self.current_pos
        target_angle = math.atan2(delta[1], delta[0])

        error = abs(target_angle - self.current_heading)
        error = min(error, 2 * math.pi - error)  # Handle wraparound

        return error < tolerance

    def check_stable_position(self, threshold: float = 0.05, frames: int = 5) -> bool:
        """Check if position has been stable for N frames."""
        if len(self.position_history) < frames:
            return False

        recent = self.position_history[-frames:]
        for i in range(1, len(recent)):
            if np.linalg.norm(recent[i] - recent[i-1]) > threshold:
                return False
        return True


# =============================================================================
# HYBRID NAVIGATOR
# =============================================================================

class HybridNavigator:
    """
    Combines lane following and waypoint navigation with:
    - State machine for taxi operations
    - Hysteresis-based mode switching
    - Traffic light/sign detection
    """

    def __init__(self):
        self.lane_detector = LaneDetector()
        self.waypoint_nav = WaypointNavigator()
        self.traffic_light_detector = TrafficLightDetector()
        self.sign_detector = SignDetector()

        # Road feature detection (Phase 3) - for speed adjustment
        # DISABLED by default - classical CV not reliable enough
        # Press 'R' to enable if you want to test it
        self.road_advisor = NavigationAdvisor()
        self.road_feature_enabled = False  # Toggle with 'R' key
        self.current_road_type = RoadType.STRAIGHT
        self.road_speed_multiplier = 1.0

        # Navigation mode with hysteresis
        # Lowered thresholds for QLabs 0.1 scale (less visible lanes)
        self.mode = NavigationMode.WAYPOINT
        self.lane_enter_threshold = 0.25  # Enter LANE mode when confidence > this
        self.lane_exit_threshold = 0.10   # Exit LANE mode when confidence < this
        self.min_mode_duration = 1.0      # Minimum seconds in mode before switching
        self.mode_switch_time = 0.0

        # Arrival detection (tightened)
        self.arrival_threshold = 0.25  # meters to consider "arrived"
        self.arrival_stable_frames = 5  # frames to confirm arrival

        # Competition waypoints with state mappings and paths
        self.waypoints = [
            {
                "name": "Pickup",
                "pos": [0.125, 4.395],
                "path": PATHS['hub_to_pickup'],
                "state": TaxiState.EN_ROUTE_TO_PICKUP,
                "arrival_state": TaxiState.AT_PICKUP
            },
            {
                "name": "Dropoff",
                "pos": [-0.905, 0.800],
                "path": PATHS['pickup_to_dropoff'],
                "state": TaxiState.EN_ROUTE_TO_DROPOFF,
                "arrival_state": TaxiState.AT_DROPOFF
            },
            {
                "name": "Taxi Hub",
                "pos": [-1.205, -0.83],
                "path": PATHS['dropoff_to_hub'],
                "state": TaxiState.RETURNING_TO_HUB,
                "arrival_state": TaxiState.WAITING_AT_HUB
            },
        ]
        self.current_waypoint_idx = 0

        # Traffic detection results
        self.traffic_light_state = TrafficLightState.NONE
        self.stop_sign_detected = False
        self.stop_sign_distance = float('inf')

        # Flag to enable/disable traffic detection (and its visualization)
        self.traffic_detection_enabled = False

    def check_arrival(self, distance: float) -> bool:
        """Check if we've arrived at the FINAL waypoint with stability."""
        # Only check arrival for final waypoint in path
        if not self.waypoint_nav.is_final_waypoint():
            return False

        if distance >= self.arrival_threshold:
            return False

        # Also check stable position
        return self.waypoint_nav.check_stable_position(
            threshold=0.03, frames=self.arrival_stable_frames
        )

    def next_waypoint(self) -> dict:
        """Move to next waypoint and return it."""
        self.current_waypoint_idx = (self.current_waypoint_idx + 1) % len(self.waypoints)
        wp = self.waypoints[self.current_waypoint_idx]
        # Use path if available, otherwise single target
        if "path" in wp and wp["path"]:
            self.waypoint_nav.set_path(wp["path"])
        else:
            self.waypoint_nav.set_target(wp["pos"])
        return wp

    def get_current_waypoint(self) -> dict:
        """Get current waypoint info."""
        return self.waypoints[self.current_waypoint_idx]

    def _update_mode(self, lane_confidence: float):
        """Update navigation mode with hysteresis to prevent flickering."""
        now = time.time()
        time_in_mode = now - self.mode_switch_time

        # Don't switch if not enough time has passed
        if time_in_mode < self.min_mode_duration:
            return

        if self.mode == NavigationMode.WAYPOINT:
            # Switch to LANE if confidence high enough
            if lane_confidence > self.lane_enter_threshold:
                self.mode = NavigationMode.LANE
                self.mode_switch_time = now
        else:
            # Switch to WAYPOINT if confidence drops too low
            if lane_confidence < self.lane_exit_threshold:
                self.mode = NavigationMode.WAYPOINT
                self.mode_switch_time = now

    def process(self, image: np.ndarray, car_state: dict) -> Tuple[float, np.ndarray, dict]:
        """
        Process frame and return steering, annotated image, and detection info.
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

        # Road feature detection (Phase 3) - for speed adjustment
        if self.road_feature_enabled:
            # Get edges from lane detector's preprocessing
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blur, 50, 150)

            # Update road feature detection
            feature = self.road_advisor.update(edges, image)
            self.current_road_type = feature.road_type
            self.road_speed_multiplier = feature.recommended_speed

        # Detect traffic lights and signs (only if enabled)
        if self.traffic_detection_enabled:
            self.traffic_light_state, tl_confidence, annotated = self.traffic_light_detector.detect(annotated)
            self.stop_sign_detected, self.stop_sign_distance, annotated = self.sign_detector.detect_stop_sign(annotated)
        else:
            self.traffic_light_state = TrafficLightState.NONE
            self.stop_sign_detected = False
            self.stop_sign_distance = float('inf')

        # Update navigation mode with hysteresis
        self._update_mode(lane_confidence)

        # Auto-advance through intermediate waypoints in path
        self.waypoint_nav.advance_waypoint()

        # Calculate steering based on mode
        if self.mode == NavigationMode.LANE:
            steering = lane_steering
        else:
            steering, _ = self.waypoint_nav.calculate_steering()

        # LEFT SIDE - Navigation info (spaced at 25px intervals)
        h, w = annotated.shape[:2]
        y = 25  # Starting Y position

        mode_color = (0, 255, 0) if self.mode == NavigationMode.LANE else (0, 200, 255)
        cv2.putText(annotated, f"Mode: {self.mode.name}", (10, y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, mode_color, 2)

        y += 25
        cv2.putText(annotated, f"Lane: {lane_confidence:.0%}", (10, y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

        y += 25
        cv2.putText(annotated, f"Steer: {steering:+.2f}", (10, y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 200, 0), 1)

        # Waypoint info
        if self.waypoint_nav.target is not None:
            wp = self.get_current_waypoint()
            _, dist = self.waypoint_nav.calculate_steering()
            path_idx, path_total = self.waypoint_nav.get_path_progress()
            y += 25
            if path_total > 0:
                cv2.putText(annotated, f"To: {wp['name']} [{path_idx+1}/{path_total}] {dist:.1f}m", (10, y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 255), 1)
            else:
                cv2.putText(annotated, f"To: {wp['name']} {dist:.1f}m", (10, y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 255), 1)

        # Detection info for main loop
        detection_info = {
            'lane_confidence': lane_confidence,
            'traffic_light': self.traffic_light_state,
            'stop_sign': self.stop_sign_detected,
            'stop_sign_distance': self.stop_sign_distance,
            'road_type': self.current_road_type,
            'road_speed_mult': self.road_speed_multiplier,
        }

        return steering, annotated, detection_info

    def should_stop_for_traffic(self) -> Tuple[bool, str]:
        """Check if car should stop for traffic light or sign."""
        if self.traffic_light_state == TrafficLightState.RED:
            return True, "RED LIGHT"

        if self.sign_detector.should_stop(self.stop_sign_detected, self.stop_sign_distance):
            return True, "STOP SIGN"

        return False, ""

    def should_slow_for_traffic(self) -> bool:
        """Check if car should slow down."""
        return self.traffic_light_state == TrafficLightState.YELLOW


# =============================================================================
# MAIN LOOP
# =============================================================================

def main():
    os.system('cls')
    print("=" * 60)
    print("  QCar 2 HYBRID Navigation - ACC 2026")
    print("  State Machine + Hysteresis + Traffic Detection")
    print("=" * 60)

    qlabs = QuanserInteractiveLabs()
    print("\nConnecting to QLabs...")

    if not qlabs.open("localhost"):
        print("Could not connect!")
        return

    print("Connected!")

    qlabs.destroy_all_spawned_actors()
    time.sleep(0.5)

    # Setup Competition Environment (Walls/Floor) - returns overhead camera
    overhead_cam = setup_environment(qlabs)

    print("Spawning QCar...")
    car = QLabsQCar2(qlabs)
    car.spawn_id_degrees(
        actorNumber=0,
        location=[-1.205, -0.83, 0.005],  # Taxi Hub (Competition Start)
        rotation=[0, 0, -44.7],            # Correct Orientation
        scale=[0.1, 0.1, 0.1],             # Competition scale
        configuration=0,
        waitForConfirmation=True
    )

    # Give QLabs time to initialize the actor and cameras
    print("Waiting 5s for cameras to initialize...")
    time.sleep(5.0)

    # Initialize components
    navigator = HybridNavigator()
    speed_controller = SpeedController(max_speed=0.35, min_speed=0.0)
    safety_monitor = SafetyMonitor()
    camera_manager = MultiCameraManager(car)

    # State machine
    taxi_state = TaxiState.WAITING_AT_HUB
    wait_start_time = 0.0
    WAIT_DURATION = 3.0

    # Start with first waypoint (Pickup)
    navigator.current_waypoint_idx = 0
    current_wp = navigator.next_waypoint()

    # Set initial LED
    car.set_led_strip_uniform(LED_COLORS[taxi_state])

    print("\n" + "=" * 60)
    print("  CONTROLS:")
    print("  Arrow keys = Manual override")
    print("  A = Toggle autonomous")
    print("  N = Next waypoint")
    print("  M = Toggle multi-camera view")
    print("  D = Toggle debug visualization")
    print("  T = Toggle traffic light detection")
    print("  R = Toggle road feature detection")
    print("  Q = Quit")
    print("=" * 60)
    print("\n  TIP: Press D to see lane detection debug windows!")

    # Car camera window
    cv2.namedWindow("Car Camera - Hybrid Navigation", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Car Camera - Hybrid Navigation", 800, 600)

    turn = 0.0
    autonomous = False
    show_multicam = False
    stopped_for_traffic = False
    traffic_stop_reason = ""
    # Traffic detection controlled via navigator.traffic_detection_enabled (default: False)

    running = True
    while running:
        # --- Input Handling ---
        if keyboard.is_pressed('q'):
            running = False
        elif keyboard.is_pressed('m'):
            show_multicam = not show_multicam
            print(f"\n  Multi-camera: {'ON' if show_multicam else 'OFF'}")
            time.sleep(0.2)
        elif keyboard.is_pressed('a'):
            autonomous = not autonomous
            if autonomous:
                speed_controller.set_target(0.35)
                taxi_state = current_wp['state']
                car.set_led_strip_uniform(LED_COLORS[taxi_state])
                print(f"\n  AUTONOMOUS: ON - State: {taxi_state.name}")
            else:
                speed_controller.stop()
                print("\n  AUTONOMOUS: OFF")
            time.sleep(0.2)
        elif keyboard.is_pressed('n'):
            current_wp = navigator.next_waypoint()
            taxi_state = current_wp['state']
            car.set_led_strip_uniform(LED_COLORS[taxi_state])
            print(f"\n  Target: {current_wp['name']} - State: {taxi_state.name}")
            time.sleep(0.2)
        elif keyboard.is_pressed('d'):
            debug_on = navigator.lane_detector.toggle_debug()
            print(f"\n  Debug mode: {'ON' if debug_on else 'OFF'}")
            time.sleep(0.2)
        elif keyboard.is_pressed('t'):
            navigator.traffic_detection_enabled = not navigator.traffic_detection_enabled
            print(f"\n  Traffic detection: {'ON' if navigator.traffic_detection_enabled else 'OFF'}")
            time.sleep(0.2)
        elif keyboard.is_pressed('r'):
            navigator.road_feature_enabled = not navigator.road_feature_enabled
            print(f"\n  Road feature detection: {'ON' if navigator.road_feature_enabled else 'OFF'}")
            time.sleep(0.2)

        # --- Manual Control ---
        if not autonomous:
            # Speed control - supports both arrow keys and WASD
            if keyboard.is_pressed('up') or keyboard.is_pressed('w'):
                speed_controller.current_speed = 1.0  # Faster forward
            elif keyboard.is_pressed('down') or keyboard.is_pressed('s'):
                speed_controller.current_speed = -0.5  # Reverse
            else:
                speed_controller.current_speed = 0.0

            # Steering control - supports both arrow keys and WASD
            if keyboard.is_pressed('left') or keyboard.is_pressed('a'):
                turn = -0.5  # Turn left (negative)
            elif keyboard.is_pressed('right') or keyboard.is_pressed('d'):
                turn = 0.5   # Turn right (positive)
            elif keyboard.is_pressed('space'):
                turn = 0.0
                speed_controller.current_speed = 0.0
            else:
                # Gradual return to center when no key pressed
                turn = turn * 0.7

        # --- Get Camera Image ---
        success, image = car.get_image(camera=car.CAMERA_CSI_FRONT)

        # --- Get Car State ---
        s_loc, loc, rot, scale = car.get_world_transform()

        if s_loc:
            heading_rad = math.radians(rot[2])
            car_state = {
                'x': loc[0],
                'y': loc[1],
                'z': loc[2],
                'heading': heading_rad
            }
            safety_monitor.update(loc[0], loc[1])
        else:
            car_state = {'x': 0, 'y': 0, 'z': 0, 'heading': 0}

        # --- Process Navigation ---
        if success and image is not None:
            steering, annotated, detection_info = navigator.process(image, car_state)

            if autonomous:
                turn = steering

                # Curvature-based speed control in LANE mode
                if navigator.mode == NavigationMode.LANE:
                    rec_speed = navigator.lane_detector.get_recommended_speed(0.5)
                    # Apply road feature speed multiplier (Phase 3)
                    if navigator.road_feature_enabled:
                        rec_speed *= detection_info.get('road_speed_mult', 1.0)
                    speed_controller.set_target(rec_speed)
                else:
                    # WAYPOINT mode - use normal speed with road feature adjustment
                    if not stopped_for_traffic:
                        base_speed = 0.35
                        if navigator.road_feature_enabled:
                            base_speed *= detection_info.get('road_speed_mult', 1.0)
                        speed_controller.set_target(base_speed)

                # Check for traffic stops (only if enabled)
                if navigator.traffic_detection_enabled:
                    should_stop, stop_reason = navigator.should_stop_for_traffic()
                    if should_stop and not stopped_for_traffic:
                        stopped_for_traffic = True
                        traffic_stop_reason = stop_reason
                        speed_controller.stop()
                        print(f"\n  STOP: {stop_reason}")
                    elif not should_stop and stopped_for_traffic:
                        stopped_for_traffic = False
                        traffic_stop_reason = ""
                        speed_controller.set_target(0.35)

                    # Slow for yellow light
                    if navigator.should_slow_for_traffic():
                        speed_controller.set_target(0.15)
                else:
                    # Traffic detection disabled - clear any previous stop
                    if stopped_for_traffic:
                        stopped_for_traffic = False
                        traffic_stop_reason = ""
                        speed_controller.set_target(0.35)

                # State machine handling
                _, dist = navigator.waypoint_nav.calculate_steering()

                # Slow down when approaching waypoint
                if dist < 0.5:
                    speed_controller.slow_approach(dist)

                # Check arrival based on state
                if taxi_state in [TaxiState.EN_ROUTE_TO_PICKUP,
                                  TaxiState.EN_ROUTE_TO_DROPOFF,
                                  TaxiState.RETURNING_TO_HUB]:

                    if navigator.check_arrival(dist):
                        # Transition to arrival state
                        taxi_state = current_wp['arrival_state']
                        car.set_led_strip_uniform(LED_COLORS[taxi_state])
                        speed_controller.stop()
                        wait_start_time = time.time()
                        print(f"\n  ARRIVED: {current_wp['name']} - State: {taxi_state.name}")

                elif taxi_state in [TaxiState.AT_PICKUP, TaxiState.AT_DROPOFF]:
                    # Waiting at location
                    speed_controller.stop()
                    elapsed = time.time() - wait_start_time

                    if elapsed > WAIT_DURATION:
                        # Move to next waypoint
                        current_wp = navigator.next_waypoint()
                        taxi_state = current_wp['state']
                        car.set_led_strip_uniform(LED_COLORS[taxi_state])
                        speed_controller.set_target(0.35)
                        print(f"\n  DEPARTING: Next target {current_wp['name']} - State: {taxi_state.name}")

                elif taxi_state == TaxiState.WAITING_AT_HUB:
                    # Completed full cycle
                    speed_controller.stop()

            # --- Annotate Display ---
            h, w = annotated.shape[:2]
            current_speed = speed_controller.update()

            # RIGHT SIDE - State info (spaced at 25px intervals)
            rx = w - 200  # Right column X position
            ry = 25       # Starting Y position

            state_color = {
                TaxiState.WAITING_AT_HUB: (255, 0, 255),
                TaxiState.EN_ROUTE_TO_PICKUP: (0, 255, 0),
                TaxiState.AT_PICKUP: (255, 0, 0),
                TaxiState.EN_ROUTE_TO_DROPOFF: (0, 255, 0),
                TaxiState.AT_DROPOFF: (0, 165, 255),
                TaxiState.RETURNING_TO_HUB: (0, 255, 0),
                TaxiState.STOPPED: (0, 0, 255),
            }.get(taxi_state, (255, 255, 255))

            cv2.putText(annotated, taxi_state.name, (rx, ry),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, state_color, 1)

            ry += 25
            cv2.putText(annotated, f"Speed: {current_speed:.2f}", (rx, ry),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 200, 0), 1)

            ry += 25
            cv2.putText(annotated, f"Curve: {navigator.lane_detector.curvature:.2f}", (rx, ry),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

            # Road feature info (Phase 3)
            if navigator.road_feature_enabled:
                ry += 25
                road_type = detection_info.get('road_type', RoadType.STRAIGHT)
                road_mult = detection_info.get('road_speed_mult', 1.0)
                road_color = {
                    RoadType.STRAIGHT: (0, 255, 0),
                    RoadType.CURVE_LEFT: (0, 165, 255),
                    RoadType.CURVE_RIGHT: (0, 165, 255),
                    RoadType.INTERSECTION: (0, 0, 255),
                    RoadType.ROUNDABOUT: (255, 0, 255),
                    RoadType.PARKING: (255, 255, 0),
                }.get(road_type, (200, 200, 200))
                cv2.putText(annotated, f"Road: {road_type.name}", (rx, ry),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, road_color, 1)
                ry += 20
                cv2.putText(annotated, f"Spd x{road_mult:.0%}", (rx, ry),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, road_color, 1)

            # Center screen overlays (only when needed)
            if taxi_state in [TaxiState.AT_PICKUP, TaxiState.AT_DROPOFF]:
                elapsed = time.time() - wait_start_time
                remaining = max(0, WAIT_DURATION - elapsed)
                cv2.putText(annotated, f"WAITING {remaining:.1f}s",
                           (w // 2 - 80, h // 2),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            if stopped_for_traffic:
                cv2.putText(annotated, f"STOP: {traffic_stop_reason}",
                           (w // 2 - 60, h // 2),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            if safety_monitor.is_stuck:
                cv2.putText(annotated, "STUCK!",
                           (w // 2 - 40, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            # --- Display ---
            if show_multicam:
                strip = camera_manager.create_surround_strip(size=(200, 150))
                annotated_resized = cv2.resize(annotated, (strip.shape[1], 300))
                combined = np.vstack([annotated_resized, strip])
                cv2.imshow("Car Camera - Hybrid Navigation", combined)
            else:
                cv2.imshow("Car Camera - Hybrid Navigation", annotated)

        else:
            # Camera failed
            if show_multicam:
                strip = camera_manager.create_surround_strip(size=(200, 150))
                dummy = np.zeros((300, strip.shape[1], 3), dtype=np.uint8)
                cv2.putText(dummy, "FRONT CAMERA FAILED", (200, 130),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                combined = np.vstack([dummy, strip])
                cv2.imshow("Car Camera - Hybrid Navigation", combined)
            else:
                dummy = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(dummy, "NO CAMERA SIGNAL", (200, 240),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                cv2.imshow("Car Camera - Hybrid Navigation", dummy)

        # --- Apply Control ---
        current_speed = speed_controller.update()
        car.set_velocity_and_request_state(
            forward=current_speed,
            turn=turn,
            headlights=False,  # Disabled - interferes with lane detection
            leftTurnSignal=(turn < -0.1),
            rightTurnSignal=(turn > 0.1),
            brakeSignal=(current_speed == 0),
            reverseSignal=(current_speed < 0)
        )

        key = cv2.waitKey(30) & 0xFF
        if key == 27:
            running = False

    # Cleanup
    car.set_velocity_and_request_state(0, 0, False, False, False, True, False)
    cv2.destroyAllWindows()
    print("\nStopped!")
    qlabs.close()
    print("Done!")


if __name__ == '__main__':
    main()
