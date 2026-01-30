"""
Competition Scenario Setup - ACC 2026 Self-Driving Car Competition
Based on official Setup_Real_Scenario.py from Quanser

*** USE WITH OPEN WORLD WORKSPACE - NOT CITYSCAPE ***

This script sets up the complete competition environment including:
- Competition flooring (roadmap)
- Walls (boundaries)
- Traffic lights at intersection
- Stop signs, yield signs, roundabout signs
- Crosswalks
- QCar 2 at taxi hub starting position
"""

import os
import time

# Environment objects
from qvl.qlabs import QuanserInteractiveLabs
from qvl.qcar2 import QLabsQCar2
from qvl.free_camera import QLabsFreeCamera
from qvl.real_time import QLabsRealTime
from qvl.basic_shape import QLabsBasicShape
from qvl.system import QLabsSystem
from qvl.walls import QLabsWalls
from qvl.qcar_flooring import QLabsQCarFlooring
from qvl.stop_sign import QLabsStopSign
from qvl.yield_sign import QLabsYieldSign
from qvl.roundabout_sign import QLabsRoundaboutSign
from qvl.crosswalk import QLabsCrosswalk
from qvl.traffic_light import QLabsTrafficLight


# Competition coordinates from the detailed scenario
TAXI_HUB_POSITION = [-1.205, -0.83, 0.005]
TAXI_HUB_ROTATION = [0, 0, -44.7]  # degrees
PICKUP_COORDINATE = [0.125, 4.395]  # meters
DROPOFF_COORDINATE = [-0.905, 0.800]  # meters


