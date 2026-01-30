# Coordinate System

The competition uses a consistent coordinate system for both virtual (QLabs) and physical environments.

---

## 🎯 Base Frame

The coordinate system origin is defined as:

```
[0, 0, 0] = Base Frame Origin
```

The **orientation of the coordinate tool in QLabs** defines the base frame that all coordinates are determined from.

---

## 📐 Coordinate Convention

| Axis | Direction |
|------|-----------|
| **X** | Forward/Backward |
| **Y** | Left/Right |
| **Z** | Up/Down (height) |

> [!NOTE]
> Always verify axis orientation using the QLabs coordinate helper tool.

---

## 🔄 Virtual-Physical Mapping

The same coordinate system applies to:

- **QLabs environments** (Cityscape, Cityscape Lite)
- **Physical Quanser Roadmaps**

> [!IMPORTANT]
> QLabs CityScape maps are **1:1 full-scale representations** of the Physical Quanser Roadmaps.

This means:
- Code developed in simulation transfers directly to physical
- Coordinates learned in QLabs work on competition day
- Same waypoints for virtual and physical stages

---

## 📍 Example Coordinates

From the [[Detailed-Scenario|Detailed Scenario]]:

| Location | Coordinates (meters) |
|----------|---------------------|
| **Pickup Point** | `[0.125, 4.395]` |
| **Drop-off Point** | `[-0.905, 0.800]` |
| **Taxi Hub Area** | Starting position |

---

## 🛠️ Using QLabs Coordinate Helper

In QLabs, use the **Coordinate Helper** tool to:

1. Determine exact positions on the map
2. Plan waypoints for navigation
3. Verify pickup/drop-off locations
4. Debug localization issues

### Accessing the Tool

1. Open QLabs
2. Navigate to UI options
3. Enable Coordinate Helper
4. Click on map locations to see coordinates

---

## 🗺️ Map Features

The competition roadmap includes:

| Feature | Description |
|---------|-------------|
| **Taxi Hub** | Start/end point for rides |
| **Intersections** | Traffic-controlled junctions |
| **Lane Markings** | Single and double lane roads |
| **Parking Areas** | Designated parking spaces |
| **Roundabouts** | Circular driving areas |

---

## 💡 Tips for Navigation

### Path Planning
- Store key coordinates in your navigation system
- Use the base frame as reference
- Account for vehicle dimensions at waypoints

### Localization
- Use IMU + odometry for state estimation
- LiDAR matching for map-based localization
- Camera-based lane detection for fine adjustments

### Coordinate Transforms
- Convert sensor readings to base frame
- Handle rotations properly
- Consider vehicle heading in calculations

---

## 🔗 Related Documents

- [[Detailed-Scenario]] - Competition scenario with coordinates
- [[Core-Principles]] - Localization principles
- [[QLabs-Setup]] - QLabs environment

---

## 📚 External Resources

- [Virtual Stage Competition Guide - Coordinate System](https://quanser.github.io/student-competitions/events/common/Rules_and_Objectives/Virtual_Stage_Competition_Guide.html#coordinate-system)
- [QLabs User Interface](https://qlabs.quanserdocs.com/en/latest/User%20Interface.html#coordinate-helper)
