"""
QLabs Connection Test Script
This script connects to QLabs and spawns a QCar 2 in the Cityscape environment.
Make sure QLabs is running with the Cityscape workspace open before running this script.
"""

from qvl.qlabs import QuanserInteractiveLabs
from qvl.qcar2 import QLabsQCar2
from qvl.free_camera import QLabsFreeCamera
import time

def main():
    # Connect to QLabs
    print("Connecting to QLabs...")
    qlabs = QuanserInteractiveLabs()
    
    # Try to connect (QLabs must be running)
    connected = qlabs.open("localhost")
    
    if not connected:
        print("ERROR: Could not connect to QLabs.")
        print("Make sure Quanser Interactive Labs is running with a workspace open.")
        return
    
    print("✅ Connected to QLabs!")
    
    # Destroy any existing actors to start fresh
    print("Clearing existing actors...")
    qlabs.destroy_all_spawned_actors()
    time.sleep(0.5)
    
    # Create a free camera for a good view
    print("Setting up camera...")
    camera = QLabsFreeCamera(qlabs)
    camera.spawn(location=[0, -5, 3], rotation=[0, 0.5, 0])
    camera.possess()
    
    # Spawn a QCar 2
    print("Spawning QCar 2...")
    qcar = QLabsQCar2(qlabs)
    
    # Spawn at origin with no rotation
    # Location: [x, y, z] in meters
    # Rotation: [roll, pitch, yaw] in radians
    qcar.spawn(
        location=[0, 0, 0],
        rotation=[0, 0, 0],
        scale=[1, 1, 1],
        configuration=0
    )
    
    print("✅ QCar 2 spawned successfully!")
    print("\n🚗 You should now see a QCar 2 in your QLabs window.")
    print("Press Enter to clean up and exit...")
    input()
    
    # Clean up
    print("Cleaning up...")
    qlabs.destroy_all_spawned_actors()
    qlabs.close()
    print("Done!")

if __name__ == "__main__":
    main()
