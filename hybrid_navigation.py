"""
QCar 2 Hybrid Navigation - ACC 2026
Entry point script that uses modular components.

Two navigation modes:
1. WAYPOINT: Drive toward target coordinates (when no lanes)
2. LANE: Follow detected lanes (when on road with markings)

Features:
- Zone-aware navigation (lane following, waypoint, roundabout, etc.)
- State machine for taxi operations (LED colors, wait times)
- Hysteresis-based mode switching (prevents flickering)
- Smooth speed control (gradual acceleration/deceleration)
- HSV + perspective transform lane detection
- Multi-camera support (side awareness)
- Traffic light/stop sign detection
- Telemetry logging

*** Run in OPEN WORLD workspace (not Cityscape) ***
"""

import os
import time
import cv2
import numpy as np
import keyboard
import math
from typing import Optional, Tuple

# QLabs imports
from qvl.qlabs import QuanserInteractiveLabs
from qvl.qcar2 import QLabsQCar2
from qvl.free_camera import QLabsFreeCamera
from qvl.walls import QLabsWalls
from qvl.qcar_flooring import QLabsQCarFlooring
from qvl.crosswalk import QLabsCrosswalk
from qvl.basic_shape import QLabsBasicShape
from qvl.stop_sign import QLabsStopSign
from qvl.yield_sign import QLabsYieldSign
from qvl.roundabout_sign import QLabsRoundaboutSign
from qvl.traffic_light import QLabsTrafficLight
from qvl.animal import QLabsAnimal

# Modular components
from navigation import HybridNavigator, SpeedController, NavigationMode, PATHS
from perception import MultiCameraManager, TrafficLightState
from state import TaxiState, LED_COLORS, NavigationZone
from utils import SafetyMonitor, load_config, TelemetryLogger, create_logger_from_config

# Road feature detection (Phase 3)
from road_features import NavigationAdvisor, RoadType


# =============================================================================
# CONFIGURATION
# =============================================================================

# Toggle cow spawning (disabled by default to reduce visual clutter)
SPAWN_COWS = False


# =============================================================================
# ENVIRONMENT SETUP
# =============================================================================

def spawn_waypoint_markers(qlabs):
    """Spawn colored cubes at each waypoint to visualize navigation paths."""
    shape = QLabsBasicShape(qlabs)

    # Color mapping for each path (RGB normalized 0-1)
    path_colors = {
        'hub_to_pickup': [0, 1, 0],      # Green - route to pickup
        'pickup_to_dropoff': [0, 0, 1],  # Blue - route to dropoff
        'dropoff_to_hub': [1, 0, 1],     # Magenta - route back to hub
    }

    marker_id = 100  # Start ID for markers
    marker_scale = 0.03  # Small cubes
    marker_height = 0.3  # Float above car to avoid collision

    for path_name, waypoints in PATHS.items():
        color = path_colors.get(path_name, [1, 1, 1])

        for i, wp in enumerate(waypoints):
            x, y = wp[0], wp[1]

            # Spawn cube marker
            shape.spawn_id(
                actorNumber=marker_id,
                location=[x, y, marker_height],
                rotation=[0, 0, 0],
                scale=[marker_scale, marker_scale, marker_scale],
                configuration=shape.SHAPE_CUBE,
                waitForConfirmation=False
            )

            # Set color
            shape.set_material_properties(
                color=color,
                roughness=0.5,
                metallic=False
            )

            marker_id += 1

    # Add larger markers at key locations (Hub, Pickup, Dropoff)
    key_locations = [
        ([-1.205, -0.83], [1, 0, 1], "Hub"),      # Magenta - Hub
        ([0.125, 4.395], [0, 1, 1], "Pickup"),    # Cyan - Pickup
        ([-0.905, 0.800], [1, 0.5, 0], "Dropoff"), # Orange - Dropoff
    ]

    for pos, color, name in key_locations:
        shape.spawn_id(
            actorNumber=marker_id,
            location=[pos[0], pos[1], 0.4],  # Float above car to avoid collision
            rotation=[0, 0, 0],
            scale=[0.06, 0.06, 0.06],  # Larger cube
            configuration=shape.SHAPE_CUBE,
            waitForConfirmation=False
        )
        shape.set_material_properties(color=color, roughness=0.3, metallic=False)
        marker_id += 1
        print(f"    {name}: [{pos[0]:.2f}, {pos[1]:.2f}]")


