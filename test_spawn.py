"""
Simple QLabs Test - Debug Script
Spawns a QCar at origin with full scale to debug visibility issues
"""

import time
from qvl.qlabs import QuanserInteractiveLabs
from qvl.qcar2 import QLabsQCar2
from qvl.free_camera import QLabsFreeCamera

def main():
    print("="*50)
    print("  Simple QLabs Spawn Test")
    print("="*50)
    
    qlabs = QuanserInteractiveLabs()
    print("\nConnecting to QLabs...")
    
    connected = qlabs.open("localhost")
    if not connected:
        print("❌ Failed to connect!")
        return
    
    print("✅ Connected!")
    
    # Clear everything
    print("\nClearing all actors...")
    qlabs.destroy_all_spawned_actors()
    time.sleep(1)
    
    # Try spawning with FULL scale at origin
    print("\nSpawning QCar at origin [0, 0, 0.5] with scale [1,1,1]...")
    car = QLabsQCar2(qlabs)
    
    result = car.spawn_degrees(
        location=[0, 0, 0.5],  # Slightly above ground
        rotation=[0, 0, 0],
        scale=[1, 1, 1],  # FULL scale, not 0.1
        configuration=0,
        waitForConfirmation=True
    )
    print(f"  Spawn result: {result}")
    
    # Set camera looking at origin
    print("\nSetting up camera looking at origin...")
    camera = QLabsFreeCamera(qlabs)
    camera.spawn_degrees(
        location=[5, 5, 5],
        rotation=[0, 35, -135]
    )
    camera.possess()
    print("  Camera set!")
    
    print("\n" + "="*50)
    print("  You should see a QCar in QLabs now!")
    print("  If not, check that QLabs has 'Plane' workspace open")
    print("="*50)
    
    print("\nPress Enter to exit (car will stay)...")
    input()
    
    qlabs.close()
    print("Done!")


if __name__ == '__main__':
    main()
