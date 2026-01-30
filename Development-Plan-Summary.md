# 🚀 Development Plan Summary

> **Goal**: Submit a competitive self-driving algorithm for the ACC 2026 competition
> **Deadline**: February 27, 2026 (Virtual Stage)

---

## 📊 Timeline Overview

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| **1. Setup** | Week 1 | Environment ready, basic driving |
| **2. Perception** | Week 2 | Lane detection, sign recognition |
| **3. Navigation** | Week 2-3 | Path planning, localization |
| **4. Integration** | Week 3 | Complete taxi scenario |
| **5. Video & Submission** | Week 4 | 3-min video, GitHub repo |

---

## 🎯 Key Deliverables

### Virtual Stage Submission
- [ ] **GitHub Repository** - Working self-driving algorithm
- [ ] **YouTube Video** - 3-minute demonstration
- [ ] **Detailed Scenario** - Pickup → Drop-off → Return

### Core Algorithm Components
1. **Perception** - Camera/LiDAR processing
2. **Decision Making** - Traffic rules, route selection
3. **Control** - Lane following, stopping
4. **Navigation** - Path planning, localization

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                    PERCEPTION                        │
│  [Camera] [LiDAR] [IMU] → Feature Extraction        │
└─────────────────────┬───────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────┐
│                  INTERPRETATION                      │
│  Lane Detection │ Sign Recognition │ Obstacle Det.  │
└─────────────────────┬───────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────┐
│                 PATH PLANNING                        │
│  Localization │ Route Planning │ Path Adjustment    │
└─────────────────────┬───────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────┐
│                    CONTROL                           │
│  Steering │ Throttle │ Braking │ LED Control        │
└─────────────────────────────────────────────────────┘
```

---

## 📋 Quick Checklist

### Week 1: Setup ✅
- [ ] **🔴 DECIDE: Tech stack** (Python-only vs ROS vs MATLAB)
- [ ] Set up development environment
- [ ] Install QLabs and verify connection
- [ ] Run basic QCar 2 control examples
- [ ] Understand sensor APIs

### Week 2: Perception & Control
- [ ] Implement lane detection
- [ ] Implement traffic sign/light recognition
- [ ] Basic lane-following controller
- [ ] Stop at traffic controls

### Week 3: Navigation & Integration
- [ ] Implement localization system
- [ ] Path planning to coordinates
- [ ] LED state machine
- [ ] Complete taxi scenario flow

### Week 4: Polish & Submit
- [ ] Test complex scenarios
- [ ] Record 3-minute video
- [ ] Prepare GitHub repository
- [ ] Submit before Feb 27

---

## 🔗 Related Documents

- [[Development-Plan]] - Detailed development plan
- [[Overview]] - Competition overview
- [[Virtual-Stage-Guide]] - Submission requirements
- [[Core-Principles]] - Algorithm requirements
- [[Detailed-Scenario]] - Scenario to implement

---

## ⚡ Critical Success Factors

1. **Demonstrate all 4 core principles** in video
2. **Complete the detailed scenario** cleanly
3. **Explain your algorithm** clearly
4. **Stay in lanes** and obey traffic rules
5. **Correct LED colors** at each phase
