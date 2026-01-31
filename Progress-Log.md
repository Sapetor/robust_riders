# 📋 Progress Log

> Tracking accomplishments and setup milestones for ACC 2026

---

## ✅ Completed Tasks

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

#### Scripts Created
| Script | Purpose |
|--------|---------|
| `test_qlabs.py` | Basic connection test |
| `test_spawn.py` | QCar spawn verification |
| `demo_drive.py` | Arrow key velocity control |
| `camera_feed.py` | Live camera display |
| `lane_detection.py` | Lane detection visualization |
| `lane_following.py` | Autonomous lane following |
| `drive_with_lanes.py` | Manual driving + lane view |
| `setup_competition.py` | Competition scenario (Open World) |

---

## 📚 Key Learnings

> [!IMPORTANT]
> **Use Cityscape workspace** - QCar spawning works in Cityscape, NOT Plane/Open World

- Competition flooring script is for **Open World** but needs version alignment
- Velocity control requires continuous key presses (hold to accelerate)
- Speed persists until changed (momentum-based)
- **Lane detection**: Basic Canny/Hough is fragile - need HSV filtering + perspective transform

---

## 🔄 In Progress

- [x] **Tech stack decision** - Pure Python on Windows (port to pal/hal for submission)
- [ ] Improve lane detection (HSV filtering, bird's eye view)
- [ ] Sign/traffic light detection
- [ ] Path planning (Taxi Hub → Pickup → Dropoff)
- [ ] Port to pal/hal for final submission

---

## 📝 Environment Details

| Component | Version/Path |
|-----------|--------------|
| **Python** | 3.13.1 (control2 conda env) |
| **QLabs** | Quanser Interactive Labs |
| **SDK** | C:\Program Files\Quanser\Quanser SDK\ |
| **Workspace** | **Cityscape** (required!) |

---

## 🔗 Related Documents

- [[Development-Plan]] - Full development plan
- [[Development-Plan-Summary]] - Quick overview
- [[External-Resources]] - External links and resources
- [[Detailed-Scenario]] - Competition scenario details

