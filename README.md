# ACC 2026 Self-Driving Car Competition

Autonomous taxi navigation for the **American Control Conference 2026** Self-Driving Car Student Competition.

## Event Details

- **Event**: American Control Conference 2026
- **Location**: New Orleans, Louisiana, USA
- **Dates**: May 26-28, 2026
- **Organizer**: Quanser

## Quick Start

```bash
# Run in QLabs PLANE workspace
python hybrid_navigation.py
```

**Controls:**
- Arrow keys / WASD = Manual drive
- A = Toggle autonomous mode
- N = Next waypoint
- Q = Quit

## Project Structure

```
ACC2026/
├── hybrid_navigation.py    # Main navigation system (use this!)
├── demo_drive.py           # Simple manual driving test
├── camera_feed.py          # Camera testing utility
│
├── lane_detection.py       # Basic lane detection (reference)
├── lane_detection_v2.py    # Improved lane detection (reference)
├── lane_following.py       # Lane following (reference)
├── road_features.py        # Road feature detection (disabled)
│
├── capture_training_data.py # YOLO training data capture
├── train_yolo.py           # Train YOLO model
├── yolo_road_detector.py   # YOLO-based detection (future)
│
├── 01-Competition-Rules/   # Rules and structure
├── 02-Technical-Resources/ # Hardware/software guides
├── 03-Self-Driving-Principles/
├── 04-Scenario/            # Competition scenario details
├── 05-Competition-Day/     # Event preparation
│
├── Development-Plan.md     # Detailed development plan
├── Progress-Log.md         # Progress tracking
└── README.md               # This file
```

## Main Components

### hybrid_navigation.py

The main navigation system combining:
- **Waypoint navigation** - Drive to coordinates
- **Lane following** - PID steering from detected lanes
- **State machine** - Taxi operations (pickup/dropoff/hub)
- **LED protocol** - Competition-compliant status colors

### YOLO Road Detection (In Progress)

Training a YOLOv8 classifier for road features. See [[YOLO-Training]] for full guide.

1. `capture_training_data.py` - Capture & label images
2. `train_yolo.py` - Train the model
3. `yolo_road_detector.py` - Use trained model

## Development Status

See [[Progress-Log]] for detailed progress.

**Completed:**
- Lane detection with PID steering
- Waypoint navigation with path following
- Taxi state machine with LED colors
- Competition environment setup

**In Progress:**
- YOLO road feature detection

**TODO:**
- LiDAR obstacle detection
- Port to pal/hal for submission
- Video production

## Requirements

- Python 3.10+
- Quanser QLabs
- OpenCV, NumPy, keyboard
- ultralytics (for YOLO)

## Official Resources

- [Competition Page](https://www.quanser.com/winners/american-control-conference-self-driving-car-student-competition-2026/)
- [GitHub Documentation](https://quanser.github.io/student-competitions/events/acc-2026/index.html)
- [ROS Resources](https://github.com/quanser/student-competition-resources-ros)