def setup_environment(qlabs):
    """Spawn the competition environment (Walls, Floors, Signs)."""
    print("  Setting up Taxi Hub Environment (Floors, Walls, Signs)...")

    # Offsets from base scenario
    x_offset = 0.13
    y_offset = 1.67

    # Flooring (the competition mat - no scale, it's already correct size)
    hFloor = QLabsQCarFlooring(qlabs)
    hFloor.spawn_degrees([x_offset, y_offset, 0.001], rotation=[0, 0, -90])

    # Walls (boundaries - no scale needed)
    hWall = QLabsWalls(qlabs)
    hWall.set_enable_dynamics(False)

    # Wall loops
    for y in range(5):
        hWall.spawn_degrees(location=[-2.4 + x_offset, (-y*1.0)+2.55 + y_offset, 0.001], rotation=[0, 0, 0])
    for x in range(5):
        hWall.spawn_degrees(location=[-1.9+x + x_offset, 3.05+ y_offset, 0.001], rotation=[0, 0, 90])
    for y in range(6):
        hWall.spawn_degrees(location=[2.4+ x_offset, (-y*1.0)+2.55 + y_offset, 0.001], rotation=[0, 0, 0])
    for x in range(4):
        hWall.spawn_degrees(location=[-0.9+x+ x_offset, -3.05+ y_offset, 0.001], rotation=[0, 0, 90])

    # Angled walls
    hWall.spawn_degrees(location=[-2.03 + x_offset, -2.275+ y_offset, 0.001], rotation=[0, 0, 48])
    hWall.spawn_degrees(location=[-1.575+ x_offset, -2.7+ y_offset, 0.001], rotation=[0, 0, 48])

    # Crosswalk
    myCrossWalk = QLabsCrosswalk(qlabs)
    myCrossWalk.spawn_degrees(location=[-2 + x_offset, -1.475 + y_offset, 0.01],
                             rotation=[0,0,0], scale=[0.1,0.1,0.075], configuration=0)

    # --- SIGNS (from Setup_Real_Scenario.py) ---
    print("  Spawning Signs & Lights...")

    # Yield Sign (The one near start)
    myYieldSign = QLabsYieldSign(qlabs)
    myYieldSign.spawn_degrees(location=[0.0, -1.3, 0.006], rotation=[0, 0, -180], scale=[0.1, 0.1, 0.1], waitForConfirmation=False)

    # Stop Signs
    myStopSign = QLabsStopSign(qlabs)
    myStopSign.spawn_degrees(location=[-1.5, 3.6, 0.006], rotation=[0, 0, -35], scale=[0.1, 0.1, 0.1], waitForConfirmation=False)
    myStopSign.spawn_degrees(location=[-1.5, 2.2, 0.006], rotation=[0, 0, 35], scale=[0.1, 0.1, 0.1], waitForConfirmation=False)
    myStopSign.spawn_degrees(location=[2.410, 0.206, 0.006], rotation=[0, 0, -90], scale=[0.1, 0.1, 0.1], waitForConfirmation=False)
    myStopSign.spawn_degrees(location=[1.766, 1.697, 0.006], rotation=[0, 0, 90], scale=[0.1, 0.1, 0.1], waitForConfirmation=False)

    # Roundabout Signs
    myRoundaboutSign = QLabsRoundaboutSign(qlabs)
    myRoundaboutSign.spawn_degrees(location=[2.392, 2.522, 0.006], rotation=[0, 0, -90], scale=[0.1, 0.1, 0.1], waitForConfirmation=False)
    myRoundaboutSign.spawn_degrees(location=[0.698, 2.483, 0.006], rotation=[0, 0, -145], scale=[0.1, 0.1, 0.1], waitForConfirmation=False)
    myRoundaboutSign.spawn_degrees(location=[0.007, 3.973, 0.006], rotation=[0, 0, 135], scale=[0.1, 0.1, 0.1], waitForConfirmation=False)

    # Traffic Lights (Spawn only, no cycling logic to avoid blocking)
    tl = QLabsTrafficLight(qlabs)
    tl.spawn_id_degrees(actorNumber=1, location=[0.6, 1.55, 0.006], rotation=[0,0,0], scale=[0.1, 0.1, 0.1], configuration=0, waitForConfirmation=False)
    tl.spawn_id_degrees(actorNumber=2, location=[-0.6, 1.28, 0.006], rotation=[0,0,90], scale=[0.1, 0.1, 0.1], configuration=0, waitForConfirmation=False)
    tl.spawn_id_degrees(actorNumber=3, location=[-0.37, 0.3, 0.006], rotation=[0,0,180], scale=[0.1, 0.1, 0.1], configuration=0, waitForConfirmation=False)
    tl.spawn_id_degrees(actorNumber=4, location=[0.75, 0.48, 0.006], rotation=[0,0,-90], scale=[0.1, 0.1, 0.1], configuration=0, waitForConfirmation=False)

    # --- COWS! ---
    if SPAWN_COWS:
        print("  Spawning Cows...")
        cow = QLabsAnimal(qlabs)
        # Spawn a few cows near the road (configuration 0 = cow)
        cow.spawn_degrees(location=[1.5, 2.5, 0.01], rotation=[0, 0, 45], scale=[0.1, 0.1, 0.1], configuration=0, waitForConfirmation=False)
        cow.spawn_degrees(location=[1.8, 2.2, 0.01], rotation=[0, 0, -30], scale=[0.1, 0.1, 0.1], configuration=0, waitForConfirmation=False)
        cow.spawn_degrees(location=[-1.8, 3.0, 0.01], rotation=[0, 0, 120], scale=[0.1, 0.1, 0.1], configuration=0, waitForConfirmation=False)

    print("  Environment & Signs Spawned")

    # --- WAYPOINT MARKERS (for debugging navigation) ---
    print("  Spawning Waypoint Markers...")
    spawn_waypoint_markers(qlabs)

    # Spawn Birds Eye Camera to verify setup
    print("  Spawning Overhead Camera...")
    camera_loc = [0.15, 1.7, 5]   # From official setup
    camera_rot = [0, 90, 0]       # Looking down
    cam = QLabsFreeCamera(qlabs)
    cam.spawn_degrees(location=camera_loc, rotation=camera_rot)
    # Start with overhead view for better visualization
    cam.possess()

    return cam


