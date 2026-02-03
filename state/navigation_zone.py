"""Navigation zone state machine for context-aware driving."""

from enum import Enum, auto
from typing import Optional, Tuple
import time


class NavigationZone(Enum):
    """Road context zones that determine navigation behavior."""
    LANE_FOLLOWING = auto()      # Good lane markings - use lane detector
    WAYPOINT_ONLY = auto()       # No lanes - pure waypoint navigation
    ROUNDABOUT = auto()          # Right-edge following at reduced speed
    INTERSECTION = auto()        # Waypoint-based, cautious navigation
    APPROACH_STOP = auto()       # Approaching stop sign - slow down
    APPROACH_YIELD = auto()      # Approaching yield sign - slow down


class ZoneTransitionManager:
    """Manages transitions between navigation zones with hysteresis."""

    def __init__(self,
                 lane_enter_threshold: float = 0.25,
                 lane_exit_threshold: float = 0.10,
                 min_zone_duration: float = 1.0):
        """
        Initialize zone transition manager.

        Args:
            lane_enter_threshold: Lane confidence to enter LANE_FOLLOWING
            lane_exit_threshold: Lane confidence to exit LANE_FOLLOWING
            min_zone_duration: Minimum seconds in zone before switching
        """
        self.lane_enter_threshold = lane_enter_threshold
        self.lane_exit_threshold = lane_exit_threshold
        self.min_zone_duration = min_zone_duration

        self.current_zone = NavigationZone.WAYPOINT_ONLY
        self.zone_start_time = time.time()
        self.previous_zone = None

        # Sign-triggered zone override (takes priority)
        self._sign_override: Optional[NavigationZone] = None
        self._sign_override_time: float = 0.0
        self._sign_override_duration: float = 5.0  # seconds

    def get_zone(self) -> NavigationZone:
        """Get current navigation zone."""
        # Check if sign override is active
        if self._sign_override is not None:
            elapsed = time.time() - self._sign_override_time
            if elapsed < self._sign_override_duration:
                return self._sign_override
            else:
                self._sign_override = None

        return self.current_zone

    def update(self,
               lane_confidence: float,
               detected_sign: Optional[str] = None,
               sign_distance: float = float('inf')) -> NavigationZone:
        """
        Update zone based on sensor inputs.

        Args:
            lane_confidence: Current lane detection confidence (0-1)
            detected_sign: Detected sign type ('roundabout', 'stop', 'yield', or None)
            sign_distance: Distance to detected sign in meters

        Returns:
            Current navigation zone
        """
        now = time.time()
        time_in_zone = now - self.zone_start_time

        # Priority 1: Sign-triggered zones (override lane confidence)
        if detected_sign is not None:
            new_zone = self._get_zone_for_sign(detected_sign, sign_distance)
            if new_zone is not None:
                self._sign_override = new_zone
                self._sign_override_time = now
                return new_zone

        # Priority 2: Lane confidence-based transitions (with hysteresis)
        if time_in_zone >= self.min_zone_duration:
            if self.current_zone == NavigationZone.WAYPOINT_ONLY:
                if lane_confidence > self.lane_enter_threshold:
                    self._transition_to(NavigationZone.LANE_FOLLOWING)
            elif self.current_zone == NavigationZone.LANE_FOLLOWING:
                if lane_confidence < self.lane_exit_threshold:
                    self._transition_to(NavigationZone.WAYPOINT_ONLY)

        return self.get_zone()

    def _get_zone_for_sign(self, sign_type: str, distance: float) -> Optional[NavigationZone]:
        """Determine zone based on detected sign."""
        sign_type = sign_type.lower()

        if sign_type == 'roundabout' and distance < 0.8:
            return NavigationZone.ROUNDABOUT
        elif sign_type == 'stop' and distance < 0.5:
            return NavigationZone.APPROACH_STOP
        elif sign_type == 'yield' and distance < 0.6:
            return NavigationZone.APPROACH_YIELD

        return None

    def _transition_to(self, new_zone: NavigationZone):
        """Transition to a new zone."""
        if new_zone != self.current_zone:
            self.previous_zone = self.current_zone
            self.current_zone = new_zone
            self.zone_start_time = time.time()

    def force_zone(self, zone: NavigationZone, duration: float = 5.0):
        """Force a specific zone for a duration (e.g., for intersection handling)."""
        self._sign_override = zone
        self._sign_override_time = time.time()
        self._sign_override_duration = duration

    def clear_override(self):
        """Clear any sign-triggered zone override."""
        self._sign_override = None

    def get_recommended_speed_factor(self) -> float:
        """Get speed factor based on current zone (1.0 = normal)."""
        zone = self.get_zone()
        factors = {
            NavigationZone.LANE_FOLLOWING: 1.0,
            NavigationZone.WAYPOINT_ONLY: 0.9,
            NavigationZone.ROUNDABOUT: 0.6,
            NavigationZone.INTERSECTION: 0.5,
            NavigationZone.APPROACH_STOP: 0.4,
            NavigationZone.APPROACH_YIELD: 0.6,
        }
        return factors.get(zone, 0.8)

    def should_use_lane_detection(self) -> bool:
        """Check if current zone should use lane detection."""
        zone = self.get_zone()
        return zone in (NavigationZone.LANE_FOLLOWING, NavigationZone.ROUNDABOUT)

    def should_use_right_edge_only(self) -> bool:
        """Check if current zone should follow right edge only (roundabout)."""
        return self.get_zone() == NavigationZone.ROUNDABOUT
