# 📋 Progress Log

> Tracking accomplishments and setup milestones for ACC 2026

---

## ✅ Completed Tasks

### January 31, 2026

#### Repository Cleanup
- [x] **Deleted 16 files** - Removed diagnostic scripts, test files, superseded code
- [x] **Updated .gitignore** - Added __pycache__, datasets/, models/, runs/, screenshots
- [x] **Updated README.md** - Current project structure and quick start guide
- [x] **Cleaned screenshots** - Removed debug screenshots from repo

#### YOLO Road Detection Setup
- [x] **ultralytics installed** - YOLOv8 framework ready
- [x] **capture_training_data.py** - Drive & label images (S/L/R/I/O keys)
- [x] **train_yolo.py** - Training pipeline for classification model
- [x] **yolo_road_detector.py** - YOLO-based detector (replaces classical CV)
- [ ] **Capture training images** - Need ~50+ images per class
- [ ] **Train model** - Will create models/road_features.pt

#### Road Feature Detection (Phase 3) - Classical CV (DISABLED)
- [x] **RoadFeatureDetector class** - Analyzes Canny edges for road infrastructure
- [x] **Integrated into hybrid_navigation.py** - Toggle with 'R' key
- [x] **DISABLED by default** - Classical CV too unreliable, replaced by YOLO approach
- [x] **RoadFeatureDetector class** - Analyzes Canny edges for road infrastructure
- [x] **RoadType enum** - STRAIGHT, CURVE_LEFT, CURVE_RIGHT, INTERSECTION, ROUNDABOUT, PARKING
- [x] **Intersection detection** - Multi-sector edge density + perpendicular line analysis
- [x] **Roundabout detection** - Hough circles + arc/ellipse fitting
- [x] **Curve detection** - Contour polynomial fitting with curvature estimation
- [x] **Parking detection** - Rectangular patterns + parallel line groups
- [x] **NavigationAdvisor class** - Integrates with lane following for adaptive behavior
- [x] **Speed recommendations** - Per-feature speed multipliers (slow at intersections)
- [x] **Steering adjustments** - Curvature-based steering blending
- [x] **Visualization** - Color-coded feature display with confidence scores
- [x] **Test script** - `test_road_features.py` for QLabs integration testing

#### Lane Detection & Following (COMPLETE)
- [x] **Hough line detection** - Canny edges + HoughLinesP for lane lines
- [x] **Left/right lane separation** - Slope-based classification
- [x] **Curvature estimation** - Lane width change + slope difference analysis
- [x] **PID steering controller** - Smooth steering with Kp=0.8, Ki=0.05, Kd=0.3
- [x] **Curvature-based speed** - Slower on curves, faster on straights
- [x] **Right edge prioritization** - Stay away from road boundary

#### Waypoint Navigation Enhancement
- [x] **PID waypoint steering** - Smoother waypoint approach (Kp=0.6, Ki=0.02, Kd=0.2)
- [x] **Path waypoints** - Intermediate waypoints for road curves (PATHS dict)
- [x] **Sequential path following** - Auto-advance through waypoints
- [x] **Hybrid navigation** - Lane following + waypoint fallback with hysteresis

#### Traffic Detection
- [x] **Traffic light detection** - HSV color detection in ROI
- [x] **Stop sign detection** - Red octagon shape detection
- [x] **Toggleable detection** - Press 'T' to enable/disable (reduces false positives)

#### State Machine & LED
- [x] **LED protocol compliance** - All colors verified correct
- [x] **Taxi state machine** - WAITING→EN_ROUTE→AT_PICKUP→EN_ROUTE→AT_DROPOFF→RETURNING

---

### January 30, 2026

#### Environment Setup
- [x] **Quanser Portal account** - Active with ACC 2026 competition access
- [x] **QLabs installed** - Quanser Interactive Labs running on Windows
- [x] **Quanser SDK installed** - v2024.10.17
- [x] **Python environment configured** - Using `control2` conda environment
- [x] **Quanser Python API** - Installed and working
- [x] **QVL library** - Installed and working
- [x] **OpenCV** - Installed for computer vision
- [x] **keyboard library** - Installed for real-time control

#### QLabs Verification
- [x] **QLabs connection** - Successfully connected via Python
- [x] **QCar 2 spawning** - Works in **Cityscape** workspace
- [x] **Velocity control** - `set_velocity_and_request_state()` working
- [x] **Arrow key driving** - Real-time control with `demo_drive.py`

#### Perception Development
- [x] **Camera feed** - Live camera access working (`camera_feed.py`)
- [x] **Lane detection** - Basic Canny/Hough implementation (`lane_detection.py`)
- [x] **Lane following** - Autonomous steering prototype (`lane_following.py`)

#### Research
- [x] **ACC 2025 resources** - Found official competition repo and examples
- [x] **Lane detection approaches** - Documented recommended methods
- [x] **External resources** - Created [[External-Resources]] reference page

#### Current Scripts
| Script | Purpose |
|--------|---------|
| `hybrid_navigation.py` | **Main navigation** - Use this! |
| `demo_drive.py` | Simple manual driving test |
| `camera_feed.py` | Camera testing utility |
| `lane_detection.py` | Basic lane detection (reference) |
| `lane_detection_v2.py` | Improved lane detection (reference) |
| `lane_following.py` | Lane following (reference) |
| `road_features.py` | Classical CV road features (disabled) |
| `capture_training_data.py` | YOLO training data capture |
| `train_yolo.py` | Train YOLO model |
| `yolo_road_detector.py` | YOLO-based detector |

---

## 📚 Key Learnings

> [!IMPORTANT]
> **Use PLANE workspace** - Competition environment spawns floor/walls in Plane

- **PLANE workspace** for competition environment (spawns floor, walls, signs)
- **Cityscape Lite** only for quick tests (pre-built city, no competition floor)
- Velocity control requires continuous key presses (hold to accelerate)
- Speed persists until changed (momentum-based)
- **Lane detection**: Basic Canny/Hough works, but classical CV for road features is unreliable
- **YOLO is better** for road feature classification - needs training data from competition floor

---

## 🔄 In Progress

- [x] **Tech stack decision** - Pure Python on Windows (port to pal/hal for submission)
- [x] **Lane detection** - Hough lines + PID steering (COMPLETE)
- [x] **Sign/traffic light detection** - HSV + shape detection (COMPLETE)
- [x] **Path planning** - Sequential waypoints with curves (COMPLETE)
- [ ] **YOLO road features** - Capture data, train model, integrate
- [ ] LiDAR obstacle detection
- [ ] Port to pal/hal for final submission
- [ ] Video production

---

## 📝 Environment Details

| Component | Version/Path |
|-----------|--------------|
| **Python** | 3.13.1 (control2 conda env) |
| **QLabs** | Quanser Interactive Labs |
| **SDK** | C:\Program Files\Quanser\Quanser SDK\ |
| **Workspace** | **PLANE** (for competition floor) |
| **YOLO** | ultralytics 8.4.9 |

---

## 🔗 Related Documents

- [[Development-Plan]] - Full development plan
- [[Development-Plan-Summary]] - Quick overview
- [[External-Resources]] - External links and resources
- [[Detailed-Scenario]] - Competition scenario details

