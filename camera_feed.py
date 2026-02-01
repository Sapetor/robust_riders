"""
QCar 2 Camera Feed - ACC 2026
Display live camera feed from the QCar's cameras

Run in CITYSCAPE workspace!
"""

import os
import time
import cv2
import numpy as np

from qvl.qlabs import QuanserInteractiveLabs
from qvl.qcar2 import QLabsQCar2
from qvl.free_camera import QLabsFreeCamera


def main():
    os.system('cls')
    print("="*60)
    print("  QCar 2 Camera Feed - CITYSCAPE")
    print("="*60)
    
    qlabs = QuanserInteractiveLabs()
    print("\nConnecting to QLabs...")
    
    if not qlabs.open("localhost"):
        print("❌ Could not connect!")
        return
    
    print("✅ Connected!")
    
    # Clear and spawn
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
    
    print("\n📷 Available Cameras:")
    print("  1 = CSI Front")
    print("  2 = CSI Right")
    print("  3 = CSI Back")
    print("  4 = CSI Left")
    print("  5 = RealSense RGB")
    print("  6 = RealSense Depth")
    
    print("\n" + "="*60)
    print("  Press ESC in the camera window to exit")
    print("  Press 1-6 to switch cameras")
    print("="*60)
    
    # Camera mapping
    cameras = {
        ord('1'): (car.CAMERA_CSI_FRONT, "CSI Front"),
        ord('2'): (car.CAMERA_CSI_RIGHT, "CSI Right"),
        ord('3'): (car.CAMERA_CSI_BACK, "CSI Back"),
        ord('4'): (car.CAMERA_CSI_LEFT, "CSI Left"),
        ord('5'): (car.CAMERA_RGB, "RealSense RGB"),
        ord('6'): (car.CAMERA_DEPTH, "RealSense Depth"),
    }
    
    current_camera = car.CAMERA_CSI_FRONT
    camera_name = "CSI Front"
    
    print(f"\n🎥 Starting with {camera_name} camera...")
    print("   (Press ESC to exit)")
    
    cv2.namedWindow("QCar Camera", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("QCar Camera", 640, 480)
    
    while True:
        # Get image from camera
        success, image = car.get_image(camera=current_camera)
        
        if success and image is not None:
            # Add camera label
            cv2.putText(image, camera_name, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Display the image
            cv2.imshow("QCar Camera", image)
        else:
            # Show black screen with error
            blank = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(blank, "No image received", (150, 240),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.imshow("QCar Camera", blank)
        
        # Check for key presses
        key = cv2.waitKey(30) & 0xFF
        
        if key == 27:  # ESC
            break
        elif key in cameras:
            current_camera, camera_name = cameras[key]
            print(f"  → Switched to {camera_name}")
    
    cv2.destroyAllWindows()
    print("\n🛑 Camera closed")
    qlabs.close()
    print("✅ Done!")


if __name__ == '__main__':
    main()
