"""
Unit tests for AeroQ-Route data generation, models, and solvers.
"""

import pytest
import networkx as nx

from data_gen import generate_airspace_graph, generate_flights, haversine_distance
from models import build_route_conflict_qubo, build_qubo, generate_candidate_paths, calculate_path_fuel
from solvers import DijkstraSolver, ExactILPSolver, AnnealerSolver, QAOASolver


@pytest.fixture
def airspace_data():
    G = generate_airspace_graph(n_nodes=10, seed=42, default_capacity=2)
    flights = generate_flights(G, num_flights=4, seed=42)
    return G, flights


def test_haversine_distance():
    # Delhi to Mumbai ~ 1150 km
    dist = haversine_distance(77.1025, 28.7041, 72.8777, 19.0760)
    assert 1100 < dist < 1250


def test_airspace_graph_generation(airspace_data):
    G, _ = airspace_data
    assert len(G.nodes) == 10
    assert nx.is_connected(G)
    for u, v, d in G.edges(data=True):
        assert "distance" in d
        assert "fuel_burn" in d
        assert "capacity" in d


def test_flight_generation(airspace_data):
    G, flights = airspace_data
    assert len(flights) == 4
    for f in flights:
        assert f["origin"] in G
        assert f["destination"] in G
        assert f["fuel_rate"] > 0


def test_candidate_paths(airspace_data):
    G, flights = airspace_data
    paths = generate_candidate_paths(G, flights, k_paths=2)
    for f in flights:
        f_id = f["id"]
        assert f_id in paths
        assert len(paths[f_id]) == 2
        for p in paths[f_id]:
            assert p[0] == f["origin"]
            assert p[-1] == f["destination"]


def test_route_conflict_qubo(airspace_data):
    G, flights = airspace_data
    candidate_paths = generate_candidate_paths(G, flights, k_paths=2)
    Q, var_list, conflicts = build_route_conflict_qubo(G, flights, candidate_paths)
    assert Q.shape[0] == len(var_list)
    assert Q.shape[0] == len(flights) * 2


def test_dijkstra_solver(airspace_data):
    G, flights = airspace_data
    solver = DijkstraSolver()
    res = solver.solve(G, flights)
    assert "total_fuel" in res
    assert res["total_fuel"] > 0
    assert len(res["assignments"]) == len(flights)


def test_exact_ilp_solver(airspace_data):
    G, flights = airspace_data
    solver = ExactILPSolver()
    res = solver.solve(G, flights, k_candidates=2)
    assert "total_fuel" in res
    assert res["total_fuel"] > 0
    assert len(res["assignments"]) == len(flights)


def test_annealer_solver(airspace_data):
    G, flights = airspace_data
    solver = AnnealerSolver()
    res = solver.solve(G, flights, num_reads=50, num_sweeps=100)
    assert "total_fuel" in res
    assert res["total_fuel"] > 0
    assert len(res["assignments"]) == len(flights)


def test_qaoa_solver(airspace_data):
    G, flights = airspace_data
    solver = QAOASolver()
    res = solver.solve(G, flights, p_layers=1, max_qubits=8)
    assert "total_fuel" in res
    assert res["total_fuel"] > 0
    assert len(res["assignments"]) == len(flights)
