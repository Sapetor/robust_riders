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

#### Scripts Created
| Script | Purpose |
|--------|---------|
| `test_qlabs.py` | Basic connection test |
| `test_spawn.py` | QCar spawn verification |
| `demo_drive.py` | Arrow key velocity control |
| `setup_competition.py` | Competition scenario (for Open World) |

---

## 📚 Key Learnings

> [!IMPORTANT]
> **Use Cityscape workspace** - QCar spawning works in Cityscape, NOT Plane/Open World

- Competition flooring script is for **Open World** but needs version alignment
- Velocity control requires continuous key presses (hold to accelerate)
- Speed persists until changed (momentum-based)

---

## 🔄 In Progress

- [ ] Tech stack decision (Python-only vs ROS)
- [ ] Competition scenario in Cityscape
- [ ] Camera feed access
- [ ] Lane detection

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
- [[Detailed-Scenario]] - Competition scenario details

