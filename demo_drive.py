"""
QCar 2 Velocity Control - Using Official API
This uses the actual velocity commands like the Quanser tutorial

Run in CITYSCAPE workspace!
"""

import os
import time
import math
import keyboard

from qvl.qlabs import QuanserInteractiveLabs
from qvl.qcar2 import QLabsQCar2
from qvl.free_camera import QLabsFreeCamera


def main():
    os.system('cls')
    print("="*60)
    print("  QCar 2 Velocity Control - CITYSCAPE")
    print("="*60)
    
    qlabs = QuanserInteractiveLabs()
    print("\nConnecting to QLabs...")
    
    if not qlabs.open("localhost"):
        print("❌ Could not connect!")
        return
    
    print("✅ Connected!")
    
    # Clear previous
    qlabs.destroy_all_spawned_actors()
    time.sleep(0.5)
    
    # Spawn QCar
    print("Spawning QCar...")
    car = QLabsQCar2(qlabs)
    car.spawn_id_degrees(
        actorNumber=0,
        location=[0, 0, 0.5],
        rotation=[0, 0, 0],
        scale=[1, 1, 1],
        configuration=0,
        waitForConfirmation=True
    )
    
    # Camera
    camera = QLabsFreeCamera(qlabs)
    camera.spawn_degrees(location=[10, 10, 8], rotation=[0, 30, -135])
    camera.possess()
    
    print("\n" + "="*60)
    print("  ✅ Ready! Use ARROW KEYS (requires admin)")
    print("="*60)
    print("  ↑/↓ = Speed up/down")
    print("  ←/→ = Steer left/right")
    print("  SPACE = Stop")
    print("  Q = Quit")
    print("="*60)
    print("\n🚗 Driving... (If keys don't work, run as Administrator)")
    
    speed = 0.0
    turn = 0.0
    
    running = True
    while running:
        try:
            # Check keys
            if keyboard.is_pressed('q'):
                running = False
                
            elif keyboard.is_pressed('up'):
                speed = min(speed + 0.1, 2.0)
                print(f"\r  Speed: {speed:.1f}  Turn: {turn:.1f}    ", end="")
                
            elif keyboard.is_pressed('down'):
                speed = max(speed - 0.1, -1.0)
                print(f"\r  Speed: {speed:.1f}  Turn: {turn:.1f}    ", end="")
                
            elif keyboard.is_pressed('left'):
                turn = min(turn + 0.1, 0.5)
                print(f"\r  Speed: {speed:.1f}  Turn: {turn:.1f}    ", end="")
                
            elif keyboard.is_pressed('right'):
                turn = max(turn - 0.1, -0.5)
                print(f"\r  Speed: {speed:.1f}  Turn: {turn:.1f}    ", end="")
                
            elif keyboard.is_pressed('space'):
                speed = 0.0
                turn = 0.0
                print(f"\r  STOPPED                        ", end="")
            
            # Apply velocity
            car.set_velocity_and_request_state(
                forward=speed,
                turn=turn,
                headlights=True,
                leftTurnSignal=(turn > 0.1),
                rightTurnSignal=(turn < -0.1),
                brakeSignal=(speed == 0),
                reverseSignal=(speed < 0)
            )
            
            time.sleep(0.1)
            
        except Exception as e:
            print(f"\nError: {e}")
            break
    
    # Stop the car
    car.set_velocity_and_request_state(0, 0, False, False, False, True, False)
    
    print("\n\n🛑 Stopped!")
    qlabs.close()
    print("✅ Done!")


if __name__ == '__main__':
    main()
