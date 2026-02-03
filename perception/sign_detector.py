"""
Sign detection for ACC 2026 competition.

Supports:
- YOLO object detection (when model available)
- HSV fallback detection
- Signs: roundabout, stop, yield
"""

import os
import time
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict
import numpy as np
import cv2

# Try to import ultralytics for YOLO
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False


class SignType(Enum):
    """Detected sign types."""
    NONE = auto()
    STOP = auto()
    YIELD = auto()
    ROUNDABOUT = auto()


@dataclass
class DetectedSign:
    """Detection result for a single sign."""
    sign_type: SignType
    confidence: float
    distance: float  # Estimated distance in meters
    bbox: Optional[Tuple[int, int, int, int]] = None  # x1, y1, x2, y2
    center: Optional[Tuple[int, int]] = None  # center x, y in image


class YOLOSignDetector:
    """
    YOLO-based sign detection.

    Requires a trained object detection model with classes:
    - stop
    - yield
    - roundabout
    """

    def __init__(self, model_path: str = None, confidence_threshold: float = 0.5):
        self.model = None
        self.model_loaded = False
        self.confidence_threshold = confidence_threshold

        if not YOLO_AVAILABLE:
            return

        # Default model path
        if model_path is None:
            model_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "models",
                "sign_detector.pt"
            )

        if os.path.exists(model_path):
            try:
                self.model = YOLO(model_path)
                self.model_loaded = True
                print(f"Loaded YOLO sign model: {model_path}")
            except Exception as e:
                print(f"Failed to load sign model: {e}")

        # Class name mapping
        self.class_map = {
            'stop': SignType.STOP,
            'yield': SignType.YIELD,
            'roundabout': SignType.ROUNDABOUT,
            'stop_sign': SignType.STOP,
            'yield_sign': SignType.YIELD,
            'roundabout_sign': SignType.ROUNDABOUT,
        }

    def detect(self, image: np.ndarray) -> List[DetectedSign]:
        """Detect signs using YOLO."""
        if not self.model_loaded:
            return []

        results = self.model(image, verbose=False)
        signs = []

        if len(results) == 0:
            return signs

        result = results[0]
        if not hasattr(result, 'boxes') or len(result.boxes) == 0:
            return signs

        h, w = image.shape[:2]

        for box in result.boxes:
            conf = box.conf.item()
            if conf < self.confidence_threshold:
                continue

            class_idx = int(box.cls.item())
            class_name = result.names[class_idx].lower()
            sign_type = self.class_map.get(class_name)

            if sign_type is None:
                continue

            # Get bounding box
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            bbox = (int(x1), int(y1), int(x2), int(y2))
            center = (int((x1 + x2) / 2), int((y1 + y2) / 2))

            # Estimate distance from apparent size
            box_height = y2 - y1
            # Calibration: at 0.5m, sign is ~100px tall (adjust as needed)
            distance = 50.0 / max(box_height, 1)
            distance = max(0.1, min(5.0, distance))  # Clamp to reasonable range

            signs.append(DetectedSign(
                sign_type=sign_type,
                confidence=conf,
                distance=distance,
                bbox=bbox,
                center=center
            ))

        return signs


