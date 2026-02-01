"""
YOLO Road Feature Detector - ACC 2026

Uses YOLOv8 to detect road features (straight, curves, intersections, roundabouts).
This replaces the classical CV approach in road_features.py.

Setup:
1. pip install ultralytics
2. Train model with: python train_yolo.py
3. Model saved to: models/road_features.pt

Usage:
    from yolo_road_detector import YOLONavigationAdvisor
    advisor = YOLONavigationAdvisor()
    feature = advisor.update(image)
    speed_mult = advisor.get_speed_multiplier()
"""

import os
from enum import Enum, auto
from dataclasses import dataclass
from typing import Tuple, Optional, Dict
import numpy as np
import cv2

# Try to import ultralytics
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("Warning: ultralytics not installed. Run: pip install ultralytics")


class RoadType(Enum):
    """Road feature classes (must match training labels)."""
    STRAIGHT = 0
    CURVE_LEFT = 1
    CURVE_RIGHT = 2
    INTERSECTION = 3
    ROUNDABOUT = 4
    UNKNOWN = 99


# Speed multipliers for each road type
SPEED_MULTIPLIERS = {
    RoadType.STRAIGHT: 1.0,
    RoadType.CURVE_LEFT: 0.6,
    RoadType.CURVE_RIGHT: 0.6,
    RoadType.INTERSECTION: 0.3,
    RoadType.ROUNDABOUT: 0.25,
    RoadType.UNKNOWN: 0.8,
}


@dataclass
class RoadFeature:
    """Detected road feature with metadata."""
    road_type: RoadType
    confidence: float
    recommended_speed: float
    bbox: Optional[Tuple[int, int, int, int]] = None  # x1, y1, x2, y2


class YOLORoadDetector:
    """
    YOLO-based road feature detection.

    Uses a trained YOLOv8 classification model to detect road types.
    """

    def __init__(self, model_path: str = None):
        """
        Initialize detector with trained model.

        Args:
            model_path: Path to trained .pt model file.
                       If None, looks in models/road_features.pt
        """
        self.model = None
        self.model_loaded = False

        if not YOLO_AVAILABLE:
            print("YOLO not available - using fallback")
            return

        # Default model path
        if model_path is None:
            model_path = os.path.join(
                os.path.dirname(__file__),
                "models",
                "road_features.pt"
            )

        # Load model if exists
        if os.path.exists(model_path):
            try:
                self.model = YOLO(model_path)
                self.model_loaded = True
                print(f"Loaded YOLO model: {model_path}")
            except Exception as e:
                print(f"Failed to load model: {e}")
        else:
            print(f"Model not found: {model_path}")
            print("Train a model first with: python train_yolo.py")

        # Class name to RoadType mapping
        self.class_map = {
            'straight': RoadType.STRAIGHT,
            'curve_left': RoadType.CURVE_LEFT,
            'curve_right': RoadType.CURVE_RIGHT,
            'intersection': RoadType.INTERSECTION,
            'roundabout': RoadType.ROUNDABOUT,
        }

        # Detection history for temporal smoothing
        self.history: list = []
        self.max_history = 5

    def detect(self, image: np.ndarray) -> RoadFeature:
        """
        Detect road feature in image.

        Args:
            image: BGR image from camera

        Returns:
            RoadFeature with detected type and confidence
        """
        if not self.model_loaded:
            return RoadFeature(
                road_type=RoadType.UNKNOWN,
                confidence=0.0,
                recommended_speed=1.0
            )

        # Run inference
        results = self.model(image, verbose=False)

        if len(results) == 0:
            return self._fallback_result()

        # Get top prediction (classification model)
        result = results[0]

        if hasattr(result, 'probs') and result.probs is not None:
            # Classification model
            probs = result.probs
            top_class_idx = probs.top1
            confidence = probs.top1conf.item()
            class_name = result.names[top_class_idx]

            road_type = self.class_map.get(class_name, RoadType.UNKNOWN)

        elif hasattr(result, 'boxes') and len(result.boxes) > 0:
            # Detection model - get highest confidence box
            boxes = result.boxes
            best_idx = boxes.conf.argmax()
            confidence = boxes.conf[best_idx].item()
            class_idx = int(boxes.cls[best_idx].item())
            class_name = result.names[class_idx]

            road_type = self.class_map.get(class_name, RoadType.UNKNOWN)
        else:
            return self._fallback_result()

        # Temporal smoothing
        self.history.append(road_type)
        if len(self.history) > self.max_history:
            self.history.pop(0)

        # Use most common recent prediction
        if len(self.history) >= 3:
            from collections import Counter
            counts = Counter(self.history[-3:])
            road_type = counts.most_common(1)[0][0]

        speed_mult = SPEED_MULTIPLIERS.get(road_type, 1.0)

        return RoadFeature(
            road_type=road_type,
            confidence=confidence,
            recommended_speed=speed_mult
        )

    def _fallback_result(self) -> RoadFeature:
        """Return fallback when detection fails."""
        return RoadFeature(
            road_type=RoadType.STRAIGHT,
            confidence=0.5,
            recommended_speed=1.0
        )


