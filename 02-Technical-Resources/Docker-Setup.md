# 🐳 Docker Setup for ACC 2026

> Competition-compliant development environment setup

---

## ✅ Prerequisites (Already Installed)

- [x] Docker Desktop - Found installed
- [x] WSL2 - Available (docker-desktop)

---

## 📥 Step 1: Download Competition Resources

1. Go to [Competition Resources Box](https://quanserinc.box.com/s/g2690n3jwbhquwr8uqdz0b45m5wx945z)
2. Password: `acc2025denver`
3. Download `ACC_Resources.zip`
4. Extract to `C:\Users\sapet\Documents\ACC_Development\`

---

## 🚀 Step 2: Start Docker Desktop

1. Open **Docker Desktop** from Start Menu
2. Wait for it to start (whale icon turns green)
3. Ensure WSL2 backend is enabled (Settings → General → Use WSL2)

---

## 📦 Step 3: Run Setup Script

Open PowerShell and run:

```powershell
cd C:\Users\sapet\Documents\ACC_Development
python setup_linux.py
```

This will:
- Set up the Quanser Virtual Container
- Set up the Development Container
- Download required images

---

## 🎮 Step 4: Start Containers

### Terminal 1 - Quanser Virtual Container (QLabs)
```bash
cd ACC_Development
./scripts/run_virtual.sh
```

### Terminal 2 - Development Container (Your Code)
```bash
cd ACC_Development
./scripts/run_dev.sh /home/$USER/Documents/ACC_Development/Development
```

---

## 🔄 Step 5: Run Competition Map

Inside the Quanser Virtual Container:
```bash
python Base_Scenarios_Python/Setup_Competition_Map.py
```

This will:
- Spawn flooring and walls
- Spawn QCar at Taxi Hub position
- Start the RT Model

---

## 🚗 Step 6: Run Vehicle Control

Inside the Development Container:
```bash
cd /workspaces/isaac_ros-dev/python_dev
python vehicle_control.py
```

---

## 📁 File Structure

```
ACC_Development/
├── docker/                    # Docker files
│   └── libraries/python/      # hal/pal libraries
├── Development/
│   ├── ros2/                  # ROS packages
│   └── python_dev/            # Python development
│       ├── vehicle_control.py
│       └── QCar2_hardware_test_*.py
└── scripts/
    ├── run_virtual.sh
    └── run_dev.sh
```

---

## 🔗 Related Documents

- [[External-Resources]] - Competition links
- [[Implementation-Plan]] - Porting strategy
- [[Development-Plan]] - Overall plan

---

## 📚 References

- [ACC Software Setup Instructions](https://github.com/quanser/ACC-Competition-2025/blob/main/Software_Guides/ACC%20Software%20Setup%20Instructions.md)
- [Utilizing hal and pal](https://github.com/quanser/ACC-Competition-2025/blob/main/Software_Guides/Utilizing%20hal%20and%20pal.md)
