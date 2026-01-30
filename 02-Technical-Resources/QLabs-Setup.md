# QLabs Setup Guide

**Quanser Interactive Labs (QLabs)** provides the digital twin environment for the QCar 2 and Quanser City.

---

## 🎯 Overview

QLabs provides:
- **Virtual QCar 2** with all sensors and actuators
- **Cityscape** environment (full-scale Quanser roadmaps)
- Same APIs as physical QCar 2
- Python script-based control

---

## 💻 Design Philosophy

> The QLabs API is designed for **Python script tests**. The virtual environment is NOT designed to be used through the interface alone.

---

## 🚀 Getting Started

### 1. Installation

Follow the official [Get Started Guide](https://qlabs.quanserdocs.com/en/latest/Get%20Started.html):

1. **Installation / Set Up** - Install QLabs and dependencies
2. **Running Python Scripts** - Connect to QLabs Open Worlds

### 2. User Interface

Learn to navigate QLabs:
- Navigation controls
- Adding cameras
- Camera options
- Coordinate helper tool
- Workspace options
- Graphics settings

---

## 🌆 Workspaces

### Cityscape
Full-scale digital city environment featuring:
- Roads and intersections
- Traffic controls
- Parking areas
- Taxi hub

### Cityscape Lite
Lighter version for faster testing

> [!NOTE]
> Cityscape maps in QLabs are **1:1 representations** of the Physical Quanser Roadmaps.

---

## 📍 Coordinate System

- Base frame: `[0, 0, 0]`
- Same coordinate system for virtual and physical competitions
- Use the **coordinate helper tool** in QLabs UI

See [[Coordinate-System]] for detailed information.

---

## 🔧 Key Features

### Sensors (Virtual)
- Cameras (front, rear, side)
- LiDAR
- IMU
- All behave identically to physical sensors

### Actuators
- Steering control
- Throttle/brake
- LED strip control

### Environment Actors
- Traffic lights
- Other vehicles
- Pedestrians
- Obstacles

---

## ⚠️ Important Rules

> [!CAUTION]
> The `qvl` library is for **environment setup only**. Using `qvl` to control the QCar or gather data will **invalidate** your submission!

### Allowed
- Setting up environment
- Spawning actors
- Camera placement for video recording

### NOT Allowed
- Car control via `qvl`
- Reading sensor data via `qvl`
- Cheating with environment manipulation

---

## 📚 API Documentation

| Topic | Link |
|-------|------|
| **Installation** | [Get Started](https://qlabs.quanserdocs.com/en/latest/Get%20Started.html) |
| **User Interface** | [UI Guide](https://qlabs.quanserdocs.com/en/latest/User%20Interface.html) |
| **Workspaces** | [Workspace Docs](https://qlabs.quanserdocs.com/en/latest/Workspaces/index.html) |
| **Code Style** | [Contributing Guide](https://qlabs.quanserdocs.com/en/latest/Code%20Style.html) |

---

## 🔗 Related Documents

- [[ROS-Setup]] - ROS development guide
- [[Software-Requirements]] - Software requirements
- [[Coordinate-System]] - Coordinate system details

---

## 📚 External Resources

- [QLabs API Documentation](https://qlabs.quanserdocs.com/en/latest/)
- [QLabs Support Page](https://portal.quanser.com/Support)
- [QLabs Resources GitHub](https://github.com/quanser/Quanser_Interactive_Labs_Resources)
