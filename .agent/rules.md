# 🤖 Agent Rules & Critical Information

> **Important rules and information that must not be forgotten during development**

---

## ⚠️ Competition Rules

### Library Restrictions

> [!CAUTION]
> **`qvl` library is ONLY for environment setup, NOT for vehicle control!**

| Allowed | Not Allowed |
|---------|-------------|
| Spawn flooring, walls, objects | Read cameras via `qvl` |
| Start RT Model | Control vehicle via `qvl` |
| Set up competition map | Get sensor data via `qvl` |

### For Final Submission
- Must use `pal`/`hal` libraries (requires Linux/Docker)
- Current Windows prototyping with `qvl` is for **development only**

---

## 🛠️ Development Decisions

### ✅ Tech Stack: Pure Python (No ROS)
- Decision Date: 2026-01-30
- Reason: Simpler setup, sufficient for Virtual Stage

### ✅ Platform: Windows Prototyping
- Decision Date: 2026-01-30
- Reason: Faster iteration, port to Docker for submission
- **Action Required**: Port to `pal`/`hal` before video submission

---

## 🗺️ Competition Coordinates

```
Taxi Hub:   [-1.205, -0.83]   (Starting position)
Pickup:     [0.125, 4.395]
Dropoff:    [-0.905, 0.800]
```

---

## 🎨 LED Color Sequence

| State | Color |
|-------|-------|
| Waiting | 🟣 Magenta |
| En Route | 🟢 Green |
| Pickup | 🔵 Blue |
| Drop-off | 🟠 Orange |

---

## 📋 Submission Checklist

- [ ] Lane keeping (no crossing lines)
- [ ] Stop at traffic controls
- [ ] Proper pickup/drop-off stops
- [ ] Correct LED colors at each phase
- [ ] Obstacle avoidance
- [ ] Uses `pal`/`hal` (NOT `qvl` for control)

---

## 🔗 Critical Links

- [ACC 2025 Competition Repo](https://github.com/quanser/ACC-Competition-2025)
- [Detailed Scenario](https://github.com/quanser/ACC-Competition-2025/blob/main/Detailed_Scenario.md)
- [hal/pal Guide](https://github.com/quanser/ACC-Competition-2025/blob/main/Software_Guides/Utilizing%20hal%20and%20pal.md)
