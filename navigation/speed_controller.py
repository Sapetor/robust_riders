"""Smooth speed control with acceleration/deceleration ramps."""

import time
import numpy as np


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
