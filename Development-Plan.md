# 🚀 Development Plan

> **Goal**: Create a winning self-driving taxi algorithm for ACC 2026
> **Virtual Stage Deadline**: February 27, 2026
> **Time Remaining**: ~4 weeks

---

## 📅 Detailed Timeline

### Phase 1: Environment Setup (Days 1-5)
> **Objective**: Get development environment running with basic QCar control

#### Tasks
| Task | Priority | Est. Time | Status |
|------|----------|-----------|--------|
| Install Docker & ROS 2 environment | 🔴 High | 2h | [ ] |
| Set up QLabs and verify license | 🔴 High | 1h | [ ] |
| Clone ROS technical resources | 🔴 High | 30m | [ ] |
| Run Virtual ROS Software Setup | 🔴 High | 2h | [ ] |
| Test basic QCar 2 movement | 🔴 High | 2h | [ ] |
| Understand sensor data streams | 🟡 Med | 3h | [ ] |
| Document API usage notes | 🟢 Low | 1h | [ ] |

#### Resources
- [[ROS-Setup]] - ROS development guide
- [[QLabs-Setup]] - QLabs environment
- [[Software-Requirements]] - Software stack

#### Deliverables
- [ ] Working development environment
- [ ] QCar 2 driving manually in QLabs
- [ ] Sensor data visualization working

---

### Phase 2: Perception System (Days 6-12)
> **Objective**: Implement reliable perception for lanes, signs, and obstacles

#### 2.1 Camera Processing

| Task | Priority | Est. Time | Status |
|------|----------|-----------|--------|
| Camera image acquisition pipeline | 🔴 High | 2h | [ ] |
| Lane detection algorithm | 🔴 High | 6h | [ ] |
| Lane centering calculation | 🔴 High | 3h | [ ] |
| Traffic light detection | 🔴 High | 4h | [ ] |
| Traffic light state classification | 🔴 High | 3h | [ ] |
| Stop sign detection | 🟡 Med | 3h | [ ] |
| Pedestrian detection | 🟡 Med | 4h | [ ] |

##### Lane Detection Approaches
```python
# Option 1: Classical CV (OpenCV)
# - Canny edge detection
# - Hough transform for line detection
# - Polynomial fitting for curves

# Option 2: Deep Learning
# - Pre-trained lane detection model
# - Fine-tune on QLabs imagery

# Recommended: Start with classical, add DL if time permits
```

#### 2.2 LiDAR Processing

| Task | Priority | Est. Time | Status |
|------|----------|-----------|--------|
| LiDAR data acquisition | 🟡 Med | 2h | [ ] |
| Point cloud preprocessing | 🟡 Med | 2h | [ ] |
| Obstacle detection | 🟡 Med | 4h | [ ] |
| Distance-to-obstacle calculation | 🟡 Med | 2h | [ ] |

#### 2.3 Sensor Fusion

| Task | Priority | Est. Time | Status |
|------|----------|-----------|--------|
| Camera-LiDAR calibration | 🟡 Med | 3h | [ ] |
| Fused obstacle representation | 🟡 Med | 3h | [ ] |

#### Deliverables
- [ ] Reliable lane detection (>90% accuracy)
- [ ] Traffic light/sign recognition
- [ ] Obstacle detection and distance estimation

---

### Phase 3: Localization & Path Planning (Days 10-16)
> **Objective**: Know where we are and plan routes to destinations

#### 3.1 Localization

| Task | Priority | Est. Time | Status |
|------|----------|-----------|--------|
| Odometry integration | 🔴 High | 2h | [ ] |
| IMU data fusion | 🔴 High | 2h | [ ] |
| Map creation/loading | 🔴 High | 3h | [ ] |
| Position estimation (EKF/particle filter) | 🔴 High | 6h | [ ] |
| LiDAR-based SLAM (optional) | 🟢 Low | 8h | [ ] |

##### Localization Strategy
```
Primary: Odometry + IMU fusion
Enhancement: LiDAR matching against known map
Backup: Camera-based landmark detection
```

#### 3.2 Path Planning

| Task | Priority | Est. Time | Status |
|------|----------|-----------|--------|
| Waypoint graph of Quanser City | 🔴 High | 4h | [ ] |
| A* or Dijkstra path search | 🔴 High | 3h | [ ] |
| Path-to-trajectory conversion | 🔴 High | 3h | [ ] |
| Dynamic replanning for obstacles | 🟡 Med | 4h | [ ] |
| Nav2 integration (if using ROS) | 🟡 Med | 4h | [ ] |

##### Key Coordinates to Map
| Location | Coordinates | Purpose |
|----------|-------------|---------|
| Taxi Hub | [TBD] | Start/End |
| Pickup Point 1 | [0.125, 4.395] | Scenario pickup |
| Drop-off Point 1 | [-0.905, 0.800] | Scenario dropoff |
| Intersections | [TBD] | Decision points |

See [[Coordinate-System]] for coordinate reference.

#### Deliverables
- [ ] Reliable position estimation (<10cm error)
- [ ] Path planning to any coordinate
- [ ] Intersection navigation logic

