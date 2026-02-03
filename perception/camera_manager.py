"""Multi-camera management with caching for QCar2."""

import time
import cv2
import numpy as np
from typing import Optional, Tuple, Dict


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
