# ROS Development Guide

The competition uses **ROS** (Robot Operating System) as the primary supported framework. Technical support is only provided for ROS-based solutions.

---

## 📋 Quick Links

| Resource | Link |
|----------|------|
| **ROS Technical Resources** | [GitHub Repository](https://github.com/quanser/student-competition-resources-ros) |
| **Issues** | [Report Bugs](https://github.com/quanser/student-competition-resources-ros/issues) |
| **Discussions** | [Community Forum](https://github.com/quanser/student-competition-resources-ros/discussions) |

---

## 📚 Resource List

### Virtual Stage Resources

| Guide | Description |
|-------|-------------|
| [Virtual ROS Software Setup](https://github.com/quanser/student-competition-resources-ros/blob/main/Virtual_ROS_Resources/Virtual_ROS_Software_Setup.md) | **START HERE** - Initial setup instructions |
| [Virtual ROS Development Guide](https://github.com/quanser/student-competition-resources-ros/blob/main/Virtual_ROS_Resources/Virtual_ROS_Development_Guide.md) | Working with the Development Container (isaac-ros) |
| [Virtual Running Nav2 Guide](https://github.com/quanser/student-competition-resources-ros/blob/main/Virtual_ROS_Resources/Virtual_Running_Nav2_Guide.md) | Running Nav2 in virtual environment |
| [Virtual Stage ROS FAQ](https://github.com/quanser/student-competition-resources-ros/blob/main/Virtual_ROS_Resources/Virtual_Stage_ROS_FAQ.md) | Common issues and solutions |

### Physical Stage Resources

| Guide | Description |
|-------|-------------|
| [Physical ROS Software Setup](https://github.com/quanser/student-competition-resources-ros/blob/main/Virtual_ROS_Resources/Physical_ROS_Software_Setup.md) | Setting up QCar 2 with Isaac-ROS container |
| [Utilizing hal and pal](https://github.com/quanser/student-competition-resources-ros/blob/main/Virtual_ROS_Resources/Utilizing_hal_and_pal.md) | Using Quanser Academic Resources in container |

---

## 🚀 Getting Started

### Step 1: Virtual ROS Software Setup
Start with the [Virtual ROS Software Setup Guide](https://github.com/quanser/student-competition-resources-ros/blob/main/Virtual_ROS_Resources/Virtual_ROS_Software_Setup.md):

1. Install required dependencies
2. Set up Docker environment
3. Configure Isaac-ROS container
4. Connect to QLabs

### Step 2: Development Container
Use the [Development Guide](https://github.com/quanser/student-competition-resources-ros/blob/main/Virtual_ROS_Resources/Virtual_ROS_Development_Guide.md) to:

- Understand container architecture
- Build ROS packages
- Run self-driving nodes

### Step 3: Navigation Stack
Follow the [Nav2 Guide](https://github.com/quanser/student-competition-resources-ros/blob/main/Virtual_ROS_Resources/Virtual_Running_Nav2_Guide.md) for:

- Setting up Nav2 (Navigation 2)
- Path planning
- Autonomous navigation

---

## 🐳 Docker Container

The competition uses **Isaac-ROS** Docker container:

- Pre-configured ROS 2 environment
- GPU support for NVIDIA
- Quanser libraries included
- `hal` and `pal` from Quanser Academic Resources

---

## ⚙️ Key ROS Components

### Path Planning
- **Nav2** - Navigation 2 stack
- Global and local planners
- Costmap generation

### Perception
- Camera image processing
- LiDAR point cloud handling
- Object detection

### Localization
- SLAM (Simultaneous Localization and Mapping)
- Odometry fusion
- State estimation

### Control
- Velocity commands
- Steering control
- LED control

---

## ❓ Getting Help

### For Bugs
Post an issue on [GitHub Issues](https://github.com/quanser/student-competition-resources-ros/issues):
- Describe the problem clearly
- Include error messages
- Show your configuration

### For Discussion
Use [GitHub Discussions](https://github.com/quanser/student-competition-resources-ros/discussions):
- Ask questions to other teams
- Share ideas and solutions
- General competition discussion

### FAQ
Check the [Virtual Stage ROS FAQ](https://github.com/quanser/student-competition-resources-ros/blob/main/Virtual_ROS_Resources/Virtual_Stage_ROS_FAQ.md) for common issues.

---

## 💡 Tips

> [!TIP]
> While any software is allowed for submissions, competition organizers **only respond to technical questions about ROS**.

### Do's ✅
- Use provided Docker containers
- Follow the guides step-by-step
- Post issues on GitHub for bugs
- Check FAQ before asking questions

### Don'ts ❌
- Expect support for non-ROS frameworks
- Skip the setup guides
- Use outdated ROS versions

---

## 🔗 Related Documents

- [[Software-Requirements]] - Complete software requirements
- [[QLabs-Setup]] - QLabs environment setup
- [[QCar2-Overview]] - QCar 2 specifications

---

## 📚 External Resources

- [ROS 2 Documentation](https://docs.ros.org/en/rolling/)
- [Nav2 Documentation](https://navigation.ros.org/)
- [Quanser Academic Resources](https://github.com/quanser/Quanser_Academic_Resources)
- [QUARC Block Documentation](https://docs.quanser.com/quarc/documentation/quarc_block_categories.html)
