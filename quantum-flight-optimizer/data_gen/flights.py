"""
Flight Schedule Generator for AeroQ-Route.
==========================================
For First-Year B.Tech Students:
- In Air Traffic Management (ATM), each commercial flight requires:
  1. Unique Flight ID (e.g. F0, F1)
  2. Origin Airport (e.g. DEL - Delhi)
  3. Destination Airport (e.g. BLR - Bengaluru)
  4. Departure Time Slot (discrete time window to model simultaneous airspace occupancy)
  5. Aircraft Model (determines fuel consumption rate per kilometer)
"""

import random
from typing import Dict, List
import networkx as nx


AIRCRAFT_DATABASE = {
    'A320neo': {'fuel_rate': 4.5, 'cruise_speed': 840, 'wake_cat': 'Medium'},
    'B737-800': {'fuel_rate': 5.0, 'cruise_speed': 830, 'wake_cat': 'Medium'},
    'A321neo': {'fuel_rate': 5.8, 'cruise_speed': 845, 'wake_cat': 'Medium'},
    'ATR72': {'fuel_rate': 2.8, 'cruise_speed': 510, 'wake_cat': 'Light'},
    'B787-9': {'fuel_rate': 6.5, 'cruise_speed': 900, 'wake_cat': 'Heavy'},
}


def generate_flights(
    G: nx.Graph,
    num_flights: int = 10,
    seed: int = 42,
    num_time_slots: int = 3,
    aircraft_specs: Dict = None
) -> List[Dict]:
    """
    Generates a realistic list of scheduled commercial flights between airports in the graph.

    Parameters:
    -----------
    G : nx.Graph
        Airspace graph containing node attributes.
    num_flights : int
        Number of flights to schedule (e.g., 5 to 20).
    seed : int
        Seed for reproducibility.
    num_time_slots : int
        Discrete departure time windows.
    aircraft_specs : Dict, optional
        Custom aircraft specifications dictionary (e.g. from config.yaml).

    Returns:
    --------
    List[Dict]: List of flight objects.
    """
    random.seed(seed)

    # Prefer airport nodes as origins and destinations; fallback to waypoints if needed
    airports = [n for n, d in G.nodes(data=True) if d.get('type') == 'airport']
    if len(airports) < 2:
        airports = list(G.nodes())
    if len(airports) < 2:
        return []

    # Use custom aircraft database if provided, else use built-in defaults
    ac_db = {}
    if aircraft_specs:
        for ac_key, ac_val in aircraft_specs.items():
            ac_db[ac_key] = {
                'fuel_rate': ac_val.get('fuel_rate', 4.8),
                'cruise_speed': ac_val.get('cruise_speed_kmh', ac_val.get('cruise_speed', 800)),
                'wake_cat': ac_val.get('wake_cat', 'Medium')
            }
    if not ac_db:
        ac_db = AIRCRAFT_DATABASE

    aircraft_keys = list(ac_db.keys())
    flights = []

    # High-demand Indian city pairs for realism
    popular_pairs = [
        ('DEL', 'BOM'), ('BOM', 'DEL'),
        ('DEL', 'BLR'), ('BLR', 'DEL'),
        ('BOM', 'HYD'), ('HYD', 'BOM'),
        ('DEL', 'MAA'), ('CCU', 'DEL'),
        ('BLR', 'HYD'), ('BOM', 'CCU'),
        ('HYD', 'VTZ'), ('DEL', 'VTZ'),
        ('MAA', 'BLR'), ('CCU', 'HYD'),
    ]

    for i in range(num_flights):
        # Choose from popular pairs if available in G, else sample randomly
        valid_popular = [pair for pair in popular_pairs if pair[0] in G and pair[1] in G]
        if valid_popular and i < len(valid_popular):
            orig, dest = valid_popular[i]
        else:
            orig, dest = random.sample(airports, 2)

        # Select aircraft type
        ac_type = aircraft_keys[i % len(aircraft_keys)]
        spec = ac_db[ac_type]

        flights.append({
            'id': f'F{i}',
            'origin': orig,
            'destination': dest,
            'aircraft': ac_type,
            'fuel_rate': spec['fuel_rate'],
            'cruise_speed': spec['cruise_speed'],
            'slot': i % num_time_slots,
            'wake_cat': spec['wake_cat']
        })

    return flights