class HSVSignDetector:
    """
    HSV-based sign detection (fallback).

    Uses color and shape detection for signs.
    """

    def __init__(self):
        # Red color ranges (for stop/yield)
        self.red_low1 = np.array([0, 100, 100])
        self.red_high1 = np.array([10, 255, 255])
        self.red_low2 = np.array([160, 100, 100])
        self.red_high2 = np.array([180, 255, 255])

        # Blue color range (for roundabout sign background)
        self.blue_low = np.array([100, 100, 80])
        self.blue_high = np.array([130, 255, 255])

        # Yellow color range (for yield sign)
        self.yellow_low = np.array([15, 100, 100])
        self.yellow_high = np.array([35, 255, 255])

        self.min_area = 150

    def detect(self, image: np.ndarray) -> List[DetectedSign]:
        """Detect signs using HSV color filtering."""
        signs = []
        h, w = image.shape[:2]
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Detect red signs (stop, yield)
        red_mask1 = cv2.inRange(hsv, self.red_low1, self.red_high1)
        red_mask2 = cv2.inRange(hsv, self.red_low2, self.red_high2)
        red_mask = cv2.bitwise_or(red_mask1, red_mask2)

        red_signs = self._find_signs_in_mask(red_mask, image, [SignType.STOP, SignType.YIELD])
        signs.extend(red_signs)

        # Detect blue signs (roundabout)
        blue_mask = cv2.inRange(hsv, self.blue_low, self.blue_high)
        blue_signs = self._find_signs_in_mask(blue_mask, image, [SignType.ROUNDABOUT])
        signs.extend(blue_signs)

        return signs

    def _find_signs_in_mask(self, mask: np.ndarray, image: np.ndarray,
                            possible_types: List[SignType]) -> List[DetectedSign]:
        """Find sign candidates in a binary mask."""
        signs = []
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.min_area:
                continue

            # Approximate polygon to determine shape
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            x, y, box_w, box_h = cv2.boundingRect(contour)
            aspect = box_w / box_h if box_h > 0 else 0

            # Classify by shape
            num_vertices = len(approx)
            sign_type = None
            confidence = 0.5

            if SignType.STOP in possible_types:
                # Stop signs are octagonal (6-10 vertices) and roughly square
                if 6 <= num_vertices <= 10 and 0.7 < aspect < 1.3:
                    sign_type = SignType.STOP
                    confidence = min(0.8, area / 1000)

            if SignType.YIELD in possible_types and sign_type is None:
                # Yield signs are triangular (3 vertices)
                if 3 <= num_vertices <= 5 and 0.7 < aspect < 1.5:
                    sign_type = SignType.YIELD
                    confidence = min(0.7, area / 800)

            if SignType.ROUNDABOUT in possible_types and sign_type is None:
                # Roundabout signs are roughly circular/square
                perimeter = cv2.arcLength(contour, True)
                if perimeter > 0:
                    circularity = 4 * np.pi * area / (perimeter * perimeter)
                    if circularity > 0.5 and 0.6 < aspect < 1.6:
                        sign_type = SignType.ROUNDABOUT
                        confidence = min(0.7, area / 800)

            if sign_type is not None:
                # Estimate distance from size
                distance = 50.0 / max(box_h, 1)
                distance = max(0.1, min(5.0, distance))

                bbox = (x, y, x + box_w, y + box_h)
                center = (x + box_w // 2, y + box_h // 2)

                signs.append(DetectedSign(
                    sign_type=sign_type,
                    confidence=confidence,
                    distance=distance,
                    bbox=bbox,
                    center=center
                ))

        return signs


class HybridSignDetector:
    """
    Hybrid sign detector combining YOLO and HSV approaches.

    Uses YOLO when available, falls back to HSV otherwise.
    """

    def __init__(self,
                 yolo_model_path: str = None,
                 yolo_confidence: float = 0.5,
                 use_hsv_fallback: bool = True):
        self.yolo_detector = YOLOSignDetector(yolo_model_path, yolo_confidence)
        self.hsv_detector = HSVSignDetector()
        self.use_hsv_fallback = use_hsv_fallback

        # Detection history for temporal smoothing
        self.detection_history: List[List[DetectedSign]] = []
        self.max_history = 5

        # Cooldown for repeated detection (prevent spam)
        self.last_detection_time: Dict[SignType, float] = {}
        self.detection_cooldown = 3.0  # seconds

    def detect(self, image: np.ndarray) -> List[DetectedSign]:
        """
        Detect signs in image.

        Returns list of detected signs, prioritizing YOLO results.
        """
        signs = []

        # Try YOLO first
        if self.yolo_detector.model_loaded:
            signs = self.yolo_detector.detect(image)

        # Fall back to HSV if no YOLO results
        if len(signs) == 0 and self.use_hsv_fallback:
            signs = self.hsv_detector.detect(image)

        # Add to history for smoothing
        self.detection_history.append(signs)
        if len(self.detection_history) > self.max_history:
            self.detection_history.pop(0)

        return signs

    def get_closest_sign(self, image: np.ndarray) -> Optional[DetectedSign]:
        """Get the closest detected sign."""
        signs = self.detect(image)
        if not signs:
            return None
        return min(signs, key=lambda s: s.distance)

    def get_sign_for_zone_transition(self, image: np.ndarray) -> Optional[Tuple[str, float]]:
        """
        Get sign info formatted for ZoneTransitionManager.

        Returns: (sign_type_name, distance) or None
        """
        closest = self.get_closest_sign(image)
        if closest is None:
            return None

        # Check cooldown
        now = time.time()
        last_time = self.last_detection_time.get(closest.sign_type, 0)
        if now - last_time < self.detection_cooldown:
            return None

        self.last_detection_time[closest.sign_type] = now

        sign_name_map = {
            SignType.STOP: 'stop',
            SignType.YIELD: 'yield',
            SignType.ROUNDABOUT: 'roundabout',
        }

        name = sign_name_map.get(closest.sign_type)
        if name:
            return (name, closest.distance)
        return None

    def is_yolo_available(self) -> bool:
        """Check if YOLO detection is available."""
        return self.yolo_detector.model_loaded

    def annotate(self, image: np.ndarray, signs: List[DetectedSign] = None) -> np.ndarray:
        """Draw detected signs on image."""
        output = image.copy()

        if signs is None:
            signs = self.detect(image)

        colors = {
            SignType.STOP: (0, 0, 255),      # Red
            SignType.YIELD: (0, 255, 255),   # Yellow
            SignType.ROUNDABOUT: (255, 0, 0), # Blue
        }

        for sign in signs:
            color = colors.get(sign.sign_type, (255, 255, 255))

            if sign.bbox:
                x1, y1, x2, y2 = sign.bbox
                cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)

                label = f"{sign.sign_type.name} {sign.distance:.1f}m"
                cv2.putText(output, label, (x1, y1 - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        return output


# Legacy compatibility - keep original class name
class SignDetector(HybridSignDetector):
    """Legacy alias for HybridSignDetector."""

    def __init__(self):
        super().__init__(use_hsv_fallback=True)

    def detect_stop_sign(self, image: np.ndarray) -> Tuple[bool, float, np.ndarray]:
        """
        Legacy interface for stop sign detection.
        Returns: (detected, distance, annotated_image)
        """
        signs = self.detect(image)
        output = self.annotate(image, signs)

        stop_signs = [s for s in signs if s.sign_type == SignType.STOP]
        if stop_signs:
            closest = min(stop_signs, key=lambda s: s.distance)
            return True, closest.distance, output

        return False, float('inf'), output

    def should_stop(self, detected: bool, distance: float) -> bool:
        """Legacy interface for stop decision."""
        if detected and distance < 0.5:
            now = time.time()
            last_time = self.last_detection_time.get(SignType.STOP, 0)
            if now - last_time > self.detection_cooldown + 1.0:
                self.last_detection_time[SignType.STOP] = now
                return True
        return False
