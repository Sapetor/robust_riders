"""
Zone-aware Hybrid Navigator for QCar2 ACC 2026 Competition.

Combines multiple navigation strategies based on road context:
- LANE_FOLLOWING: Use lane detector steering (both lanes visible)
- WAYPOINT_ONLY: Pure waypoint navigation (no visible lanes)
- ROUNDABOUT: Right-edge following at reduced speed
- INTERSECTION: Waypoint-based with caution
- APPROACH_STOP/YIELD: Slow down for signs

Features:
- Integration with ZoneTransitionManager for zone decisions
- Integration with HybridSignDetector for sign-triggered zones
- Right-edge following mode for roundabouts
- Path/waypoint following for taxi mission
- Traffic light detection (togglable)
- Road feature detection integration (togglable)
- Hysteresis between modes
- Arrival detection for waypoints
"""

import time
import cv2
import numpy as np
from typing import Tuple, Dict, List, Optional

from .lane_detector import LaneDetector
from .waypoint_nav import WaypointNavigator
from .speed_controller import SpeedController

from state import NavigationZone, ZoneTransitionManager
from perception import HybridSignDetector, TrafficLightDetector, TrafficLightState


# Default path waypoints for taxi mission
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


class HybridNavigator:
    """
    Zone-aware hybrid navigator combining lane following and waypoint navigation.

    This class integrates all modular navigation components and implements
    zone-based navigation behaviors for the ACC 2026 competition.

    Attributes:
        lane_detector: LaneDetector for visual lane following
        waypoint_nav: WaypointNavigator for GPS-style waypoint following
        zone_manager: ZoneTransitionManager for zone state machine
        sign_detector: HybridSignDetector for sign detection
        traffic_light_detector: TrafficLightDetector for traffic lights
    """

    def __init__(self,
                 img_width: int = 820,
                 img_height: int = 410,
                 traffic_detection_enabled: bool = False,
                 road_feature_enabled: bool = False):
        """
        Initialize the hybrid navigator.

        Args:
            img_width: Image width for lane detector
            img_height: Image height for lane detector
            traffic_detection_enabled: Enable traffic light/sign detection
            road_feature_enabled: Enable road feature detection for speed
        """
        # Core navigation components
        self.lane_detector = LaneDetector(img_width, img_height)
        self.waypoint_nav = WaypointNavigator()

        # Zone management
        self.zone_manager = ZoneTransitionManager(
            lane_enter_threshold=0.25,
            lane_exit_threshold=0.10,
            min_zone_duration=1.0
        )

        # Perception components
        self.sign_detector = HybridSignDetector(use_hsv_fallback=True)
        self.traffic_light_detector = TrafficLightDetector()

        # Feature toggles
        self.traffic_detection_enabled = traffic_detection_enabled
        self.road_feature_enabled = road_feature_enabled

        # Arrival detection parameters
        self.arrival_threshold = 0.25  # meters
        self.arrival_stable_frames = 5  # consecutive frames

        # Right-edge following state (for roundabouts)
        self._right_edge_mode = False
        self._right_edge_offset = 0.30  # fraction of image width from right edge

        # Detection results cache
        self._traffic_light_state = TrafficLightState.NONE
        self._last_sign_detection: Optional[Tuple[str, float]] = None

        # Waypoint management
        self.waypoints: List[Dict] = []
        self.current_waypoint_idx = 0
        self._setup_default_waypoints()

        # Steering smoothing
        self._steering_history: List[float] = []
        self._steering_smooth_window = 3

    def _setup_default_waypoints(self):
        """Set up default taxi mission waypoints."""
        from state import TaxiState  # Avoid circular import

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

    def set_waypoints(self, waypoints: List[Dict]):
        """
        Set custom waypoints for navigation.

        Args:
            waypoints: List of waypoint dicts with 'name', 'pos', and optionally 'path'
        """
        self.waypoints = waypoints
        self.current_waypoint_idx = 0

    def process(self, image: np.ndarray, car_state: Dict) -> Tuple[float, np.ndarray, Dict]:
        """
        Process a frame and return navigation commands.

        This is the main entry point for the navigator. It:
        1. Updates position from car state
        2. Runs lane detection
        3. Runs sign/traffic detection (if enabled)
        4. Updates zone based on detections
        5. Calculates steering based on current zone
        6. Annotates the image with navigation info

        Args:
            image: BGR image from front camera
            car_state: Dict with 'x', 'y', 'z', 'heading' (radians)

        Returns:
            Tuple of (steering, annotated_image, detection_info)
        """
        # Update position
        self.waypoint_nav.update_position(
            car_state.get('x', 0),
            car_state.get('y', 0),
            car_state.get('z', 0),
            car_state.get('heading', 0)
        )

        # Run lane detection
        lane_steering, lane_confidence, annotated = self.lane_detector.detect(image)

        # Run sign detection if enabled
        sign_info = None
        if self.traffic_detection_enabled:
            sign_info = self.sign_detector.get_sign_for_zone_transition(image)
            self._last_sign_detection = sign_info

        # Update zone based on lane confidence and signs
        if sign_info:
            current_zone = self.zone_manager.update(
                lane_confidence,
                detected_sign=sign_info[0],
                sign_distance=sign_info[1]
            )
        else:
            current_zone = self.zone_manager.update(lane_confidence)

        # Run traffic light detection if enabled
        if self.traffic_detection_enabled:
            self._traffic_light_state, tl_conf, annotated = (
                self.traffic_light_detector.detect(annotated)
            )
        else:
            self._traffic_light_state = TrafficLightState.NONE

        # Calculate steering based on zone
        steering = self._calculate_zone_steering(
            current_zone, lane_steering, lane_confidence
        )

        # Smooth steering output
        steering = self._smooth_steering(steering)

        # Auto-advance through path waypoints
        self.waypoint_nav.advance_waypoint()

        # Annotate image
        annotated = self._annotate_image(
            annotated, steering, lane_confidence, current_zone
        )

        # Build detection info dict
        detection_info = {
            'lane_confidence': lane_confidence,
            'zone': current_zone,
            'traffic_light': self._traffic_light_state,
            'sign_detection': self._last_sign_detection,
            'curvature': self.lane_detector.curvature,
            'waypoint_distance': self._get_waypoint_distance(),
        }

        return steering, annotated, detection_info

    def _calculate_zone_steering(self,
                                  zone: NavigationZone,
                                  lane_steering: float,
                                  lane_confidence: float) -> float:
        """
        Calculate steering based on current navigation zone.

        Simple logic matching original behavior:
        - LANE_FOLLOWING: Pure lane steering (no blending)
        - Others: Pure waypoint steering

        Args:
            zone: Current navigation zone
            lane_steering: Steering from lane detector
            lane_confidence: Confidence of lane detection

        Returns:
            Final steering value in [-0.5, 0.5]
        """
        if zone == NavigationZone.LANE_FOLLOWING:
            # Pure lane steering - this worked well in original
            return lane_steering

        elif zone == NavigationZone.ROUNDABOUT:
            # Right-edge following for roundabouts
            return self._calculate_right_edge_steering(lane_confidence)

        else:  # WAYPOINT_ONLY, INTERSECTION, APPROACH_STOP, APPROACH_YIELD
            # Pure waypoint steering
            wp_steering, _ = self.waypoint_nav.calculate_steering()
            return wp_steering

    def _calculate_right_edge_steering(self, lane_confidence: float) -> float:
        """
        Calculate steering for right-edge following (roundabouts).

        In roundabouts, we follow only the right edge of the road,
        maintaining a safe distance from it.

        Args:
            lane_confidence: Current lane detection confidence

        Returns:
            Steering value for right-edge following
        """
        # Check if we have right lane lines
        if self.lane_detector.right_lines:
            # Use right lines to calculate offset
            h = self.lane_detector.img_height
            w = self.lane_detector.img_width

            # Get rightmost line position at bottom of image
            right_x_bottom_vals = []
            for x1, y1, x2, y2 in self.lane_detector.right_lines:
                if y2 != y1:
                    slope = (x2 - x1) / (y2 - y1)
                    x_at_bottom = x1 + slope * (h - y1)
                    right_x_bottom_vals.append(x_at_bottom)

            if right_x_bottom_vals:
                right_x = np.mean(right_x_bottom_vals)

                # Target: stay at safe distance from right edge
                safe_distance = w * self._right_edge_offset
                target_x = right_x - safe_distance

                # Calculate error relative to image center
                image_center = w / 2
                error = (target_x - image_center) / (w / 2)

                # Use lane detector's PID for smooth control
                return self.lane_detector._pid_steering(error)

        # Fallback to waypoint steering if no right edge detected
        wp_steering, _ = self.waypoint_nav.calculate_steering()
        return wp_steering

    def _smooth_steering(self, steering: float) -> float:
        """Apply temporal smoothing to steering output."""
        self._steering_history.append(steering)
        if len(self._steering_history) > self._steering_smooth_window:
            self._steering_history.pop(0)
        return np.mean(self._steering_history)

    def _get_waypoint_distance(self) -> float:
        """Get distance to current waypoint."""
        if self.waypoint_nav.target is None:
            return float('inf')
        _, dist = self.waypoint_nav.calculate_steering()
        return dist

    def _annotate_image(self,
                        image: np.ndarray,
                        steering: float,
                        lane_confidence: float,
                        zone: NavigationZone) -> np.ndarray:
        """
        Annotate image with navigation information.

        Args:
            image: Image to annotate
            steering: Current steering value
            lane_confidence: Lane detection confidence
            zone: Current navigation zone

        Returns:
            Annotated image
        """
        h, w = image.shape[:2]
        y = 25  # Starting Y position

        # Zone indicator with color coding
        zone_colors = {
            NavigationZone.LANE_FOLLOWING: (0, 255, 0),      # Green
            NavigationZone.WAYPOINT_ONLY: (0, 200, 255),     # Orange
            NavigationZone.ROUNDABOUT: (255, 0, 255),        # Magenta
            NavigationZone.INTERSECTION: (255, 255, 0),      # Cyan
            NavigationZone.APPROACH_STOP: (0, 0, 255),       # Red
            NavigationZone.APPROACH_YIELD: (0, 165, 255),    # Orange-red
        }
        zone_color = zone_colors.get(zone, (255, 255, 255))

        cv2.putText(image, f"Zone: {zone.name}", (10, y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, zone_color, 2)

        y += 25
        cv2.putText(image, f"Lane: {lane_confidence:.0%}", (10, y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

        y += 25
        cv2.putText(image, f"Steer: {steering:+.2f}", (10, y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 200, 0), 1)

        # Waypoint info
        if self.waypoint_nav.target is not None:
            wp = self.get_current_waypoint()
            if wp:
                _, dist = self.waypoint_nav.calculate_steering()
                path_idx, path_total = self.waypoint_nav.get_path_progress()
                y += 25
                if path_total > 0:
                    cv2.putText(image,
                               f"To: {wp['name']} [{path_idx+1}/{path_total}] {dist:.1f}m",
                               (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 255), 1)
                else:
                    cv2.putText(image, f"To: {wp['name']} {dist:.1f}m",
                               (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 255), 1)

        # Traffic light indicator
        if self.traffic_detection_enabled:
            y += 25
            tl_colors = {
                TrafficLightState.RED: (0, 0, 255),
                TrafficLightState.YELLOW: (0, 255, 255),
                TrafficLightState.GREEN: (0, 255, 0),
                TrafficLightState.NONE: (128, 128, 128),
            }
            tl_color = tl_colors.get(self._traffic_light_state, (128, 128, 128))
            cv2.putText(image, f"TL: {self._traffic_light_state.name}",
                       (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, tl_color, 1)

        # Right-edge mode indicator
        if zone == NavigationZone.ROUNDABOUT:
            cv2.putText(image, "RIGHT-EDGE", (w - 120, 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2)

        return image

    def check_arrival(self, distance: float = None) -> bool:
        """
        Check if we've arrived at the final waypoint.

        Args:
            distance: Optional distance override, otherwise calculated

        Returns:
            True if arrived at final waypoint with stable position
        """
        # Only check arrival for final waypoint in path
        if not self.waypoint_nav.is_final_waypoint():
            return False

        if distance is None:
            distance = self._get_waypoint_distance()

        if distance >= self.arrival_threshold:
            return False

        # Also check stable position
        return self.waypoint_nav.check_stable_position(
            threshold=0.03, frames=self.arrival_stable_frames
        )

    def next_waypoint(self) -> Optional[Dict]:
        """
        Advance to the next waypoint in the sequence.

        Returns:
            The new waypoint dict, or None if no waypoints defined
        """
        if not self.waypoints:
            return None

        self.current_waypoint_idx = (self.current_waypoint_idx + 1) % len(self.waypoints)
        wp = self.waypoints[self.current_waypoint_idx]

        # Use path if available, otherwise single target
        if "path" in wp and wp["path"]:
            self.waypoint_nav.set_path(wp["path"])
        else:
            self.waypoint_nav.set_target(wp["pos"])

        # Reset zone manager when changing waypoints
        self.zone_manager.clear_override()

        return wp

    def get_current_waypoint(self) -> Optional[Dict]:
        """
        Get the current waypoint info.

        Returns:
            Current waypoint dict or None if no waypoints
        """
        if not self.waypoints:
            return None
        return self.waypoints[self.current_waypoint_idx]

    def should_stop_for_traffic(self) -> Tuple[bool, str]:
        """
        Check if the car should stop for traffic conditions.

        Returns:
            Tuple of (should_stop, reason_string)
        """
        if not self.traffic_detection_enabled:
            return False, ""

        # Red light
        if self._traffic_light_state == TrafficLightState.RED:
            return True, "RED LIGHT"

        # Stop sign zone
        if self.zone_manager.get_zone() == NavigationZone.APPROACH_STOP:
            return True, "STOP SIGN"

        return False, ""

    def should_slow_for_traffic(self) -> bool:
        """
        Check if the car should slow down for traffic conditions.

        Returns:
            True if should slow down
        """
        if not self.traffic_detection_enabled:
            return False

        # Yellow light
        if self._traffic_light_state == TrafficLightState.YELLOW:
            return True

        # Approach zones
        zone = self.zone_manager.get_zone()
        if zone in (NavigationZone.APPROACH_STOP, NavigationZone.APPROACH_YIELD):
            return True

        return False

    def get_recommended_speed_factor(self) -> float:
        """
        Get speed factor based on current zone and conditions.

        Returns:
            Speed multiplier (0.0 to 1.0)
        """
        # Get base factor from zone manager
        factor = self.zone_manager.get_recommended_speed_factor()

        # Apply curvature reduction
        curvature_factor = max(0.3, 1.0 - self.lane_detector.curvature * 0.5)
        factor *= curvature_factor

        # Apply traffic slowdowns
        if self.should_slow_for_traffic():
            factor *= 0.5

        return max(0.2, min(1.0, factor))

    def force_zone(self, zone: NavigationZone, duration: float = 5.0):
        """
        Force a specific navigation zone for a duration.

        Useful for testing or manual zone control.

        Args:
            zone: Zone to force
            duration: Duration in seconds
        """
        self.zone_manager.force_zone(zone, duration)

    def toggle_traffic_detection(self) -> bool:
        """
        Toggle traffic detection on/off.

        Returns:
            New state of traffic detection
        """
        self.traffic_detection_enabled = not self.traffic_detection_enabled
        return self.traffic_detection_enabled

    def toggle_debug(self) -> bool:
        """
        Toggle lane detector debug mode.

        Returns:
            New debug state
        """
        return self.lane_detector.toggle_debug()

    @property
    def current_zone(self) -> NavigationZone:
        """Get the current navigation zone."""
        return self.zone_manager.get_zone()

    @property
    def lane_confidence(self) -> float:
        """Get current lane detection confidence."""
        return self.lane_detector.lane_confidence

    @property
    def traffic_light_state(self) -> TrafficLightState:
        """Get current traffic light state."""
        return self._traffic_light_state
