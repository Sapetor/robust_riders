# QCar 2 Overview

The **QCar 2** is Quanser's flagship 1/10-scale autonomous research vehicle, powered by **NVIDIA Orin AGX**.

---

## 📋 Quick Facts

| Specification | Details |
|---------------|---------|
| **Scale** | 1/10 |
| **Processor** | NVIDIA Orin AGX |
| **Purpose** | Academic self-driving research & teaching |
| **Digital Twin** | Available in QLabs |

---

## 🔬 Sensors Suite

The QCar 2 features a comprehensive sensor package:

### Visual Sensors
- Multiple cameras for 360° perception
- CSI camera interfaces
- Support for multiple camera configurations

### Ranging Sensors
- **LiDAR** for distance measurement and mapping
- Ideal for SLAM (Simultaneous Localization and Mapping)

### Inertial Sensors
- **IMU** (Inertial Measurement Unit)
- Accelerometer and gyroscope data
- Essential for state estimation

---

## 💻 Supported Software & APIs

### Primary Frameworks
- **ROS 2** (Robot Operating System)
- **Python 2.7 / 3**
- **QUARC for Simulink®**

### AI/ML Frameworks
- **TensorFlow**
- **CUDA®**
- **cuDNN**
- **TensorRT**

### Computer Vision
- **OpenCV**
- **VisionWorks®**
- **VPI™**

### Other Tools
- **GStreamer** - Multimedia streaming
- **Jetson Multimedia APIs**
- **Docker containers** with GPU support
- **Quanser Stream APIs** for inter-process communication

---

## 🎮 Digital Twin

The **QLabs Virtual QCar 2** provides:

- 1:1 representation of physical QCar 2
- Same sensors and actuators
- Same APIs as physical vehicle
- Virtual Quanser City environment
- **Cityscape** and **Cityscape Lite** environments

> [!TIP]
> Code developed in QLabs can transfer directly to physical QCar 2 with minimal changes.

---

## 🛣️ Self-Driving Car Studio

The QCar 2 is the feature vehicle of the **Self-Driving Car Studio**, which includes:

### Infrastructure
- Programmable traffic lights
- Durable driving map with:
  - Intersections
  - Parking spaces
  - Single & double lane roads
  - Roundabouts
- Scaled accessories (signs, pylons)
- Preconfigured High-Performance PC with 3 monitors

### Applications
- Self-driving algorithm development
- Machine vision and learning
- Traffic and fleet management
- Platooning
- City and highway maneuvering

---

## 📚 Documentation Resources

| Resource | Link |
|----------|------|
| **Info Sheet** | [Download PDF](https://quanserinc.box.com/shared/static/2jc8ws3d7n0g9vxsiebg6jtdoibv7eul.pdf) |
| **Research Resources** | [GitHub](https://github.com/quanser/Quanser_Academic_Resources/tree/dev-windows) |
| **Content Guide** | [Download PDF](https://www.quanser.com/wp-content/uploads/2024/09/SelfDriving-CGuide-Final.pdf) |
| **Research Guide** | [Download PDF](https://www.quanser.com/wp-content/uploads/2024/09/Research-Guide.pdf) |

---

## 🎬 Webinars

- [Applied AI with Quanser Autonomous Vehicles](https://www.youtube.com/watch?v=xY77OZY8lQk)
- [Drive Innovation: New 1/10th Scale Car](https://www.youtube.com/watch?v=JhqBpdSkfR4)

---

## 🔗 Related Documents

- [[QLabs-Setup]] - Digital twin environment setup
- [[ROS-Setup]] - ROS development guide
- [[Software-Requirements]] - Complete software stack

---

## 📚 External Resources

- [QCar 2 Product Page](https://www.quanser.com/products/qcar-2/)
- [Self-Driving Car Studio](https://www.quanser.com/products/self-driving-car-studio/)
- [Quanser Academic Resources](https://github.com/quanser/Quanser_Academic_Resources)