def setup_environment(qlabs, initial_position=TAXI_HUB_POSITION, initial_rotation=TAXI_HUB_ROTATION):
    """
    Set up the complete competition environment.
    """
    
    # Set the workspace title
    hSystem = QLabsSystem(qlabs)
    hSystem.set_title_string('ACC Self Driving Car Competition', waitForConfirmation=True)
    
    # Flooring offset (competition specific)
    x_offset = 0.13
    y_offset = 1.67
    
    # === FLOORING ===
    print("  - Spawning flooring...")
    hFloor = QLabsQCarFlooring(qlabs)
    hFloor.spawn_degrees([x_offset, y_offset, 0.001], rotation=[0, 0, -90])
    
    # === WALLS (Boundaries) ===
    print("  - Spawning walls...")
    hWall = QLabsWalls(qlabs)
    hWall.set_enable_dynamics(False)
    
    for y in range(5):
        hWall.spawn_degrees(location=[-2.4 + x_offset, (-y*1.0)+2.55 + y_offset, 0.001], rotation=[0, 0, 0])
    for x in range(5):
        hWall.spawn_degrees(location=[-1.9+x + x_offset, 3.05 + y_offset, 0.001], rotation=[0, 0, 90])
    for y in range(6):
        hWall.spawn_degrees(location=[2.4 + x_offset, (-y*1.0)+2.55 + y_offset, 0.001], rotation=[0, 0, 0])
    for x in range(4):
        hWall.spawn_degrees(location=[-0.9+x + x_offset, -3.05 + y_offset, 0.001], rotation=[0, 0, 90])
    hWall.spawn_degrees(location=[-2.03 + x_offset, -2.275 + y_offset, 0.001], rotation=[0, 0, 48])
    hWall.spawn_degrees(location=[-1.575 + x_offset, -2.7 + y_offset, 0.001], rotation=[0, 0, 48])
    
    # === STOP SIGNS ===
    print("  - Spawning signs...")
    myStopSign = QLabsStopSign(qlabs)
    myStopSign.spawn_degrees(location=[-1.5, 3.6, 0.006], rotation=[0, 0, -35], scale=[0.1, 0.1, 0.1])
    myStopSign.spawn_degrees(location=[-1.5, 2.2, 0.006], rotation=[0, 0, 35], scale=[0.1, 0.1, 0.1])
    myStopSign.spawn_degrees(location=[2.410, 0.206, 0.006], rotation=[0, 0, -90], scale=[0.1, 0.1, 0.1])
    myStopSign.spawn_degrees(location=[1.766, 1.697, 0.006], rotation=[0, 0, 90], scale=[0.1, 0.1, 0.1])
    
    # === ROUNDABOUT SIGNS ===
    myRoundaboutSign = QLabsRoundaboutSign(qlabs)
    myRoundaboutSign.spawn_degrees(location=[2.392, 2.522, 0.006], rotation=[0, 0, -90], scale=[0.1, 0.1, 0.1])
    myRoundaboutSign.spawn_degrees(location=[0.698, 2.483, 0.006], rotation=[0, 0, -145], scale=[0.1, 0.1, 0.1])
    myRoundaboutSign.spawn_degrees(location=[0.007, 3.973, 0.006], rotation=[0, 0, 135], scale=[0.1, 0.1, 0.1])
    
    # === YIELD SIGNS ===
    myYieldSign = QLabsYieldSign(qlabs)
    myYieldSign.spawn_degrees(location=[0.0, -1.3, 0.006], rotation=[0, 0, -180], scale=[0.1, 0.1, 0.1])
    myYieldSign.spawn_degrees(location=[2.4, 3.2, 0.006], rotation=[0, 0, -90], scale=[0.1, 0.1, 0.1])
    myYieldSign.spawn_degrees(location=[1.1, 2.8, 0.006], rotation=[0, 0, -145], scale=[0.1, 0.1, 0.1])
    myYieldSign.spawn_degrees(location=[0.49, 3.8, 0.006], rotation=[0, 0, 135], scale=[0.1, 0.1, 0.1])
    
    # === CROSSWALKS ===
    print("  - Spawning crosswalks...")
    myCrossWalk = QLabsCrosswalk(qlabs)
    myCrossWalk.spawn_degrees(location=[-2 + x_offset, -1.475 + y_offset, 0.01], rotation=[0,0,0], scale=[0.1,0.1,0.075])
    myCrossWalk.spawn_degrees(location=[-0.5, 0.95, 0.006], rotation=[0,0,90], scale=[0.1,0.1,0.075])
    myCrossWalk.spawn_degrees(location=[0.15, 0.32, 0.006], rotation=[0,0,0], scale=[0.1,0.1,0.075])
    myCrossWalk.spawn_degrees(location=[0.75, 0.95, 0.006], rotation=[0,0,90], scale=[0.1,0.1,0.075])
    myCrossWalk.spawn_degrees(location=[0.13, 1.57, 0.006], rotation=[0,0,0], scale=[0.1,0.1,0.075])
    myCrossWalk.spawn_degrees(location=[1.45, 0.95, 0.006], rotation=[0,0,90], scale=[0.1,0.1,0.075])
    
    # === LINE GUIDANCE ===
    mySpline = QLabsBasicShape(qlabs)
    mySpline.spawn_degrees(location=[2.21, 0.2, 0.006], rotation=[0, 0, 0], scale=[0.27, 0.02, 0.001])
    mySpline.spawn_degrees(location=[1.951, 1.68, 0.006], rotation=[0, 0, 0], scale=[0.27, 0.02, 0.001])
    mySpline.spawn_degrees(location=[-0.05, -1.02, 0.006], rotation=[0, 0, 90], scale=[0.38, 0.02, 0.001])
    
    # === QCAR 2 ===
    print("  - Spawning QCar 2...")
    car = QLabsQCar2(qlabs)
    car.spawn_id_degrees(
        actorNumber=0,
        location=initial_position,
        rotation=initial_rotation,
        scale=[0.1, 0.1, 0.1],
        configuration=0,
        waitForConfirmation=True
    )
    
    # === CAMERAS ===
    print("  - Setting up cameras...")
    camera1 = QLabsFreeCamera(qlabs)
    camera1.spawn_degrees(location=[0.15, 1.7, 5], rotation=[0, 90, 0])
    
    camera2 = QLabsFreeCamera(qlabs)
    camera2.spawn_degrees(location=[-0.36 + x_offset, -3.691 + y_offset, 2.652], rotation=[0, 47, 90])
    camera2.possess()
    
    return car


