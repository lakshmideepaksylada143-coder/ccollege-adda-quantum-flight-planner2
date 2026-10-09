"""
QUBO (Quadratic Unconstrained Binary Optimization) Formulation Module
======================================================================
For First-Year B.Tech Students:
- What is a QUBO?
  A QUBO minimizes a quadratic polynomial of binary variables x_i in {0, 1}:
      H(x) = sum_i Q_{i,i} * x_i + sum_{i < j} Q_{i,j} * x_i * x_j
  - Diagonal terms Q_{i,i}: Linear objective cost (e.g. fuel burn of selecting route i).
  - Off-diagonal terms Q_{i,j}: Quadratic interaction penalties (e.g. penalty if two flights
    attempt to occupy the same airway bottleneck at the same time).
- How do Quantum Annealers and QAOA solve this?
  By mapping x_i in {0, 1} to Pauli-Z spin operators sigma_i^z in {-1, +1} via the transformation:
      x_i = (1 - sigma_i^z) / 2
  This maps the QUBO to an Ising Spin Hamiltonian H_Ising, which physical qubits naturally
  evolve towards to find the lowest energy (ground state).
"""

from typing import Dict, List, Tuple
import networkx as nx
import numpy as np


def calculate_path_fuel(G: nx.Graph, path: List[str], fuel_rate: float) -> float:
    """
    Computes exact fuel burn (kg) for a discrete path traversing airway edges:
    Fuel = sum_{(u,v) in path} [ distance(u,v) * fuel_rate * wind_factor(u,v) ]
    """
    if not path or len(path) < 2:
        return float('inf')

    total_fuel = 0.0
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        if G.has_edge(u, v):
            dist = G[u][v]['distance']
            wind = G[u][v]['wind_factor']
            total_fuel += dist * fuel_rate * wind
        else:
            return float('inf')
    return total_fuel


def generate_candidate_paths(
    G: nx.Graph,
    flights: List[Dict],
    k_paths: int = 2
) -> Dict[str, List[List[str]]]:
    """
    Generates K candidate paths for each flight using Yen's K-shortest simple paths
    weighted by edge fuel burn.

    Parameters:
    -----------
    G : nx.Graph
        Airspace graph.
    flights : List[Dict]
        List of flight specifications.
    k_paths : int
        Number of alternative flight trajectories per flight (typically 2 or 3).

    Returns:
    --------
    Dict[str, List[List[str]]]: Mapping from flight ID to a list of candidate path node lists.
    """
    candidate_paths = {}

    for f in flights:
        orig = f['origin']
        dest = f['destination']
        f_id = f['id']

        try:
            # Generate k paths sorted by total fuel burn
            generator = nx.shortest_simple_paths(G, orig, dest, weight='fuel_burn')
            paths = []
            for _ in range(k_paths):
                try:
                    p = next(generator)
                    paths.append(p)
                except StopIteration:
                    break

            if not paths:
                # Fallback to standard shortest path
                paths = [nx.shortest_path(G, orig, dest)]

            # If fewer than k_paths were found, duplicate with detour or padding
            while len(paths) < k_paths:
                paths.append(list(paths[0]))

            candidate_paths[f_id] = paths
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            # Fallback path if disconnected
            candidate_paths[f_id] = [[orig, dest]] * k_paths

    return candidate_paths