class YOLONavigationAdvisor:
    """
    Navigation advisor using YOLO detection.

    Drop-in replacement for NavigationAdvisor from road_features.py.
    """

    def __init__(self, model_path: str = None):
        self.detector = YOLORoadDetector(model_path)
        self.current_feature: Optional[RoadFeature] = None

    def update(self, image: np.ndarray) -> RoadFeature:
        """Update detection with new frame."""
        self.current_feature = self.detector.detect(image)
        return self.current_feature

    def get_speed_multiplier(self) -> float:
        """Get recommended speed multiplier."""
        if self.current_feature is None:
            return 1.0
        return self.current_feature.recommended_speed

    def get_steering_adjustment(self, base_steering: float) -> float:
        """
        Adjust steering based on detected features.
        For now, just return base steering (YOLO doesn't provide curvature).
        """
        return base_steering

    def should_stop(self) -> bool:
        """Check if car should stop."""
        if self.current_feature is None:
            return False
        # Stop at high-confidence intersections
        return (self.current_feature.road_type == RoadType.INTERSECTION and
                self.current_feature.confidence > 0.8)

    def get_status_text(self) -> str:
        """Get status for display."""
        if self.current_feature is None:
            return "No detection"
        f = self.current_feature
        return f"YOLO: {f.road_type.name} ({f.confidence:.0%})"

    def is_available(self) -> bool:
        """Check if YOLO model is loaded."""
        return self.detector.model_loaded


def visualize_detection(image: np.ndarray, feature: RoadFeature) -> np.ndarray:
    """Draw detection result on image."""
    output = image.copy()
    h, w = output.shape[:2]

    # Color by road type
    colors = {
        RoadType.STRAIGHT: (0, 255, 0),
        RoadType.CURVE_LEFT: (0, 165, 255),
        RoadType.CURVE_RIGHT: (0, 165, 255),
        RoadType.INTERSECTION: (0, 0, 255),
        RoadType.ROUNDABOUT: (255, 0, 255),
        RoadType.UNKNOWN: (128, 128, 128),
    }
    color = colors.get(feature.road_type, (255, 255, 255))

    # Draw label
    label = f"YOLO: {feature.road_type.name} {feature.confidence:.0%}"
    cv2.putText(output, label, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    # Speed indicator
    speed_label = f"Speed: {feature.recommended_speed:.0%}"
    cv2.putText(output, speed_label, (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

    return output


if __name__ == '__main__':
    print("YOLO Road Detector - ACC 2026")
    print("=" * 50)

    if YOLO_AVAILABLE:
        print("ultralytics is installed")
    else:
        print("ultralytics NOT installed")
        print("Run: pip install ultralytics")

    print("\nRoad types:")
    for rt in RoadType:
        if rt != RoadType.UNKNOWN:
            mult = SPEED_MULTIPLIERS.get(rt, 1.0)
            print(f"  {rt.name}: speed x{mult:.0%}")

    print("\nUsage:")
    print("  1. Capture training data: python capture_training_data.py")
    print("  2. Label images in datasets/road_features/")
    print("  3. Train model: python train_yolo.py")
    print("  4. Model saved to: models/road_features.pt")
