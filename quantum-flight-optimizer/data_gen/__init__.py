"""
Data Generation Module for AeroQ-Route.
Provides graph models of national airspace corridors and commercial flight schedules.
"""
from .airspace import generate_airspace_graph, haversine_distance
from .flights import generate_flights

__all__ = ["generate_airspace_graph", "haversine_distance", "generate_flights"]
