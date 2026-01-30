# Virtual Stage Competition Guide

> **Stage 1 | Deadline: February 27, 2026**

The Virtual Stage is the **qualifying round** for the ACC 2026 Self-Driving Car Competition. All registered teams participate automatically.

---

## 🎯 Objective

Create a **video** that highlights:
- The **performance** of your Self-Driving Car Algorithm
- The **high-level details** of your implementation
- Your team's understanding of self-driving principles

The video will be created using **Quanser Interactive Labs (QLabs)**.

---

## 📋 Submission Requirements

### What to Submit

| Item | Format | Description |
|------|--------|-------------|
| **Code** | GitHub repository link | Your team's self-driving algorithm (may be reviewed) |
| **Video** | YouTube link | 3-minute maximum demonstration |

### Video Guidelines

- **Maximum duration**: 3 minutes
- Demonstrate the [[Detailed-Scenario|detailed scenario]]
- Explain your algorithm's key features
- Show your car's capabilities

> [!IMPORTANT]
> Controlling the QCar or gathering data via the `qvl` library functions will **invalidate** your submission.

---

## 📊 Ranking Criteria

Teams are evaluated on:

1. **Readiness** - Self-Driving algorithm based on [[Core-Principles|core principles]]
2. **Accuracy** - Staying within lanes during driving
3. **Timely Reactions** - Responding to road signage and traffic controls
4. **Communication** - Clear and concise explanation of concepts

> [!TIP]
> The **communication criteria** is one of the most important! It shows judges how well your team understands self-driving principles.

---

## 🎥 Example Submission

The **Czech Technical University in Prague** submitted [this video](https://www.youtube.com/watch?v=JXOI1RtLTbs) for the 2025 ACC Competition and was invited to the Physical Stage.

**What made it successful:**
- Demonstrated all core self-driving principles
- Clear explanation of algorithm concepts
- Smooth lane following
- Proper traffic control responses

---

## 🔬 What You'll Receive

Teams get access to:

- **QLabs** (Quanser Interactive Labs) platform
- **QCar 2 digital twin** with all sensors and actuators
- Same APIs used by the physical QCar 2

---

## 💡 Tips for Success

### Do's ✅
- Start with the provided detailed scenario
- Create more complex scenarios to showcase capabilities
- Spawn additional actors (traffic, obstacles)
- Use creative QLabs environments
- Clearly explain your algorithm's decision-making

### Don'ts ❌
- Use `qvl` library for car control or data gathering
- Exceed 3-minute video length
- Skip explaining core concepts
- Show messy or unstable driving

---

## 🎮 Scenario Recommendations

The [[Detailed-Scenario|detailed scenario]] is your starting point, but judges appreciate teams that:

1. Add traffic scenarios with multiple cars
2. Include pedestrian detection
3. Demonstrate obstacle avoidance
4. Handle edge cases gracefully

---

## 🔗 Related Documents

- [[Detailed-Scenario]] - Step-by-step scenario walkthrough
- [[Core-Principles]] - Self-driving fundamentals
- [[LED-Protocol]] - LED color meanings for taxi operations
- [[Coordinate-System]] - Competition coordinate system

---

## 📚 External Resources

- [Virtual Stage Competition Guide](https://quanser.github.io/student-competitions/events/common/Rules_and_Objectives/Virtual_Stage_Competition_Guide.html)
- [ROS Technical Resources](https://github.com/quanser/student-competition-resources-ros)
- [QLabs Documentation](https://qlabs.quanserdocs.com/en/latest/)
