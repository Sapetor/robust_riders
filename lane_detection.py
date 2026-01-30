"""
QCar 2 Lane Detection - ACC 2026
Detect lane lines using classical computer vision

Uses: Canny edge detection + Hough Line Transform
Run in CITYSCAPE workspace!
"""

import os
import time
import cv2
import numpy as np

from qvl.qlabs import QuanserInteractiveLabs
from qvl.qcar2 import QLabsQCar2


def region_of_interest(img, vertices):
    """Apply a mask to keep only the region of interest."""
    mask = np.zeros_like(img)
    cv2.fillPoly(mask, vertices, 255)
    return cv2.bitwise_and(img, mask)


def detect_lanes(image):
    """
    Detect lane lines in the image.
    Returns the image with lane lines drawn.
    """
    height, width = image.shape[:2]
    
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Canny edge detection
    edges = cv2.Canny(blur, 50, 150)
    
    # Define region of interest (lower half of image, trapezoid shape)
    roi_vertices = np.array([[
        (0, height),
        (width * 0.4, height * 0.6),
        (width * 0.6, height * 0.6),
        (width, height)
    ]], dtype=np.int32)
    
    masked_edges = region_of_interest(edges, roi_vertices)
    
    # Hough Line Transform
    lines = cv2.HoughLinesP(
        masked_edges,
        rho=1,
        theta=np.pi/180,
        threshold=50,
        minLineLength=50,
        maxLineGap=150
    )
    
    # Create output image
    output = image.copy()
    
    # Draw the ROI for visualization
    cv2.polylines(output, roi_vertices, True, (0, 255, 255), 2)
    
    # Separate left and right lane lines
    left_lines = []
    right_lines = []
    
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            
            # Calculate slope
            if x2 - x1 == 0:
                continue
            slope = (y2 - y1) / (x2 - x1)
            
            # Filter by slope (ignore nearly horizontal lines)
            if abs(slope) < 0.3:
                continue
            
            if slope < 0:  # Left lane (negative slope in image coords)
                left_lines.append((x1, y1, x2, y2))
            else:  # Right lane (positive slope)
                right_lines.append((x1, y1, x2, y2))
    
    # Draw detected lines
    for x1, y1, x2, y2 in left_lines:
        cv2.line(output, (x1, y1), (x2, y2), (255, 0, 0), 3)  # Blue for left
    
    for x1, y1, x2, y2 in right_lines:
        cv2.line(output, (x1, y1), (x2, y2), (0, 0, 255), 3)  # Red for right
    
    # Calculate center line if we have both lanes
    steering_direction = "STRAIGHT"
    if left_lines and right_lines:
        # Average x position of left and right lanes at bottom
        left_x = np.mean([x1 for x1, y1, x2, y2 in left_lines])
        right_x = np.mean([x1 for x1, y1, x2, y2 in right_lines])
        lane_center = (left_x + right_x) / 2
        image_center = width / 2
        
        offset = lane_center - image_center
        if offset < -30:
            steering_direction = "LEFT"
        elif offset > 30:
            steering_direction = "RIGHT"
        
        # Draw center guidance line
        cv2.line(output, (int(lane_center), height), 
                (int(lane_center), int(height * 0.7)), (0, 255, 0), 3)
    
    # Display info
    cv2.putText(output, f"Left lanes: {len(left_lines)}", (10, 30),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
    cv2.putText(output, f"Right lanes: {len(right_lines)}", (10, 60),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    cv2.putText(output, f"Steer: {steering_direction}", (10, 90),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    return output, edges, masked_edges


def main():
    os.system('cls')
    print("="*60)
    print("  QCar 2 Lane Detection - CITYSCAPE")
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
    
    # Spawn QCar at a good position
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
    
    print("\n" + "="*60)
    print("  Lane Detection Running!")
    print("  Press ESC to exit")
    print("  Press 'e' to toggle edge view")
    print("="*60)
    
    cv2.namedWindow("Lane Detection", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Lane Detection", 800, 600)
    
    show_edges = False
    
    while True:
        # Get front camera image
        success, image = car.get_image(camera=car.CAMERA_CSI_FRONT)
        
        if success and image is not None:
            # Detect lanes
            output, edges, masked_edges = detect_lanes(image)
            
            if show_edges:
                # Show edge detection
                edges_color = cv2.cvtColor(masked_edges, cv2.COLOR_GRAY2BGR)
                combined = np.hstack([output, edges_color])
                cv2.imshow("Lane Detection", combined)
            else:
                cv2.imshow("Lane Detection", output)
        
        # Check for key presses
        key = cv2.waitKey(30) & 0xFF
        
        if key == 27:  # ESC
            break
        elif key == ord('e'):
            show_edges = not show_edges
            print(f"  Edge view: {'ON' if show_edges else 'OFF'}")
    
    cv2.destroyAllWindows()
    print("\n🛑 Lane detection stopped")
    qlabs.close()
    print("✅ Done!")


if __name__ == '__main__':
    main()
