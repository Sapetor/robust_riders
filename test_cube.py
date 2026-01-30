"""
Minimal Spawn Test - Just a cube at origin
"""

import time
from qvl.qlabs import QuanserInteractiveLabs
from qvl.basic_shape import QLabsBasicShape

def main():
    print("Connecting...")
    qlabs = QuanserInteractiveLabs()
    qlabs.open("localhost")
    print("Connected!")
    
    # Clear
    qlabs.destroy_all_spawned_actors()
    time.sleep(0.5)
    
    # Spawn a big red cube at origin
    print("Spawning a cube at [0,0,1]...")
    cube = QLabsBasicShape(qlabs)
    result = cube.spawn_degrees(
        location=[0, 0, 1],
        rotation=[0, 0, 0],
        scale=[1, 1, 1],
        configuration=QLabsBasicShape.SHAPE_CUBE,
        waitForConfirmation=True
    )
    print(f"Result: {result}")
    
    # Set color to red
    cube.set_material_properties(
        color=[1, 0, 0],  # Red
        roughness=0.5,
        metallic=False
    )
    
    print("\nLook for a RED CUBE in QLabs!")
    print("Use mouse scroll wheel to zoom out")
    print("Right-click drag to rotate view")
    print("\nPress Enter to exit...")
    input()
    
    qlabs.close()

if __name__ == '__main__':
    main()