def build_route_conflict_qubo(
    G: nx.Graph,
    flights: List[Dict],
    candidate_paths: Dict[str, List[List[str]]],
    P_one: float = 5000.0,
    P_conflict: float = 2000.0,
    capacity_limit: int = 2
) -> Tuple[np.ndarray, List[Tuple[str, int]], List[Dict]]:
    """
    Builds the compact Route-Selection Conflict QUBO matrix.
    Ideal for Gate-Based QAOA (<= 16 qubits) and Quantum Annealing.

    Variables:
    ----------
    y_{f, k} in {0, 1} : Binary decision variable indicating flight f chooses candidate path k.
    Total binary variables N = F * K.

    Formulation:
    ------------
    H(y) = sum_{f, k} Fuel(p_{f, k}) * y_{f, k}
         + P_one * sum_f (sum_k y_{f, k} - 1)^2
         + P_conflict * sum_{conflicting pairs} y_{f1, k1} * y_{f2, k2}

    Expansion of (sum_k y_{f, k} - 1)^2:
      sum_k y_{f, k}^2 + 2 sum_{k < l} y_{f, k} y_{f, l} - 2 sum_k y_{f, k} + 1
      = - sum_k y_{f, k} + 2 sum_{k < l} y_{f, k} y_{f, l} + 1  (since y^2 = y)
    So diagonal gets -P_one, and off-diagonal between candidate paths of same flight gets +2*P_one.
    """
    F = len(flights)
    if F == 0:
        return np.zeros((0, 0)), [], []

    # Flatten variable indexing: (flight_id, candidate_index) -> global variable index
    var_list = []
    var_map = {}
    for f_idx, flight in enumerate(flights):
        f_id = flight['id']
        paths = candidate_paths.get(f_id, [[]])
        for k in range(len(paths)):
            idx = len(var_list)
            var_list.append((f_id, k))
            var_map[(f_id, k)] = idx

    N = len(var_list)
    Q = np.zeros((N, N), dtype=float)

    # Ensure P_one penalty strictly dominates path fuel burn (prevents all-zero unconstrained ground state)
    max_path_fuel = 0.0
    for flight in flights:
        f_id = flight['id']
        rate = flight['fuel_rate']
        for p in candidate_paths.get(f_id, []):
            cost = calculate_path_fuel(G, p, rate)
            if cost != float('inf') and cost > max_path_fuel:
                max_path_fuel = cost

    effective_P_one = max(P_one, max_path_fuel * 1.5) if max_path_fuel > 0 else P_one

    # 1. Objective: Direct Fuel Burn Cost on Diagonals
    for (f_id, k), i in var_map.items():
        flight = next(fl for fl in flights if fl['id'] == f_id)
        path = candidate_paths[f_id][k]
        fuel = calculate_path_fuel(G, path, flight['fuel_rate'])
        Q[i, i] += fuel

    # 2. Hard Constraint: Exactly ONE path chosen per flight
    # (sum_k y_k - 1)^2 => diagonal: -effective_P_one, off-diagonal (k != l): +2 * effective_P_one
    for flight in flights:
        f_id = flight['id']
        k_indices = [var_map[(f_id, k)] for k in range(len(candidate_paths[f_id]))]

        for i in k_indices:
            Q[i, i] -= effective_P_one  # linear penalty term

        for a in range(len(k_indices)):
            for b in range(a + 1, len(k_indices)):
                i, j = k_indices[a], k_indices[b]
                Q[i, j] += 2.0 * effective_P_one

    # 3. Soft Constraint: Spatiotemporal Bottleneck / Airway Conflict Penalty
    # Detect shared edges between flights departing in overlapping time slots
    conflicts = []
    for i_f1, f1 in enumerate(flights):
        for i_f2 in range(i_f1 + 1, len(flights)):
            f2 = flights[i_f2]

            # Only conflict if departure time slot difference <= 1 (airspace concurrency)
            if abs(f1['slot'] - f2['slot']) > 1:
                continue

            paths_f1 = candidate_paths[f1['id']]
            paths_f2 = candidate_paths[f2['id']]

            for k1, p1 in enumerate(paths_f1):
                edges_p1 = set(tuple(sorted((p1[idx], p1[idx + 1]))) for idx in range(len(p1) - 1))
                for k2, p2 in enumerate(paths_f2):
                    edges_p2 = set(tuple(sorted((p2[jdx], p2[jdx + 1]))) for jdx in range(len(p2) - 1))

                    shared_edges = edges_p1.intersection(edges_p2)
                    if shared_edges:
                        # Shared edge detected! If capacity is tight, add penalty
                        idx_1 = var_map[(f1['id'], k1)]
                        idx_2 = var_map[(f2['id'], k2)]

                        penalty = P_conflict * len(shared_edges)
                        # Add symmetric or upper-triangular penalty
                        if idx_1 < idx_2:
                            Q[idx_1, idx_2] += penalty
                        else:
                            Q[idx_2, idx_1] += penalty

                        conflicts.append({
                            'flight_1': f1['id'], 'path_1': k1,
                            'flight_2': f2['id'], 'path_2': k2,
                            'shared_edges': list(shared_edges)
                        })

    return Q, var_list, conflicts


def build_qubo(
    G: nx.Graph,
    flights: List[Dict],
    P_path: float = 5000.0,
    P_cap: float = 1000.0
) -> Tuple[np.ndarray, List[Tuple]]:
    """
    Builds the edge-based QUBO matrix for simulated annealing.
    Binary variable x_{f, e} in {0, 1} indicates flight f uses edge e.

    Parameters:
    -----------
    G : nx.Graph
        Airspace graph.
    flights : List[Dict]
        Flights to route.
    P_path : float
        Penalty weight for flow continuity.
    P_cap : float
        Penalty weight for edge capacity congestion.

    Returns:
    --------
    Tuple[np.ndarray, List[Tuple]]: QUBO matrix Q and ordered list of edges.
    """
    edges = list(G.edges())
    F = len(flights)
    E = len(edges)
    N = F * E
    Q = np.zeros((N, N), dtype=float)

    # 1. Objective: Fuel burn on diagonal
    for f_idx, flight in enumerate(flights):
        rate = flight['fuel_rate']
        for e_idx, (u, v) in enumerate(edges):
            dist = G[u][v]['distance']
            wind = G[u][v]['wind_factor']
            fuel = dist * rate * wind
            idx = f_idx * E + e_idx
            Q[idx, idx] += fuel

    # 2. Capacity penalty between flights sharing the same edge
    for e_idx in range(E):
        u, v = edges[e_idx]
        cap = G[u][v]['capacity']
        for f1 in range(F):
            for f2 in range(f1 + 1, F):
                i = f1 * E + e_idx
                j = f2 * E + e_idx
                # Sharing penalty increases as concurrent flights exceed capacity
                Q[i, j] += P_cap / max(1, cap)

    # 3. Flow Continuity Constraints (Departure and Arrival):
    # Origin and destination must each have exactly one incident airway corridor active: (sum x_e - 1)^2
    for f_idx, flight in enumerate(flights):
        orig = flight['origin']
        dest = flight['destination']

        for endpoint in (orig, dest):
            inc_indices = [
                f_idx * E + e_idx
                for e_idx, (u, v) in enumerate(edges)
                if u == endpoint or v == endpoint
            ]
            for i in inc_indices:
                Q[i, i] -= P_path

            for a in range(len(inc_indices)):
                for b in range(a + 1, len(inc_indices)):
                    i, j = inc_indices[a], inc_indices[b]
                    if i < j:
                        Q[i, j] += 2.0 * P_path
                    else:
                        Q[j, i] += 2.0 * P_path

    return Q, edges
