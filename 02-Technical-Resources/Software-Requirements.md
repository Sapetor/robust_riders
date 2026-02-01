# Software Requirements

This document outlines the software stack used in the ACC 2026 Self-Driving Car Competition.

---

## 🎯 Official Statement

> Any software is allowed for submissions, but competition organizers will **only respond to technical questions about ROS**.

---

## 💻 Supported Stack

### Primary Frameworks

| Framework | Support Level |
|-----------|--------------|
| **ROS 2** | ✅ Full support |
| **Python 3** | ✅ Full support |
| **MATLAB/Simulink** | Documentation available |
| **Other** | Allowed, no support |

---

## 🔧 ROS Environment

### Development Container: Isaac-ROS

The competition provides Docker containers with:

- ROS 2 environment
- GPU support (NVIDIA)
- Quanser libraries (`hal`, `pal`)
- Pre-configured dependencies

### ROS Resources

| Resource | Link |
|----------|------|
| **Setup Guide** | [Virtual ROS Software Setup](https://github.com/quanser/student-competition-resources-ros/blob/main/Virtual_ROS_Resources/Virtual_ROS_Software_Setup.md) |
| **Development Guide** | [Virtual ROS Development Guide](https://github.com/quanser/student-competition-resources-ros/blob/main/Virtual_ROS_Resources/Virtual_ROS_Development_Guide.md) |
| **Nav2 Guide** | [Running Nav2 Guide](https://github.com/quanser/student-competition-resources-ros/blob/main/Virtual_ROS_Resources/Virtual_Running_Nav2_Guide.md) |

---

## 🐍 Python Libraries

### Computer Vision
- **OpenCV** - Image processing
- **VisionWorks** - GPU-accelerated vision
- **VPI** (Vision Programming Interface)

### Machine Learning
- **TensorFlow** - Deep learning
- **TensorRT** - Optimized inference
- **CUDA** - GPU computing
- **cuDNN** - Deep neural network library

### Multimedia
- **GStreamer** - Video streaming
- **Jetson Multimedia APIs** - NVIDIA-specific

---

## 🔧 MATLAB/Simulink

For MATLAB users:

| Tool | Documentation |
|------|---------------|
| **QUARC** | [Block Documentation](https://docs.quanser.com/quarc/documentation/quarc_block_categories.html) |
| **Simulink Coder** | Required for code generation |

---

## 📦 Quanser Libraries

### hal (Hardware Abstraction Layer)
- Direct hardware interface
- Sensor/actuator access

### pal (Platform Abstraction Layer)
- Platform-independent code
- Simulation compatibility

### qvl (Quanser Virtual Library)
> [!CAUTION]
> **Environment setup only!** Using `qvl` for car control invalidates submissions.

---

## 🌐 Virtual Environment

### QLabs (Quanser Interactive Labs)
- Digital twin simulation
- 1:1 mapping to physical environment
- Python API for control

### Required Access
- QLabs subscription (provided to registered teams)
- First 10 team members get access

---

## 🔌 Communication

### Quanser Stream APIs
- Inter-process communication
- Multi-language support
- Real-time data streaming

### Docker Containers
- GPU support
- Isolated environments
- Reproducible setups

---

## 📋 Minimum Requirements

### For Virtual Stage
- Computer with Python 3
- Docker support
- Graphics capability for QLabs
- Internet connection

### For Physical Stage
- Router and Network Switch
- Laptops for development
- Portable monitors (recommended)

---

## 🔗 Related Documents

- [[ROS-Setup]] - Detailed ROS setup guide
- [[QLabs-Setup]] - QLabs environment setup
- [[QCar2-Overview]] - QCar 2 software support

---

## 📚 External Resources

- [ROS Technical Resources](https://github.com/quanser/student-competition-resources-ros)
- [Quanser Academic Resources](https://github.com/quanser/Quanser_Academic_Resources)
- [QLabs Documentation](https://qlabs.quanserdocs.com/en/latest/)
- [QUARC Documentation](https://docs.quanser.com/quarc/documentation/quarc_block_categories.html)
