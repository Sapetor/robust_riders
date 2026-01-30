"""
QCar 2 Manual Control Script - Using Position Control
Control the QCar by moving it to positions (since velocity requires real-time model)

Run this AFTER setup_competition.py (with the environment still in QLabs)
"""

import time
import math
from qvl.qlabs import QuanserInteractiveLabs
from qvl.qcar2 import QLabsQCar2


# Competition coordinates
TAXI_HUB = [-1.205, -0.83, 0.005]
PICKUP = [0.125, 4.395, 0.005]
DROPOFF = [-0.905, 0.800, 0.005]


def main():
    print("="*50)
    print("  QCar 2 Position Control")
    print("="*50)
    
    # Connect to QLabs
    qlabs = QuanserInteractiveLabs()
    print("\nConnecting to QLabs...")
    
    try:
        qlabs.open("localhost")
        print("✅ Connected!\n")
    except:
        print("❌ Could not connect. Is QLabs running?")
        return
    
    # Reference the existing QCar
    car = QLabsQCar2(qlabs)
    car.actorNumber = 0
    
    print("🚗 QCar 2 Position Control Ready!")
    print("-"*50)
    print("Commands:")
    print("  1 = Move to Taxi Hub")
    print("  2 = Move to Pickup location")
    print("  3 = Move to Dropoff location")
    print("  w = Move forward 0.5m")
    print("  s = Move backward 0.5m")
    print("  a = Rotate left 15°")
    print("  d = Rotate right 15°")
    print("  p = Print current position")
    print("  q = Quit")
    print("-"*50)
    
    # Track current position/rotation
    current_pos = list(TAXI_HUB)
    current_rot = -44.7  # degrees
    
    while True:
        cmd = input("\nCommand: ").strip().lower()
        
        if cmd == 'q':
            print("Exiting...")
            break
            
        elif cmd == '1':
            print(f"  → Moving to Taxi Hub {TAXI_HUB}")
            current_pos = list(TAXI_HUB)
            current_rot = -44.7
            car.spawn_id_degrees(
                actorNumber=0,
                location=current_pos,
                rotation=[0, 0, current_rot],
                scale=[0.1, 0.1, 0.1],
                configuration=0,
                waitForConfirmation=True
            )
            
        elif cmd == '2':
            print(f"  → Moving to Pickup {PICKUP}")
            current_pos = list(PICKUP)
            current_rot = 90
            car.spawn_id_degrees(
                actorNumber=0,
                location=current_pos,
                rotation=[0, 0, current_rot],
                scale=[0.1, 0.1, 0.1],
                configuration=0,
                waitForConfirmation=True
            )
            
        elif cmd == '3':
            print(f"  → Moving to Dropoff {DROPOFF}")
            current_pos = list(DROPOFF)
            current_rot = 0
            car.spawn_id_degrees(
                actorNumber=0,
                location=current_pos,
                rotation=[0, 0, current_rot],
                scale=[0.1, 0.1, 0.1],
                configuration=0,
                waitForConfirmation=True
            )
            
        elif cmd == 'w':
            # Move forward based on current rotation
            rad = math.radians(current_rot)
            current_pos[0] += 0.1 * math.cos(rad)
            current_pos[1] += 0.1 * math.sin(rad)
            print(f"  → Forward to {current_pos[:2]}")
            car.spawn_id_degrees(
                actorNumber=0,
                location=current_pos,
                rotation=[0, 0, current_rot],
                scale=[0.1, 0.1, 0.1],
                configuration=0,
                waitForConfirmation=True
            )
            
        elif cmd == 's':
            # Move backward
            rad = math.radians(current_rot)
            current_pos[0] -= 0.1 * math.cos(rad)
            current_pos[1] -= 0.1 * math.sin(rad)
            print(f"  → Backward to {current_pos[:2]}")
            car.spawn_id_degrees(
                actorNumber=0,
                location=current_pos,
                rotation=[0, 0, current_rot],
                scale=[0.1, 0.1, 0.1],
                configuration=0,
                waitForConfirmation=True
            )
            
        elif cmd == 'a':
            current_rot += 15
            print(f"  → Rotate left to {current_rot}°")
            car.spawn_id_degrees(
                actorNumber=0,
                location=current_pos,
                rotation=[0, 0, current_rot],
                scale=[0.1, 0.1, 0.1],
                configuration=0,
                waitForConfirmation=True
            )
            
        elif cmd == 'd':
            current_rot -= 15
            print(f"  → Rotate right to {current_rot}°")
            car.spawn_id_degrees(
                actorNumber=0,
                location=current_pos,
                rotation=[0, 0, current_rot],
                scale=[0.1, 0.1, 0.1],
                configuration=0,
                waitForConfirmation=True
            )
            
        elif cmd == 'p':
            print(f"  Position: {current_pos}")
            print(f"  Rotation: {current_rot}°")
            
        else:
            print("  Unknown command. Use 1/2/3/w/a/s/d/p/q")
    
    qlabs.close()
    print("✅ Done!")


if __name__ == '__main__':
    main()
