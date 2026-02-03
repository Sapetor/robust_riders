"""
Telemetry logging for ACC 2026 navigation.

Features:
- CSV logging of position, steering, state, zone, detections
- Video recording of annotated camera feed
- Session management with timestamps
"""

import os
import csv
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import cv2
import numpy as np


class TelemetryLogger:
    """
    Logs telemetry data to CSV and optionally records video.

    Usage:
        logger = TelemetryLogger()
        logger.start_session()

        # In main loop:
        logger.log_frame(
            x=loc[0], y=loc[1], heading=heading,
            speed=speed, steering=steering,
            taxi_state="EN_ROUTE_TO_PICKUP",
            nav_zone="LANE_FOLLOWING",
            lane_confidence=0.75,
            detected_signs=["roundabout"]
        )
        logger.add_video_frame(annotated_image)

        logger.end_session()
    """

    def __init__(self,
                 log_directory: str = "logs",
                 save_video: bool = True,
                 video_fps: int = 15,
                 enabled: bool = True):
        """
        Initialize telemetry logger.

        Args:
            log_directory: Directory for log files
            save_video: Whether to record video
            video_fps: Video frame rate
            enabled: Master enable switch
        """
        self.log_directory = Path(log_directory)
        self.save_video = save_video
        self.video_fps = video_fps
        self.enabled = enabled

        self.session_id: Optional[str] = None
        self.csv_file = None
        self.csv_writer = None
        self.video_writer = None
        self.frame_count = 0
        self.start_time = 0.0

        # CSV columns
        self.csv_columns = [
            'timestamp',
            'elapsed',
            'frame',
            'x',
            'y',
            'heading',
            'speed',
            'steering',
            'taxi_state',
            'nav_zone',
            'nav_mode',
            'lane_confidence',
            'curvature',
            'detected_signs',
            'traffic_light',
            'distance_to_waypoint',
            'waypoint_name',
        ]

    def start_session(self, session_name: Optional[str] = None) -> str:
        """
        Start a new logging session.

        Args:
            session_name: Optional custom session name

        Returns:
            Session ID string
        """
        if not self.enabled:
            return ""

        # Create session ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_id = session_name or f"session_{timestamp}"

        # Create log directory
        self.log_directory.mkdir(parents=True, exist_ok=True)

        # Open CSV file
        csv_path = self.log_directory / f"{self.session_id}.csv"
        self.csv_file = open(csv_path, 'w', newline='')
        self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=self.csv_columns)
        self.csv_writer.writeheader()

        # Video will be initialized on first frame (to get dimensions)
        self.video_writer = None

        self.frame_count = 0
        self.start_time = time.time()

        print(f"Telemetry session started: {self.session_id}")
        print(f"  CSV: {csv_path}")

        return self.session_id

    def log_frame(self,
                  x: float = 0.0,
                  y: float = 0.0,
                  heading: float = 0.0,
                  speed: float = 0.0,
                  steering: float = 0.0,
                  taxi_state: str = "",
                  nav_zone: str = "",
                  nav_mode: str = "",
                  lane_confidence: float = 0.0,
                  curvature: float = 0.0,
                  detected_signs: List[str] = None,
                  traffic_light: str = "",
                  distance_to_waypoint: float = 0.0,
                  waypoint_name: str = ""):
        """Log a single frame of telemetry data."""
        if not self.enabled or self.csv_writer is None:
            return

        now = time.time()
        elapsed = now - self.start_time

        row = {
            'timestamp': datetime.now().isoformat(),
            'elapsed': f"{elapsed:.3f}",
            'frame': self.frame_count,
            'x': f"{x:.4f}",
            'y': f"{y:.4f}",
            'heading': f"{heading:.4f}",
            'speed': f"{speed:.3f}",
            'steering': f"{steering:.3f}",
            'taxi_state': taxi_state,
            'nav_zone': nav_zone,
            'nav_mode': nav_mode,
            'lane_confidence': f"{lane_confidence:.3f}",
            'curvature': f"{curvature:.3f}",
            'detected_signs': ','.join(detected_signs or []),
            'traffic_light': traffic_light,
            'distance_to_waypoint': f"{distance_to_waypoint:.3f}",
            'waypoint_name': waypoint_name,
        }

        self.csv_writer.writerow(row)
        self.frame_count += 1

    def add_video_frame(self, frame: np.ndarray):
        """Add a frame to the video recording."""
        if not self.enabled or not self.save_video:
            return

        if self.session_id is None:
            return

        # Initialize video writer on first frame
        if self.video_writer is None:
            h, w = frame.shape[:2]
            video_path = self.log_directory / f"{self.session_id}.mp4"
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.video_writer = cv2.VideoWriter(
                str(video_path), fourcc, self.video_fps, (w, h)
            )
            print(f"  Video: {video_path}")

        self.video_writer.write(frame)

    def end_session(self):
        """End the current logging session."""
        if self.csv_file:
            self.csv_file.close()
            self.csv_file = None
            self.csv_writer = None

        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None

        if self.session_id:
            elapsed = time.time() - self.start_time
            print(f"Telemetry session ended: {self.session_id}")
            print(f"  Frames: {self.frame_count}")
            print(f"  Duration: {elapsed:.1f}s")

        self.session_id = None

    def __del__(self):
        """Cleanup on deletion."""
        self.end_session()


class SessionAnalyzer:
    """Analyze logged telemetry sessions."""

    def __init__(self, log_directory: str = "logs"):
        self.log_directory = Path(log_directory)

    def list_sessions(self) -> List[str]:
        """List available sessions."""
        if not self.log_directory.exists():
            return []

        return [f.stem for f in self.log_directory.glob("*.csv")]

    def load_session(self, session_id: str) -> List[Dict[str, Any]]:
        """Load session data from CSV."""
        csv_path = self.log_directory / f"{session_id}.csv"
        if not csv_path.exists():
            return []

        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            return list(reader)

    def get_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary statistics for a session."""
        data = self.load_session(session_id)
        if not data:
            return {}

        # Calculate statistics
        elapsed = float(data[-1]['elapsed']) if data else 0

        # Count states
        state_counts = {}
        zone_counts = {}
        for row in data:
            state = row.get('taxi_state', '')
            zone = row.get('nav_zone', '')
            state_counts[state] = state_counts.get(state, 0) + 1
            zone_counts[zone] = zone_counts.get(zone, 0) + 1

        return {
            'session_id': session_id,
            'total_frames': len(data),
            'duration_seconds': elapsed,
            'state_distribution': state_counts,
            'zone_distribution': zone_counts,
        }


def create_logger_from_config(config: Dict[str, Any] = None) -> TelemetryLogger:
    """Create TelemetryLogger from config dict."""
    if config is None:
        return TelemetryLogger()

    telemetry_config = config.get('telemetry', {})

    return TelemetryLogger(
        log_directory=telemetry_config.get('log_directory', 'logs'),
        save_video=telemetry_config.get('save_video', True),
        video_fps=telemetry_config.get('video_fps', 15),
        enabled=telemetry_config.get('enabled', True),
    )
