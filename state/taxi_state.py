"""Taxi operation states and LED color mappings."""

from enum import Enum, auto


class TaxiState(Enum):
    """Taxi operation states with corresponding LED colors."""
    WAITING_AT_HUB = auto()      # Magenta - waiting for ride
    EN_ROUTE_TO_PICKUP = auto()  # Green - driving to pickup
    AT_PICKUP = auto()           # Blue - stopped at pickup
    EN_ROUTE_TO_DROPOFF = auto() # Green - driving with passenger
    AT_DROPOFF = auto()          # Orange - stopped at dropoff
    RETURNING_TO_HUB = auto()    # Green - returning
    STOPPED = auto()             # Red - stopped at sign/light


# LED colors (RGB normalized 0-1)
LED_COLORS = {
    TaxiState.WAITING_AT_HUB: [1.0, 0.0, 1.0],      # Magenta
    TaxiState.EN_ROUTE_TO_PICKUP: [0.0, 1.0, 0.0],  # Green
    TaxiState.AT_PICKUP: [0.0, 0.0, 1.0],           # Blue
    TaxiState.EN_ROUTE_TO_DROPOFF: [0.0, 1.0, 0.0], # Green
    TaxiState.AT_DROPOFF: [1.0, 0.5, 0.0],          # Orange
    TaxiState.RETURNING_TO_HUB: [0.0, 1.0, 0.0],    # Green
    TaxiState.STOPPED: [1.0, 0.0, 0.0],             # Red
}
