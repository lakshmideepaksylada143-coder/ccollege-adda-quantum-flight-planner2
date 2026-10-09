"""
Base Solver Interface for AeroQ-Route.
======================================
Defines the standard contract for all classical, quantum, and hybrid solvers.
All solvers return a uniform dictionary schema for benchmarking and visualization.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple
import networkx as nx


class BaseSolver(ABC):
    """
    Abstract Base Class for Airspace Trajectory Solvers.
    """

    def __init__(self, name: str = "BaseSolver"):
        self.name = name

    @abstractmethod
    def solve(self, G: nx.Graph, flights: List[Dict], **kwargs) -> Dict:
        """
        Solves the multi-flight trajectory optimization problem.

        Parameters:
        -----------
        G : nx.Graph
            Airspace graph.
        flights : List[Dict]
            List of flight dictionaries with origins, destinations, fuel rates, etc.

        Returns:
        --------
        Dict: Standardized solution dictionary:
            - 'solver_name': str
            - 'assignments': Dict[str, List[str]] (Flight ID -> List of waypoints)
            - 'total_fuel': float (kg)
            - 'total_co2': float (kg = fuel * 3.16)
            - 'violations': int (count of capacity over-utilization)
            - 'runtime_sec': float
            - 'edge_usage': Dict[Tuple[str, str], int]
            - 'details': Dict (solver-specific metadata)
        """
        pass

    @staticmethod
    def evaluate_solution(
        G: nx.Graph,
        flights: List[Dict],
        assignments: Dict[str, List[str]],
        co2_multiplier: float = 3.16
    ) -> Tuple[float, float, int, Dict[Tuple[str, str], int]]:
        """
        Evaluates fuel, CO2, capacity violations, and edge usage for a set of flight path assignments.
        """
        total_fuel = 0.0
        edge_usage: Dict[Tuple[str, str], int] = {}

        flight_map = {f['id']: f for f in flights}

        for f_id, path in assignments.items():
            flight = flight_map.get(f_id)
            if not flight or not path or len(path) < 2:
                continue

            rate = flight['fuel_rate']
            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                edge_key = tuple(sorted((u, v)))
                edge_usage[edge_key] = edge_usage.get(edge_key, 0) + 1

                if G.has_edge(u, v):
                    dist = G[u][v]['distance']
                    wind = G[u][v]['wind_factor']
                    total_fuel += dist * rate * wind
                else:
                    # Broken trajectory penalty
                    total_fuel += 10000.0

        # Calculate capacity violations
        violations = 0
        for (u, v), usage in edge_usage.items():
            if G.has_edge(u, v):
                cap = G[u][v].get('capacity', 2)
                if usage > cap:
                    violations += (usage - cap)

        total_co2 = total_fuel * co2_multiplier  # Environmental emissions factor
        return round(total_fuel, 2), round(total_co2, 2), violations, edge_usage

