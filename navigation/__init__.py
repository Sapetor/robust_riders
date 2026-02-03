"""Navigation modules for QCar2 hybrid navigation."""

from enum import Enum, auto

from .lane_detector import LaneDetector
from .waypoint_nav import WaypointNavigator
from .speed_controller import SpeedController
from .hybrid_navigator import HybridNavigator, PATHS


class NavigationMode(Enum):
    """Navigation mode for driving."""
    WAYPOINT = auto()  # Follow waypoints
    LANE = auto()      # Follow lane markings


__all__ = [
    'LaneDetector',
    'WaypointNavigator',
    'SpeedController',
    'NavigationMode',
    'HybridNavigator',
    'PATHS',
]