# =============================================================================
# MAIN LOOP
# =============================================================================

def main():
    os.system('cls')
    print("=" * 60)
    print("  QCar 2 HYBRID Navigation - ACC 2026")
    print("  Modular Architecture with Zone-Based Navigation")
    print("=" * 60)

    # Load configuration
    config = load_config()
    print("\nConfiguration loaded from config.yaml")

    # Initialize telemetry logger
    telemetry = create_logger_from_config(config._config)

    qlabs = QuanserInteractiveLabs()
    print("\nConnecting to QLabs...")

    if not qlabs.open("localhost"):
        print("Could not connect!")
        return

    print("Connected!")

    qlabs.destroy_all_spawned_actors()
    time.sleep(0.5)

    # Setup Competition Environment (Walls/Floor) - returns overhead camera
    overhead_cam = setup_environment(qlabs)

    print("Spawning QCar...")
    car = QLabsQCar2(qlabs)
    car.spawn_id_degrees(
        actorNumber=0,
        location=[-1.205, -0.83, 0.005],  # Taxi Hub (Competition Start)
        rotation=[0, 0, -44.7],            # Correct Orientation
        scale=[0.1, 0.1, 0.1],             # Competition scale
        configuration=0,
        waitForConfirmation=True
    )

    # Give QLabs time to initialize the actor and cameras
    print("Waiting 5s for cameras to initialize...")
    time.sleep(5.0)

    # Initialize components from config
    speed_config = config.get('speed', {})
    navigator = HybridNavigator(
        traffic_detection_enabled=False,  # Toggle with 'T' key
        road_feature_enabled=False,       # Toggle with 'R' key
    )
    speed_controller = SpeedController(
        max_speed=speed_config.get('max_speed', 0.35) if isinstance(speed_config, dict) else 0.35,
        min_speed=speed_config.get('min_speed', 0.0) if isinstance(speed_config, dict) else 0.0,
        accel_rate=speed_config.get('accel_rate', 0.15) if isinstance(speed_config, dict) else 0.15,
        decel_rate=speed_config.get('decel_rate', 0.25) if isinstance(speed_config, dict) else 0.25,
    )
    safety_config = config.get('safety', {})
    safety_monitor = SafetyMonitor(
        stuck_threshold=safety_config.get('stuck_threshold', 5.0) if isinstance(safety_config, dict) else 5.0,
        min_total_movement=safety_config.get('min_total_movement', 0.1) if isinstance(safety_config, dict) else 0.1,
    )
    camera_manager = MultiCameraManager(car)

    # Road feature detection (Phase 3 - disabled by default)
    road_advisor = NavigationAdvisor()
    road_feature_enabled = False
    current_road_type = RoadType.STRAIGHT
    road_speed_multiplier = 1.0

    # State machine
    wait_start_time = 0.0
    WAIT_DURATION = 3.0

    # Start with first waypoint (Pickup)
    navigator.current_waypoint_idx = -1  # Will become 0 after next_waypoint()
    current_wp = navigator.next_waypoint()
    taxi_state = current_wp['state']  # EN_ROUTE_TO_PICKUP

    # Set initial LED
    car.set_led_strip_uniform(LED_COLORS[taxi_state])

    # Start telemetry session
    telemetry.start_session()

    print("\n" + "=" * 60)
    print("  CONTROLS:")
    print("  Arrow keys / WASD = Manual control")
    print("  A = Toggle autonomous")
    print("  N = Next waypoint")
    print("  M = Toggle multi-camera view")
    print("  D = Toggle debug visualization")
    print("  T = Toggle traffic light detection")
    print("  R = Toggle road feature detection")
    print("  Q = Quit")
    print("=" * 60)
    print("\n  TIP: Press D to see lane detection debug windows!")

    # Car camera window
    cv2.namedWindow("Car Camera - Hybrid Navigation", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Car Camera - Hybrid Navigation", 800, 600)

    turn = 0.0
    autonomous = False
    show_multicam = False
    stopped_for_traffic = False
    traffic_stop_reason = ""

    running = True
    while running:
        # --- Input Handling ---
        if keyboard.is_pressed('q'):
            running = False
        elif keyboard.is_pressed('m'):
            show_multicam = not show_multicam
            print(f"\n  Multi-camera: {'ON' if show_multicam else 'OFF'}")
            time.sleep(0.2)
        elif keyboard.is_pressed('a'):
            autonomous = not autonomous
            if autonomous:
                speed_controller.set_target(speed_controller.max_speed)
                taxi_state = current_wp['state']
                car.set_led_strip_uniform(LED_COLORS[taxi_state])
                print(f"\n  AUTONOMOUS: ON - State: {taxi_state.name}")
            else:
                speed_controller.stop()
                print("\n  AUTONOMOUS: OFF")
            time.sleep(0.2)
        elif keyboard.is_pressed('n'):
            current_wp = navigator.next_waypoint()
            taxi_state = current_wp['state']
            car.set_led_strip_uniform(LED_COLORS[taxi_state])
            print(f"\n  Target: {current_wp['name']} - State: {taxi_state.name}")
            time.sleep(0.2)
        elif keyboard.is_pressed('d'):
            debug_on = navigator.toggle_debug()
            print(f"\n  Debug mode: {'ON' if debug_on else 'OFF'}")
            time.sleep(0.2)
        elif keyboard.is_pressed('t'):
            traffic_on = navigator.toggle_traffic_detection()
            print(f"\n  Traffic detection: {'ON' if traffic_on else 'OFF'}")
            time.sleep(0.2)
        elif keyboard.is_pressed('r'):
            road_feature_enabled = not road_feature_enabled
            print(f"\n  Road feature detection: {'ON' if road_feature_enabled else 'OFF'}")
            time.sleep(0.2)

        # --- Manual Control ---
        if not autonomous:
            # Speed control - supports both arrow keys and WASD
            if keyboard.is_pressed('up') or keyboard.is_pressed('w'):
                speed_controller.current_speed = 1.0  # Faster forward
            elif keyboard.is_pressed('down') or keyboard.is_pressed('s'):
                speed_controller.current_speed = -0.5  # Reverse
            else:
                speed_controller.current_speed = 0.0

            # Steering control - supports both arrow keys and WASD
            if keyboard.is_pressed('left'):
                turn = -0.5  # Turn left (negative)
            elif keyboard.is_pressed('right'):
                turn = 0.5   # Turn right (positive)
            elif keyboard.is_pressed('space'):
                turn = 0.0
                speed_controller.current_speed = 0.0
            else:
                # Gradual return to center when no key pressed
                turn = turn * 0.7

        # --- Get Camera Image ---
        success, image = car.get_image(camera=car.CAMERA_CSI_FRONT)

        # --- Get Car State ---
        s_loc, loc, rot, scale = car.get_world_transform()

        if s_loc:
            heading_rad = math.radians(rot[2])
            car_state = {
                'x': loc[0],
                'y': loc[1],
                'z': loc[2],
                'heading': heading_rad
            }
            safety_monitor.update(loc[0], loc[1])
        else:
            car_state = {'x': 0, 'y': 0, 'z': 0, 'heading': 0}

        # --- Process Navigation ---
        if success and image is not None:
            steering, annotated, detection_info = navigator.process(image, car_state)

            # Road feature detection (Phase 3) - for speed adjustment
            if road_feature_enabled:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                blur = cv2.GaussianBlur(gray, (5, 5), 0)
                edges = cv2.Canny(blur, 50, 150)
                feature = road_advisor.update(edges, image)
                current_road_type = feature.road_type
                road_speed_multiplier = feature.recommended_speed

            if autonomous:
                turn = steering

                # Get base speed from zone-based recommendations
                base_speed = speed_controller.max_speed * navigator.get_recommended_speed_factor()

                # Apply road feature speed multiplier (Phase 3)
                if road_feature_enabled:
                    base_speed *= road_speed_multiplier

                # Check for traffic stops
                should_stop, stop_reason = navigator.should_stop_for_traffic()
                if should_stop and not stopped_for_traffic:
                    stopped_for_traffic = True
                    traffic_stop_reason = stop_reason
                    speed_controller.stop()
                    print(f"\n  STOP: {stop_reason}")
                elif not should_stop and stopped_for_traffic:
                    stopped_for_traffic = False
                    traffic_stop_reason = ""
                    speed_controller.set_target(base_speed)

                # Slow for yellow light or approach zones
                if navigator.should_slow_for_traffic():
                    base_speed *= 0.5

                if not stopped_for_traffic:
                    speed_controller.set_target(base_speed)

                # State machine handling
                _, dist = navigator.waypoint_nav.calculate_steering()

                # Slow down when approaching waypoint
                if dist < 0.5:
                    speed_controller.slow_approach(dist)

                # Check arrival based on state
                if taxi_state in [TaxiState.EN_ROUTE_TO_PICKUP,
                                  TaxiState.EN_ROUTE_TO_DROPOFF,
                                  TaxiState.RETURNING_TO_HUB]:

                    if navigator.check_arrival(dist):
                        # Transition to arrival state
                        taxi_state = current_wp['arrival_state']
                        car.set_led_strip_uniform(LED_COLORS[taxi_state])
                        speed_controller.stop()
                        wait_start_time = time.time()
                        print(f"\n  ARRIVED: {current_wp['name']} - State: {taxi_state.name}")

                elif taxi_state in [TaxiState.AT_PICKUP, TaxiState.AT_DROPOFF]:
                    # Waiting at location
                    speed_controller.stop()
                    elapsed = time.time() - wait_start_time

                    if elapsed > WAIT_DURATION:
                        # Move to next waypoint
                        current_wp = navigator.next_waypoint()
                        taxi_state = current_wp['state']
                        car.set_led_strip_uniform(LED_COLORS[taxi_state])
                        speed_controller.set_target(speed_controller.max_speed)
                        print(f"\n  DEPARTING: Next target {current_wp['name']} - State: {taxi_state.name}")

                elif taxi_state == TaxiState.WAITING_AT_HUB:
                    # Completed full cycle
                    speed_controller.stop()
                    print("\n" + "="*50)
                    print("  MISSION COMPLETE - Back at Hub!")
                    print("="*50)

            # --- Annotate Display ---
            h, w = annotated.shape[:2]
            current_speed = speed_controller.update()

            # TOP BAR - Mission progress
            cv2.rectangle(annotated, (0, 0), (w, 35), (40, 40, 40), -1)
            mission_text = f"TAXI: Hub -> Pickup -> Dropoff -> Hub | Now: {taxi_state.name.replace('_', ' ')}"
            cv2.putText(annotated, mission_text, (10, 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            # RIGHT SIDE - State info (spaced at 25px intervals)
            rx = w - 200  # Right column X position
            ry = 50       # Starting Y position (below top bar)

            state_color = {
                TaxiState.WAITING_AT_HUB: (255, 0, 255),
                TaxiState.EN_ROUTE_TO_PICKUP: (0, 255, 0),
                TaxiState.AT_PICKUP: (255, 0, 0),
                TaxiState.EN_ROUTE_TO_DROPOFF: (0, 255, 0),
                TaxiState.AT_DROPOFF: (0, 165, 255),
                TaxiState.RETURNING_TO_HUB: (0, 255, 0),
                TaxiState.STOPPED: (0, 0, 255),
            }.get(taxi_state, (255, 255, 255))

            cv2.putText(annotated, taxi_state.name, (rx, ry),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, state_color, 1)

            ry += 25
            cv2.putText(annotated, f"Speed: {current_speed:.2f}", (rx, ry),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 200, 0), 1)

            ry += 25
            cv2.putText(annotated, f"Curve: {navigator.lane_detector.curvature:.2f}", (rx, ry),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

            # Road feature info (Phase 3)
            if road_feature_enabled:
                ry += 25
                road_type = current_road_type
                road_mult = road_speed_multiplier
                road_color = {
                    RoadType.STRAIGHT: (0, 255, 0),
                    RoadType.CURVE_LEFT: (0, 165, 255),
                    RoadType.CURVE_RIGHT: (0, 165, 255),
                    RoadType.INTERSECTION: (0, 0, 255),
                    RoadType.ROUNDABOUT: (255, 0, 255),
                    RoadType.PARKING: (255, 255, 0),
                }.get(road_type, (200, 200, 200))
                cv2.putText(annotated, f"Road: {road_type.name}", (rx, ry),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, road_color, 1)
                ry += 20
                cv2.putText(annotated, f"Spd x{road_mult:.0%}", (rx, ry),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, road_color, 1)

            # Center screen overlays - BIG STATUS ALERTS
            if taxi_state == TaxiState.AT_PICKUP:
                elapsed = time.time() - wait_start_time
                remaining = max(0, WAIT_DURATION - elapsed)
                # Big blue box
                cv2.rectangle(annotated, (w//2 - 150, h//2 - 50), (w//2 + 150, h//2 + 50), (255, 0, 0), -1)
                cv2.putText(annotated, "PICKUP", (w//2 - 60, h//2 - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
                cv2.putText(annotated, f"Waiting {remaining:.1f}s", (w//2 - 70, h//2 + 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            elif taxi_state == TaxiState.AT_DROPOFF:
                elapsed = time.time() - wait_start_time
                remaining = max(0, WAIT_DURATION - elapsed)
                # Big orange box
                cv2.rectangle(annotated, (w//2 - 150, h//2 - 50), (w//2 + 150, h//2 + 50), (0, 165, 255), -1)
                cv2.putText(annotated, "DROPOFF", (w//2 - 70, h//2 - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
                cv2.putText(annotated, f"Waiting {remaining:.1f}s", (w//2 - 70, h//2 + 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            elif taxi_state == TaxiState.WAITING_AT_HUB:
                # Big magenta box
                cv2.rectangle(annotated, (w//2 - 150, h//2 - 50), (w//2 + 150, h//2 + 50), (255, 0, 255), -1)
                cv2.putText(annotated, "MISSION", (w//2 - 60, h//2 - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
                cv2.putText(annotated, "COMPLETE!", (w//2 - 70, h//2 + 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

            if stopped_for_traffic:
                cv2.putText(annotated, f"STOP: {traffic_stop_reason}",
                           (w // 2 - 60, h // 2),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            if safety_monitor.is_stuck:
                cv2.putText(annotated, "STUCK!",
                           (w // 2 - 40, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            # --- Log Telemetry ---
            telemetry.log_frame(
                x=car_state.get('x', 0),
                y=car_state.get('y', 0),
                heading=car_state.get('heading', 0),
                speed=current_speed,
                steering=turn,
                taxi_state=taxi_state.name,
                nav_zone=navigator.current_zone.name,
                nav_mode="AUTONOMOUS" if autonomous else "MANUAL",
                lane_confidence=detection_info.get('lane_confidence', 0),
                curvature=detection_info.get('curvature', 0),
                traffic_light=detection_info.get('traffic_light', TrafficLightState.NONE).name,
                distance_to_waypoint=detection_info.get('waypoint_distance', 0),
                waypoint_name=current_wp.get('name', '') if current_wp else '',
            )
            telemetry.add_video_frame(annotated)

            # --- Display ---
            if show_multicam:
                strip = camera_manager.create_surround_strip(size=(200, 150))
                annotated_resized = cv2.resize(annotated, (strip.shape[1], 300))
                combined = np.vstack([annotated_resized, strip])
                cv2.imshow("Car Camera - Hybrid Navigation", combined)
            else:
                cv2.imshow("Car Camera - Hybrid Navigation", annotated)

        else:
            # Camera failed
            if show_multicam:
                strip = camera_manager.create_surround_strip(size=(200, 150))
                dummy = np.zeros((300, strip.shape[1], 3), dtype=np.uint8)
                cv2.putText(dummy, "FRONT CAMERA FAILED", (200, 130),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                combined = np.vstack([dummy, strip])
                cv2.imshow("Car Camera - Hybrid Navigation", combined)
            else:
                dummy = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(dummy, "NO CAMERA SIGNAL", (200, 240),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                cv2.imshow("Car Camera - Hybrid Navigation", dummy)

        # --- Apply Control ---
        current_speed = speed_controller.update()
        car.set_velocity_and_request_state(
            forward=current_speed,
            turn=turn,
            headlights=False,  # Disabled - interferes with lane detection
            leftTurnSignal=(turn < -0.1),
            rightTurnSignal=(turn > 0.1),
            brakeSignal=(current_speed == 0),
            reverseSignal=(current_speed < 0)
        )

        key = cv2.waitKey(30) & 0xFF
        if key == 27:
            running = False

    # Cleanup
    car.set_velocity_and_request_state(0, 0, False, False, False, True, False)
    cv2.destroyAllWindows()
    telemetry.end_session()
    print("\nStopped!")
    qlabs.close()
    print("Done!")


if __name__ == '__main__':
    main()
