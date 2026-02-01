"""
QCar 2 Road Feature Detection - ACC 2026
Detects road infrastructure for better navigation at intersections,
roundabouts, curves, and parking areas.

Uses: Canny edge analysis beyond straight-line detection
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Tuple, List, Optional, Dict
import cv2
import numpy as np


class RoadType(Enum):
    """Classification of road segment types."""
    STRAIGHT = auto()
    CURVE_LEFT = auto()
    CURVE_RIGHT = auto()
    INTERSECTION = auto()
    ROUNDABOUT = auto()
    PARKING = auto()
    UNKNOWN = auto()


@dataclass
class RoadFeature:
    """Detected road feature with metadata."""
    road_type: RoadType
    confidence: float
    center_offset: float  # Offset from image center (-1 to 1)
    curvature: float  # For curves: positive = right, negative = left
    recommended_speed: float  # Speed multiplier (0.0 to 1.0)
    feature_info: Dict  # Additional feature-specific data


class RoadFeatureDetector:
    """
    Analyzes Canny edges to detect road features beyond straight lanes.

    Detection methods:
    - Intersections: Edge density in multiple directions
    - Roundabouts: Hough circles / arc detection
    - Curves: Contour fitting, polynomial analysis
    - Lane width: Edge boundary tracking
    """

    def __init__(self, img_width: int = 640, img_height: int = 480):
        self.img_width = img_width
        self.img_height = img_height

        # Detection thresholds (tunable)
        self.intersection_density_threshold = 0.25  # Raised to reduce false positives
        self.roundabout_min_radius = 50
        self.roundabout_max_radius = 200
        self.curve_min_contour_points = 20
        self.parking_aspect_ratio_threshold = 2.5

        # Feature toggles (disable noisy detectors)
        self.enable_roundabout = False  # Too many false positives
        self.enable_curve = False       # Use lane curvature instead
        self.enable_parking = False     # Not needed for competition

        # History for temporal smoothing
        self.detection_history: List[RoadType] = []
        self.max_history = 5

    def detect(self, edges: np.ndarray,
               original_image: Optional[np.ndarray] = None) -> RoadFeature:
        """
        Main detection pipeline. Analyzes edge image to determine road type.

        Args:
            edges: Canny edge image (grayscale, binary)
            original_image: Optional BGR image for additional analysis

        Returns:
            RoadFeature with detected road type, confidence, and metadata
        """
        h, w = edges.shape[:2]
        self.img_height = h
        self.img_width = w

        # Define analysis region (bottom portion of image = near road)
        roi_top = int(h * 0.45)
        roi = edges[roi_top:, :]

        # Run enabled detectors only
        candidates = []

        # Always run intersection and straight detection
        intersection_result = self._detect_intersection(roi)
        candidates.append(intersection_result)

        straight_result = self._detect_straight(roi)
        candidates.append(straight_result)

        # Optional detectors (disabled by default - too noisy)
        if self.enable_roundabout:
            roundabout_result = self._detect_roundabout(roi)
            candidates.append(roundabout_result)

        if self.enable_curve:
            curve_result = self._detect_curve(roi)
            candidates.append(curve_result)

        if self.enable_parking:
            parking_result = self._detect_parking(roi, original_image)
            candidates.append(parking_result)

        # Select highest confidence detection
        best = max(candidates, key=lambda x: x.confidence)

        # Apply temporal smoothing
        self.detection_history.append(best.road_type)
        if len(self.detection_history) > self.max_history:
            self.detection_history.pop(0)

        # If recent history is inconsistent, reduce confidence
        if len(self.detection_history) >= 3:
            recent = self.detection_history[-3:]
            if len(set(recent)) > 1:  # Mixed detections
                best = RoadFeature(
                    road_type=best.road_type,
                    confidence=best.confidence * 0.7,
                    center_offset=best.center_offset,
                    curvature=best.curvature,
                    recommended_speed=best.recommended_speed,
                    feature_info=best.feature_info
                )

        return best

    def _detect_intersection(self, roi: np.ndarray) -> RoadFeature:
        """
        Detect intersections by analyzing edge density in multiple sectors.
        Intersections show high edge activity in multiple directions.
        """
        h, w = roi.shape[:2]

        # Divide ROI into sectors: left, center, right, top-center
        sectors = {
            'left': roi[:, :w//3],
            'center': roi[:, w//3:2*w//3],
            'right': roi[:, 2*w//3:],
            'top': roi[:h//2, w//4:3*w//4],
        }

        # Calculate edge density in each sector
        densities = {}
        for name, sector in sectors.items():
            total_pixels = sector.size
            edge_pixels = np.count_nonzero(sector)
            densities[name] = edge_pixels / total_pixels if total_pixels > 0 else 0

        # Intersection signature: multiple sectors have high density
        high_density_count = sum(1 for d in densities.values()
                                  if d > self.intersection_density_threshold)

        # Also check for perpendicular lines using Hough
        lines = cv2.HoughLinesP(roi, 1, np.pi/180, 30,
                                minLineLength=30, maxLineGap=50)

        horizontal_lines = 0
        vertical_lines = 0

        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                if x2 - x1 == 0:
                    vertical_lines += 1
                    continue
                slope = abs((y2 - y1) / (x2 - x1))
                if slope < 0.3:  # Near horizontal
                    horizontal_lines += 1
                elif slope > 3:  # Near vertical
                    vertical_lines += 1

        # Intersection has both horizontal and vertical edges
        has_perpendicular = horizontal_lines >= 2 and vertical_lines >= 2

        # Calculate confidence
        confidence = 0.0
        if high_density_count >= 3:
            confidence = 0.4 + (high_density_count - 3) * 0.15
        if has_perpendicular:
            confidence += 0.3

        confidence = min(confidence, 0.95)

        return RoadFeature(
            road_type=RoadType.INTERSECTION,
            confidence=confidence,
            center_offset=0.0,  # Intersection typically centered
            curvature=0.0,
            recommended_speed=0.3,  # Slow down at intersections
            feature_info={
                'sector_densities': densities,
                'horizontal_lines': horizontal_lines,
                'vertical_lines': vertical_lines,
            }
        )

    def _detect_roundabout(self, roi: np.ndarray) -> RoadFeature:
        """
        Detect roundabouts using Hough circle detection and arc analysis.
        """
        h, w = roi.shape[:2]

        # Apply morphological operations to connect edge fragments
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        dilated = cv2.dilate(roi, kernel, iterations=1)

        # Detect circles
        circles = cv2.HoughCircles(
            dilated,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=50,
            param1=100,
            param2=30,
            minRadius=self.roundabout_min_radius,
            maxRadius=self.roundabout_max_radius
        )

        confidence = 0.0
        center_x = w // 2
        radius = 0

        if circles is not None:
            circles = np.uint16(np.around(circles))
            # Find the most prominent circle (likely the roundabout)
            best_circle = None
            best_score = 0

            for circle in circles[0]:
                cx, cy, r = circle
                # Prefer circles that are:
                # 1. Centered horizontally
                # 2. Have reasonable radius
                # 3. Are in upper portion (roundabout ahead)
                center_score = 1 - abs(cx - w/2) / (w/2)
                size_score = 1 - abs(r - 100) / 100  # Prefer ~100px radius
                position_score = 1 - cy / h  # Prefer circles higher up

                score = center_score * 0.4 + size_score * 0.3 + position_score * 0.3
                if score > best_score:
                    best_score = score
                    best_circle = circle

            if best_circle is not None:
                center_x, _, radius = best_circle
                confidence = min(0.6 + best_score * 0.35, 0.95)

        # Also check for curved contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)

        arc_count = 0
        for contour in contours:
            if len(contour) >= 10:  # Minimum points for arc
                # Fit ellipse if enough points
                if len(contour) >= 5:
                    try:
                        ellipse = cv2.fitEllipse(contour)
                        # Check if it's a reasonable arc (not too elongated)
                        (_, _), (ma, MA), _ = ellipse
                        if MA > 0 and 0.3 < ma/MA < 1.0:
                            arc_count += 1
                    except cv2.error:
                        pass

        if arc_count >= 2:
            confidence = max(confidence, 0.4 + arc_count * 0.1)

        center_offset = (center_x - w/2) / (w/2) if w > 0 else 0

        return RoadFeature(
            road_type=RoadType.ROUNDABOUT,
            confidence=confidence,
            center_offset=center_offset,
            curvature=0.0,  # Roundabout requires full navigation logic
            recommended_speed=0.25,  # Very slow for roundabouts
            feature_info={
                'radius': int(radius),
                'arc_count': arc_count,
                'circles_found': len(circles[0]) if circles is not None else 0,
            }
        )

    def _detect_curve(self, roi: np.ndarray) -> RoadFeature:
        """
        Detect curves by analyzing contour shapes and fitting polynomials.
        """
        h, w = roi.shape[:2]

        # Find contours
        contours, _ = cv2.findContours(roi, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return RoadFeature(
                road_type=RoadType.CURVE_LEFT,
                confidence=0.0,
                center_offset=0.0,
                curvature=0.0,
                recommended_speed=1.0,
                feature_info={}
            )

        # Find the largest contour (likely the road edge)
        largest_contour = max(contours, key=cv2.contourArea)

        if len(largest_contour) < self.curve_min_contour_points:
            return RoadFeature(
                road_type=RoadType.CURVE_LEFT,
                confidence=0.1,
                center_offset=0.0,
                curvature=0.0,
                recommended_speed=1.0,
                feature_info={}
            )

        # Fit polynomial to contour points
        points = largest_contour.reshape(-1, 2)
        x_coords = points[:, 0]
        y_coords = points[:, 1]

        # Sort by y (top to bottom)
        sort_idx = np.argsort(y_coords)
        x_sorted = x_coords[sort_idx]
        y_sorted = y_coords[sort_idx]

        # Fit 2nd degree polynomial: x = ay^2 + by + c
        try:
            coeffs = np.polyfit(y_sorted, x_sorted, 2)
            a, b, c = coeffs

            # Curvature is determined by 'a' coefficient
            # Positive a = curves right, Negative a = curves left
            curvature = a * 1000  # Scale for usability

            # Calculate curve confidence based on fit quality
            x_fitted = np.polyval(coeffs, y_sorted)
            residuals = x_sorted - x_fitted
            fit_error = np.std(residuals) / w

            # Good fit = low error
            fit_quality = max(0, 1 - fit_error * 10)

            # Only confident if there's actual curvature
            curvature_magnitude = abs(curvature)
            is_curved = curvature_magnitude > 0.5

            confidence = fit_quality * 0.6 if is_curved else 0.0

            # Determine curve direction
            if curvature > 0.5:
                road_type = RoadType.CURVE_RIGHT
            elif curvature < -0.5:
                road_type = RoadType.CURVE_LEFT
            else:
                road_type = RoadType.STRAIGHT
                confidence = 0.0  # Not actually a curve

            # Speed recommendation based on curvature
            speed_mult = max(0.4, 1.0 - curvature_magnitude * 0.1)

            return RoadFeature(
                road_type=road_type,
                confidence=confidence,
                center_offset=(c - w/2) / (w/2),  # Where curve starts
                curvature=curvature,
                recommended_speed=speed_mult,
                feature_info={
                    'polynomial_coeffs': coeffs.tolist(),
                    'fit_error': fit_error,
                    'contour_points': len(points),
                }
            )

        except (np.RankWarning, np.linalg.LinAlgError):
            return RoadFeature(
                road_type=RoadType.UNKNOWN,
                confidence=0.0,
                center_offset=0.0,
                curvature=0.0,
                recommended_speed=1.0,
                feature_info={}
            )

    def _detect_parking(self, roi: np.ndarray,
                        original_image: Optional[np.ndarray] = None) -> RoadFeature:
        """
        Detect parking areas by looking for rectangular patterns
        and characteristic markings.
        """
        h, w = roi.shape[:2]

        # Find contours
        contours, _ = cv2.findContours(roi, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)

        parking_candidates = []

        for contour in contours:
            # Approximate contour to polygon
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            # Parking spots are typically rectangular (4 corners)
            if len(approx) == 4:
                # Check aspect ratio
                x, y, bw, bh = cv2.boundingRect(approx)
                if bh > 0:
                    aspect_ratio = bw / bh
                    # Parking spots are wider than tall
                    if aspect_ratio > self.parking_aspect_ratio_threshold:
                        parking_candidates.append({
                            'bbox': (x, y, bw, bh),
                            'aspect_ratio': aspect_ratio,
                            'area': bw * bh,
                        })

        # Also look for parallel lines (parking space dividers)
        lines = cv2.HoughLinesP(roi, 1, np.pi/180, 30,
                                minLineLength=40, maxLineGap=20)

        parallel_groups = []
        if lines is not None and len(lines) >= 2:
            # Group lines by similar angle
            for i, line1 in enumerate(lines):
                x1, y1, x2, y2 = line1[0]
                if x2 - x1 == 0:
                    angle1 = 90
                else:
                    angle1 = np.degrees(np.arctan((y2-y1)/(x2-x1)))

                for line2 in lines[i+1:]:
                    x3, y3, x4, y4 = line2[0]
                    if x4 - x3 == 0:
                        angle2 = 90
                    else:
                        angle2 = np.degrees(np.arctan((y4-y3)/(x4-x3)))

                    # Lines are parallel if angles are similar
                    if abs(angle1 - angle2) < 10:
                        parallel_groups.append((line1, line2))

        # Calculate confidence
        confidence = 0.0
        if len(parking_candidates) >= 2:
            confidence = 0.4 + min(len(parking_candidates) * 0.1, 0.3)
        if len(parallel_groups) >= 3:
            confidence = max(confidence, 0.3 + min(len(parallel_groups) * 0.1, 0.4))

        return RoadFeature(
            road_type=RoadType.PARKING,
            confidence=confidence,
            center_offset=0.0,
            curvature=0.0,
            recommended_speed=0.2,  # Very slow in parking areas
            feature_info={
                'parking_candidates': len(parking_candidates),
                'parallel_line_groups': len(parallel_groups),
            }
        )

    def _detect_straight(self, roi: np.ndarray) -> RoadFeature:
        """
        Detect straight road by looking for consistent parallel lane lines.
        This is the default/fallback detection.
        """
        h, w = roi.shape[:2]

        # Detect lines
        lines = cv2.HoughLinesP(roi, 1, np.pi/180, 40,
                                minLineLength=50, maxLineGap=100)

        if lines is None or len(lines) < 2:
            # No clear lines, low confidence for any type
            return RoadFeature(
                road_type=RoadType.STRAIGHT,
                confidence=0.3,  # Default assumption
                center_offset=0.0,
                curvature=0.0,
                recommended_speed=1.0,
                feature_info={'lines_found': 0}
            )

        # Analyze line angles
        left_lines = []
        right_lines = []

        for line in lines:
            x1, y1, x2, y2 = line[0]
            if x2 - x1 == 0:
                continue
            slope = (y2 - y1) / (x2 - x1)

            # Filter near-horizontal lines
            if abs(slope) < 0.3:
                continue

            mid_x = (x1 + x2) / 2
            if slope < 0 and mid_x < w * 0.5:
                left_lines.append((x1, y1, x2, y2, slope))
            elif slope > 0 and mid_x > w * 0.5:
                right_lines.append((x1, y1, x2, y2, slope))

        # Straight road has consistent slopes on each side
        confidence = 0.0
        center_offset = 0.0

        if left_lines and right_lines:
            # Check slope consistency
            left_slopes = [s for _, _, _, _, s in left_lines]
            right_slopes = [s for _, _, _, _, s in right_lines]

            left_var = np.var(left_slopes) if len(left_slopes) > 1 else 0
            right_var = np.var(right_slopes) if len(right_slopes) > 1 else 0

            # Low variance = consistent = straight road
            consistency = 1 - min((left_var + right_var) * 5, 1)
            confidence = 0.4 + consistency * 0.5

            # Calculate center offset
            left_x_avg = np.mean([x1 for x1, _, _, _, _ in left_lines])
            right_x_avg = np.mean([x1 for x1, _, _, _, _ in right_lines])
            lane_center = (left_x_avg + right_x_avg) / 2
            center_offset = (lane_center - w/2) / (w/2)

        elif left_lines or right_lines:
            confidence = 0.3  # Only one lane visible

        return RoadFeature(
            road_type=RoadType.STRAIGHT,
            confidence=confidence,
            center_offset=center_offset,
            curvature=0.0,
            recommended_speed=1.0,
            feature_info={
                'left_lines': len(left_lines),
                'right_lines': len(right_lines),
            }
        )

    def visualize(self, edges: np.ndarray, feature: RoadFeature) -> np.ndarray:
        """
        Create visualization of detected features.

        Args:
            edges: Original edge image
            feature: Detected road feature

        Returns:
            BGR visualization image
        """
        h, w = edges.shape[:2]

        # Create color visualization
        vis = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

        # Color code by road type
        colors = {
            RoadType.STRAIGHT: (0, 255, 0),      # Green
            RoadType.CURVE_LEFT: (255, 165, 0),  # Orange
            RoadType.CURVE_RIGHT: (0, 165, 255), # Orange-ish
            RoadType.INTERSECTION: (0, 0, 255),  # Red
            RoadType.ROUNDABOUT: (255, 0, 255),  # Magenta
            RoadType.PARKING: (255, 255, 0),     # Cyan
            RoadType.UNKNOWN: (128, 128, 128),   # Gray
        }

        color = colors.get(feature.road_type, (255, 255, 255))

        # Draw feature type label
        label = f"{feature.road_type.name}: {feature.confidence:.0%}"
        cv2.putText(vis, label, (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        # Draw speed recommendation
        speed_label = f"Speed: {feature.recommended_speed:.0%}"
        cv2.putText(vis, speed_label, (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        # Draw center offset indicator
        center_x = int(w/2 + feature.center_offset * w/4)
        cv2.arrowedLine(vis, (w//2, h-20), (center_x, h-20), color, 2)

        # Feature-specific visualizations
        if feature.road_type == RoadType.ROUNDABOUT:
            radius = feature.feature_info.get('radius', 50)
            if radius > 0:
                cv2.circle(vis, (w//2, h//3), radius, color, 2)

        elif feature.road_type in (RoadType.CURVE_LEFT, RoadType.CURVE_RIGHT):
            # Draw curvature indicator
            curv = feature.curvature
            curv_label = f"Curv: {curv:.2f}"
            cv2.putText(vis, curv_label, (10, 75),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        return vis


class NavigationAdvisor:
    """
    Provides navigation advice based on detected road features.
    Integrates with lane following to adjust behavior.
    """

    def __init__(self):
        self.current_feature: Optional[RoadFeature] = None
        self.feature_detector = RoadFeatureDetector()

    def update(self, edges: np.ndarray,
               original_image: Optional[np.ndarray] = None) -> RoadFeature:
        """Update detection with new frame."""
        self.current_feature = self.feature_detector.detect(edges, original_image)
        return self.current_feature

    def get_speed_multiplier(self) -> float:
        """Get recommended speed multiplier based on current road type."""
        if self.current_feature is None:
            return 1.0
        return self.current_feature.recommended_speed

    def get_steering_adjustment(self, base_steering: float) -> float:
        """
        Adjust steering based on detected features.

        Args:
            base_steering: Steering from lane follower (-1 to 1)

        Returns:
            Adjusted steering value
        """
        if self.current_feature is None:
            return base_steering

        feature = self.current_feature

        # For curves, blend in curvature-based steering
        if feature.road_type in (RoadType.CURVE_LEFT, RoadType.CURVE_RIGHT):
            curvature_steering = np.clip(feature.curvature * 0.1, -0.3, 0.3)
            # Blend: 70% lane following, 30% curvature
            return base_steering * 0.7 + curvature_steering * 0.3

        # For roundabouts, use center offset more heavily
        if feature.road_type == RoadType.ROUNDABOUT:
            # Follow the roundabout edge
            offset_steering = feature.center_offset * 0.3
            return base_steering * 0.5 + offset_steering * 0.5

        # For intersections, be more cautious with steering
        if feature.road_type == RoadType.INTERSECTION:
            return base_steering * 0.5  # Reduce steering sensitivity

        return base_steering

    def should_stop(self) -> bool:
        """Check if the car should stop (e.g., at intersection for decision)."""
        if self.current_feature is None:
            return False

        # High confidence intersection might require stop
        if (self.current_feature.road_type == RoadType.INTERSECTION and
            self.current_feature.confidence > 0.7):
            return True

        return False

    def get_status_text(self) -> str:
        """Get human-readable status for display."""
        if self.current_feature is None:
            return "No detection"

        f = self.current_feature
        return f"{f.road_type.name} ({f.confidence:.0%}) | Speed: {f.recommended_speed:.0%}"


# Convenience function for quick testing
def analyze_frame(image: np.ndarray) -> Tuple[RoadFeature, np.ndarray]:
    """
    Analyze a single frame and return detection results with visualization.

    Args:
        image: BGR input image

    Returns:
        Tuple of (RoadFeature, visualization_image)
    """
    # Preprocess
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)

    # Detect
    detector = RoadFeatureDetector()
    feature = detector.detect(edges, image)

    # Visualize
    vis = detector.visualize(edges, feature)

    return feature, vis


if __name__ == '__main__':
    # Test with a sample image if run directly
    print("Road Feature Detector - ACC 2026")
    print("="*50)
    print("RoadType enum values:")
    for rt in RoadType:
        print(f"  - {rt.name}")
    print("\nImport this module and use RoadFeatureDetector or NavigationAdvisor")
    print("Example:")
    print("  from road_features import NavigationAdvisor")
    print("  advisor = NavigationAdvisor()")
    print("  feature = advisor.update(edges_image)")
    print("  speed_mult = advisor.get_speed_multiplier()")