---

### Phase 4: Control System (Days 8-14)
> **Objective**: Execute plans accurately with smooth driving

#### 4.1 Motion Control

| Task | Priority | Est. Time | Status |
|------|----------|-----------|--------|
| Steering controller (PID/Pure Pursuit) | 🔴 High | 4h | [ ] |
| Speed controller | 🔴 High | 3h | [ ] |
| Lane following behavior | 🔴 High | 4h | [ ] |
| Stop execution at coordinates | 🔴 High | 2h | [ ] |
| Stop at traffic controls | 🔴 High | 3h | [ ] |

##### Control Architecture
```python
class VehicleController:
    def __init__(self):
        self.steering_pid = PIDController(kp, ki, kd)
        self.speed_controller = SpeedController()
    
    def lane_follow(self, lane_center_offset):
        steering = self.steering_pid.compute(lane_center_offset)
        return steering
    
    def navigate_to(self, target_coordinate):
        # Pure pursuit or Stanley controller
        pass
```

#### 4.2 LED Control

| Task | Priority | Est. Time | Status |
|------|----------|-----------|--------|
| LED API integration | 🔴 High | 1h | [ ] |
| State machine for LED colors | 🔴 High | 2h | [ ] |
| Automatic LED transitions | 🔴 High | 1h | [ ] |

##### LED State Machine
See [[LED-Protocol]] for complete reference.

```python
class LEDStateMachine:
    WAITING = "MAGENTA"
    EN_ROUTE = "GREEN"
    PICKUP = "BLUE"
    STOP = "RED"
    DROPOFF = "ORANGE"
```

#### Deliverables
- [ ] Smooth lane following (<5cm deviation)
- [ ] Accurate stops at waypoints
- [ ] Correct LED colors at all phases

---

### Phase 5: Integration & Taxi Scenario (Days 14-20)
> **Objective**: Complete the full taxi scenario end-to-end

#### 5.1 Scenario Implementation

| Task | Priority | Est. Time | Status |
|------|----------|-----------|--------|
| State machine for taxi ride | 🔴 High | 4h | [ ] |
| Pickup sequence implementation | 🔴 High | 2h | [ ] |
| Dropoff sequence implementation | 🔴 High | 2h | [ ] |
| Return to hub sequence | 🔴 High | 2h | [ ] |
| Full scenario testing | 🔴 High | 4h | [ ] |

##### Taxi State Machine
```python
class TaxiStateMachine:
    states = [
        "WAITING_AT_HUB",      # Magenta LED
        "EN_ROUTE_TO_PICKUP",  # Green LED
        "AT_PICKUP",           # Blue LED, full stop
        "EN_ROUTE_TO_DROPOFF", # Green LED
        "AT_DROPOFF",          # Orange LED, full stop
        "RETURNING_TO_HUB",    # Green LED
        "RIDE_COMPLETE"        # Magenta LED
    ]
```

See [[Detailed-Scenario]] for the complete flow.

#### 5.2 Edge Cases & Robustness

| Task | Priority | Est. Time | Status |
|------|----------|-----------|--------|
| Traffic light handling | 🔴 High | 3h | [ ] |
| Obstacle avoidance scenarios | 🟡 Med | 4h | [ ] |
| Recovery from lost localization | 🟡 Med | 3h | [ ] |
| Pedestrian yielding | 🟡 Med | 3h | [ ] |

#### Deliverables
- [ ] Complete scenario execution (Hub → Pickup → Dropoff → Hub)
- [ ] All LED colors correct
- [ ] No lane violations
- [ ] Smooth, confident driving

---

### Phase 6: Video Production & Submission (Days 20-28)
> **Objective**: Create compelling 3-minute video and submit

#### 6.1 Video Content

| Task | Priority | Est. Time | Status |
|------|----------|-----------|--------|
| Script/storyboard | 🔴 High | 2h | [ ] |
| Record basic scenario run | 🔴 High | 2h | [ ] |
| Record complex scenario (traffic) | 🟡 Med | 3h | [ ] |
| Voiceover explaining principles | 🔴 High | 2h | [ ] |
| Video editing | 🔴 High | 4h | [ ] |
| Add overlays/annotations | 🟡 Med | 2h | [ ] |

##### Video Structure (3 minutes)
| Section | Duration | Content |
|---------|----------|---------|
| Intro | 15s | Team, challenge overview |
| Data Collection | 30s | Sensor visualization |
| Interpretation | 30s | Object detection demos |
| Control | 30s | Lane following, stops |
| Navigation | 30s | Path planning demo |
| Full Scenario | 45s | Complete taxi ride |
| Outro | 10s | Summary, contact |

See [[Virtual-Stage-Guide]] for video requirements.

#### 6.2 Code Preparation

| Task | Priority | Est. Time | Status |
|------|----------|-----------|--------|
| Clean up repository | 🔴 High | 2h | [ ] |
| Add documentation/README | 🔴 High | 2h | [ ] |
| Verify no qvl usage for control | 🔴 High | 1h | [ ] |
| License and attributions | 🟡 Med | 30m | [ ] |

