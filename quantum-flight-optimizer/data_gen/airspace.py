"""
Airspace Graph Generator for AeroQ-Route.
=========================================
For First-Year B.Tech Students:
- Graph Theory Concept: An airspace network is modeled as an undirected/directed graph G = (V, E).
  - V (Vertices/Nodes): Airports and navigational waypoints (fixes) in 2D/3D space (lat, lon, altitude).
  - E (Edges/Corridors): Air routes connecting waypoints.
- Weight (Cost): Edge cost represents estimated fuel burn (kg), which depends on:
  1. Distance (km) via Great Circle / Haversine formula
  2. Wind Factor: Tailwind (< 1.0) reduces fuel, Headwind (> 1.0) increases fuel
  3. Edge Capacity: Maximum simultaneous aircraft allowed safely in the airway corridor
"""

import math
import random
import networkx as nx
import numpy as np


def haversine_distance(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth in kilometers.
    Earth radius ~ 6371.0 km.
    """
    r_earth = 6371.0  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (math.sin(dphi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(dlambda / 2.0) ** 2))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r_earth * c


def generate_airspace_graph(n_nodes: int = 20, seed: int = 42, default_capacity: int = 2) -> nx.Graph:
    """
    Builds a realistic connected airspace graph loosely modeled on the Indian subcontinent.

    Parameters:
    -----------
    n_nodes : int
        Total number of nodes (>= 5). Includes major Indian hubs and intermediate waypoints.
    seed : int
        Random seed for reproducibility.
    default_capacity : int
        Maximum concurrent flights per airway corridor before triggering a bottleneck.

    Returns:
    --------
    nx.Graph with node attributes (pos, type, region) and edge attributes (distance, wind_factor, fuel_burn, capacity).
    """
    random.seed(seed)
    np.random.seed(seed)

    G = nx.Graph()

    # 1. Real Indian commercial airports (coordinates: [lon, lat])
    base_airports = {
        'DEL': (77.1025, 28.7041, 'North'),    # Indira Gandhi International (Delhi)
        'BOM': (72.8777, 19.0760, 'West'),     # Chhatrapati Shivaji Maharaj (Mumbai)
        'HYD': (78.4867, 17.3850, 'Central'),  # Rajiv Gandhi International (Hyderabad)
        'BLR': (77.5946, 12.9716, 'South'),    # Kempegowda International (Bengaluru)
        'MAA': (80.2707, 13.0827, 'South'),    # Chennai International (Chennai)
        'CCU': (88.3639, 22.5726, 'East'),     # Netaji Subhash Chandra Bose (Kolkata)
        'VTZ': (83.2242, 17.6868, 'East'),     # Visakhapatnam Airport (Vizag)
    }

    # 2. Known intermediate Indian navigational fixes / secondary hubs
    intermediate_fixes = {
        'NAG': (79.0882, 21.1458, 'Central'),  # Nagpur (Central India crossroads)
        'BHO': (77.4126, 23.2599, 'Central'),  # Bhopal
        'JAI': (75.7873, 26.9124, 'North'),    # Jaipur
        'LKO': (80.9462, 26.8467, 'North'),    # Lucknow
        'GOI': (73.8315, 15.3800, 'West'),     # Goa
        'COK': (76.2673, 9.9312, 'South'),     # Kochi
        'IXC': (76.7794, 30.7333, 'North'),    # Chandigarh
        'GAU': (91.7362, 26.1445, 'East'),     # Guwahati
    }

    # Add base airports up to n_nodes
    for code, (lon, lat, reg) in base_airports.items():
        if len(G.nodes()) < n_nodes:
            G.add_node(code, pos=(lon, lat), type='airport', region=reg, name=code)

    # Add intermediate fixes
    for code, (lon, lat, reg) in intermediate_fixes.items():
        if len(G.nodes()) < n_nodes:
            G.add_node(code, pos=(lon, lat), type='waypoint', region=reg, name=code)

    # Fill remaining required nodes with synthetic high-altitude navigational fixes
    wpt_counter = 1
    while len(G.nodes()) < n_nodes:
        lon = float(np.random.uniform(72.5, 88.5))
        lat = float(np.random.uniform(12.5, 29.5))
        reg = 'North' if lat > 23.0 else ('South' if lat < 17.0 else 'Central')
        wpt_name = f"WP{wpt_counter}"
        G.add_node(wpt_name, pos=(lon, lat), type='waypoint', region=reg, name=wpt_name)
        wpt_counter += 1

    nodes = list(G.nodes())

    # 3. Connect nodes based on proximity (k-nearest neighbors) to form airways
    k_neighbors = 3 if n_nodes <= 10 else 4
    for u in nodes:
        lon1, lat1 = G.nodes[u]['pos']
        distances = []
        for v in nodes:
            if u == v:
                continue
            lon2, lat2 = G.nodes[v]['pos']
            dist = haversine_distance(lon1, lat1, lon2, lat2)
            distances.append((dist, v))
        distances.sort(key=lambda item: item[0])

        for dist, v in distances[:k_neighbors]:
            if not G.has_edge(u, v):
                # Wind factor: 0.90 (tailwind) to 1.30 (headwind)
                wind = float(np.random.uniform(0.92, 1.25))
                # Fuel rate per km: 4.8 kg/km average for narrowbody
                base_fuel_rate = float(np.random.uniform(4.5, 5.5))
                fuel_burn = dist * base_fuel_rate * wind

                # Set capacity: central bottleneck airways have lower capacity
                cap = default_capacity
                if G.nodes[u].get('region') == 'Central' and G.nodes[v].get('region') == 'Central':
                    cap = max(1, default_capacity - 1)

                G.add_edge(
                    u, v,
                    distance=round(dist, 1),
                    wind_factor=round(wind, 3),
                    fuel_rate=round(base_fuel_rate, 2),
                    fuel_burn=round(fuel_burn, 1),
                    capacity=cap
                )

    # 4. Guarantee connectivity: Airspace must be a single connected component
    if not nx.is_connected(G):
        components = list(nx.connected_components(G))
        for idx in range(len(components) - 1):
            comp_a = list(components[idx])
            comp_b = list(components[idx + 1])
            # Find closest pair between components
            best_pair = None
            min_dist = float('inf')
            for u in comp_a:
                lon1, lat1 = G.nodes[u]['pos']
                for v in comp_b:
                    lon2, lat2 = G.nodes[v]['pos']
                    d = haversine_distance(lon1, lat1, lon2, lat2)
                    if d < min_dist:
                        min_dist = d
                        best_pair = (u, v)
            if best_pair:
                u, v = best_pair
                wind = 1.05
                fuel_burn = min_dist * 5.0 * wind
                G.add_edge(u, v, distance=round(min_dist, 1), wind_factor=wind,
                           fuel_rate=5.0, fuel_burn=round(fuel_burn, 1), capacity=default_capacity)

    return G
