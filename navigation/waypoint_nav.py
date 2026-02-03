"""Waypoint navigation with PID steering control and path following."""

import math
import numpy as np
from typing import List, Tuple


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