#### 6.3 Submission

| Task | Priority | Est. Time | Status |
|------|----------|-----------|--------|
| Upload video to YouTube | 🔴 High | 30m | [ ] |
| Verify GitHub repo is public | 🔴 High | 15m | [ ] |
| Submit via official form | 🔴 High | 15m | [ ] |
| Confirm submission received | 🔴 High | 5m | [ ] |

#### Deliverables
- [ ] 3-minute YouTube video (unlisted or public)
- [ ] Public GitHub repository
- [ ] Submission confirmed before Feb 27

---

## 🏗️ Technical Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────┐
│                        MAIN LOOP                              │
└──────────────────────────┬───────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│   PERCEPTION  │  │  PLANNING     │  │   CONTROL     │
├───────────────┤  ├───────────────┤  ├───────────────┤
│ Camera Node   │  │ Localization  │  │ Steering Ctrl │
│ LiDAR Node    │  │ Path Planning │  │ Speed Ctrl    │
│ Object Detect │  │ State Machine │  │ LED Control   │
└───────────────┘  └───────────────┘  └───────────────┘
```

### ROS 2 Node Structure

```
/qcar2_driver           # Low-level hardware interface
    ├── /camera/image_raw
    ├── /lidar/points
    ├── /imu/data
    └── /odom

/perception_node        # Sensor processing
    ├── /lanes/detected
    ├── /objects/detected
    └── /traffic_light/state

/localization_node      # Position estimation
    └── /pose/estimated

/planning_node          # High-level decisions
    ├── /path/global
    └── /path/local

/control_node           # Motion execution
    ├── /cmd_vel
    └── /led/state

/taxi_state_machine     # Scenario orchestration
    └── /taxi/state
```

---

## 🧪 Testing Strategy

### Unit Tests
- [ ] Lane detection accuracy on test images
- [ ] Traffic light classifier accuracy
- [ ] Path planning correctness
- [ ] Controller response characteristics

### Integration Tests
- [ ] Perception → Control loop
- [ ] Planning → Control loop
- [ ] Full state machine transitions

### Scenario Tests
- [ ] Basic route following
- [ ] Traffic light response
- [ ] Complete taxi scenario
- [ ] Edge cases (obstacles, pedestrians)

### Metrics to Track
| Metric | Target | Current |
|--------|--------|---------|
| Lane following error | <5cm | - |
| Stop position error | <10cm | - |
| Traffic light response | <1s | - |
| Full scenario success | >95% | - |

---

## 📁 Repository Structure

```
acc2026-self-driving/
├── README.md
├── docs/
│   └── architecture.md
├── src/
│   ├── perception/
│   │   ├── lane_detection.py
│   │   ├── object_detection.py
│   │   └── traffic_light.py
│   ├── planning/
│   │   ├── localization.py
│   │   ├── path_planner.py
│   │   └── waypoint_graph.py
│   ├── control/
│   │   ├── steering_controller.py
│   │   ├── speed_controller.py
│   │   └── led_controller.py
│   └── taxi/
│       ├── state_machine.py
│       └── scenario_runner.py
├── config/
│   ├── waypoints.yaml
│   └── parameters.yaml
├── launch/
│   └── taxi_demo.launch.py
└── test/
    └── ...
```

---

## 🎯 Success Criteria

### Minimum Viable Submission
- [ ] Completes basic scenario (pickup → dropoff → hub)
- [ ] Stays in lanes (mostly)
- [ ] Correct LED colors
- [ ] Video explains core concepts

### Competitive Submission
- [ ] Smooth, confident driving
- [ ] Handles traffic lights/signs
- [ ] Clear algorithm explanations with visualizations
- [ ] Complex scenario demonstrations

### Winning Submission
- [ ] Flawless execution
- [ ] Handles edge cases gracefully
- [ ] Professional video production
- [ ] Novel/impressive technical approach

---

## 🔗 Related Documents

- [[Development-Plan-Summary]] - Quick overview
- [[Overview]] - Competition rules
- [[Virtual-Stage-Guide]] - Submission requirements
- [[Core-Principles]] - What judges evaluate
- [[Detailed-Scenario]] - Scenario to implement
- [[LED-Protocol]] - LED color reference
- [[Coordinate-System]] - Navigation coordinates

---

## 📝 Notes & Decisions Log

### Technical Decisions
| Date | Decision | Rationale |
|------|----------|-----------|
| | Use ROS 2 | Official support from Quanser |
| | Classical CV for lanes | Faster development, simpler debugging |
| | Pure Pursuit for steering | Proven technique for path following |

### Risks & Mitigations
| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Time constraints | High | High | Prioritize core functionality |
| QLabs bugs | Med | Med | Report issues, work around |
| Complex navigation | High | Med | Start with waypoint-following |
| Poor video quality | Med | Low | Script in advance, practice |

---

## 🔄 Daily Standup Template

### What was completed yesterday?
- 

### What is planned for today?
- 

### Any blockers?
- 

### Current phase: [ ] Setup [ ] Perception [ ] Navigation [ ] Control [ ] Integration [ ] Video
