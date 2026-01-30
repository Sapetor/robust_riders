# 🔗 External Resources

> Key external resources for ACC 2026 competition development

---

## 🏆 Official Competition Resources

| Resource | Description |
|----------|-------------|
| [ACC 2025 Competition Repo](https://github.com/quanser/ACC-Competition-2025) | Official Quanser competition repo (2025 reference) |
| [Base Scenarios Python](https://github.com/quanser/ACC-Competition-2025/tree/main/Docker/virtual_qcar2/python/Base_Scenarios_Python) | Official Python examples |
| [Development Guide](https://github.com/quanser/ACC-Competition-2025/blob/main/Software_Guides/Development%20Guide.md) | Docker/ROS development guide |
| [Detailed Scenario](https://github.com/quanser/ACC-Competition-2025/blob/main/Detailed_Scenario.md) | Competition scenario details |
| [FAQ](https://github.com/quanser/ACC-Competition-2025/blob/main/Software_Guides/FAQ.md) | Frequently asked questions |

---

## 📖 Quanser Documentation

| Resource | Description |
|----------|-------------|
| [QLabs Documentation](https://qlabs.quanserdocs.com/en/latest/) | Official QLabs docs |
| [Quanser Python API](https://docs.quanser.com/quarc/documentation/python/index.html) | Python API reference |
| [Quanser Portal Support](https://portal.quanser.com/Support) | Support page |
| [QLabs Resources GitHub](https://github.com/quanser/Quanser_Interactive_Labs_Resources) | Tutorials and libraries |

---

## 🚗 Lane Detection & Perception

### Recommended Approach (from Quanser)

1. **HSV Color Filtering** - Filter for yellow/white lane markings
2. **Perspective Transform** - Convert to bird's eye view (top-down)
3. **Polynomial Fitting** - Fit curves to lane pixels
4. **Sliding Window** - Track lanes across frames

### Reference Implementations

| Resource | Description |
|----------|-------------|
| [bchampp/autonomous-driving](https://github.com/bchampp/autonomous-driving) | QCar autonomous driving with SLAM, lane detection, ROS |
| [Ucicek/lane-following](https://github.com/Ucicek/lane-following-autonomous-car) | General lane following with CV |

---

## 📹 Video Tutorials

- Quanser regularly posts webinars and tutorials on their competition page
- Check YouTube for "Quanser QCar" tutorials

---

## 🔑 Access Credentials

> [!WARNING]
> Keep these secure and do not share publicly

- **Competition Resources Box**: Password in ACC 2025 repo README

---

## 🔗 Related Documents

- [[Software-Requirements]] - Local software setup
- [[QLabs-Setup]] - QLabs configuration
- [[Development-Plan]] - Our development plan
