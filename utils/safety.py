"""Safety monitoring for stuck detection."""

import time
import numpy as np


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