def setup_traffic_lights(qlabs):
    """Set up traffic lights at the intersection."""
    print("  - Spawning traffic lights...")
    
    trafficLight1 = QLabsTrafficLight(qlabs)
    trafficLight2 = QLabsTrafficLight(qlabs)
    trafficLight3 = QLabsTrafficLight(qlabs)
    trafficLight4 = QLabsTrafficLight(qlabs)
    
    trafficLight1.spawn_id_degrees(actorNumber=1, location=[0.6, 1.55, 0.006], rotation=[0,0,0], scale=[0.1, 0.1, 0.1], configuration=0)
    trafficLight2.spawn_id_degrees(actorNumber=2, location=[-0.6, 1.28, 0.006], rotation=[0,0,90], scale=[0.1, 0.1, 0.1], configuration=0)
    trafficLight3.spawn_id_degrees(actorNumber=3, location=[-0.37, 0.3, 0.006], rotation=[0,0,180], scale=[0.1, 0.1, 0.1], configuration=0)
    trafficLight4.spawn_id_degrees(actorNumber=4, location=[0.75, 0.48, 0.006], rotation=[0,0,-90], scale=[0.1, 0.1, 0.1], configuration=0)
    
    return [trafficLight1, trafficLight2, trafficLight3, trafficLight4]


def run_traffic_light_loop(traffic_lights):
    """Run the traffic light sequence."""
    intersection_flag = 0
    print('\n� Traffic lights cycling (5 second intervals)')
    
    while True:
        tl1, tl2, tl3, tl4 = traffic_lights
        
        if intersection_flag == 0:
            tl1.set_color(color=QLabsTrafficLight.COLOR_RED)
            tl3.set_color(color=QLabsTrafficLight.COLOR_RED)
            tl2.set_color(color=QLabsTrafficLight.COLOR_GREEN)
            tl4.set_color(color=QLabsTrafficLight.COLOR_GREEN)
        elif intersection_flag == 1:
            tl2.set_color(color=QLabsTrafficLight.COLOR_YELLOW)
            tl4.set_color(color=QLabsTrafficLight.COLOR_YELLOW)
        elif intersection_flag == 2:
            tl1.set_color(color=QLabsTrafficLight.COLOR_GREEN)
            tl3.set_color(color=QLabsTrafficLight.COLOR_GREEN)
            tl2.set_color(color=QLabsTrafficLight.COLOR_RED)
            tl4.set_color(color=QLabsTrafficLight.COLOR_RED)
        elif intersection_flag == 3:
            tl1.set_color(color=QLabsTrafficLight.COLOR_YELLOW)
            tl3.set_color(color=QLabsTrafficLight.COLOR_YELLOW)
        
        intersection_flag = (intersection_flag + 1) % 4
        time.sleep(5)


def main():
    os.system('cls')
    print("="*60)
    print("  ACC 2026 Self-Driving Car Competition - Scenario Setup")
    print("="*60)
    print("\n⚠️  Make sure QLabs is running with OPEN WORLD workspace!")
    print("    (Not Cityscape - this script creates its own environment)\n")
    
    qlabs = QuanserInteractiveLabs()
    
    print("Connecting to QLabs...")
    try:
        qlabs.open("localhost")
        print("✅ Connected to QLabs\n")
    except:
        print("❌ Unable to connect to QLabs")
        return
    
    print("Clearing existing actors...")
    qlabs.destroy_all_spawned_actors()
    QLabsRealTime().terminate_all_real_time_models()
    time.sleep(0.5)
    
    print("\nSetting up competition environment...")
    car = setup_environment(qlabs)
    traffic_lights = setup_traffic_lights(qlabs)
    
    print("\n" + "="*60)
    print("  ✅ Competition scenario ready!")
    print("="*60)
    print(f"\n📍 QCar at Taxi Hub: {TAXI_HUB_POSITION}")
    print(f"📍 Pickup coordinate: {PICKUP_COORDINATE}")
    print(f"📍 Dropoff coordinate: {DROPOFF_COORDINATE}")
    print("\nPress Ctrl+C to exit and clean up\n")
    
    try:
        run_traffic_light_loop(traffic_lights)
    except KeyboardInterrupt:
        print("\n\n🛑 Exiting script...")
        print("💡 Objects remain in QLabs - you can interact with them!")
        print("   Run 'python setup_competition.py' again to reset.\n")
        qlabs.close()
        print("✅ Done!")


if __name__ == '__main__':
    main()
