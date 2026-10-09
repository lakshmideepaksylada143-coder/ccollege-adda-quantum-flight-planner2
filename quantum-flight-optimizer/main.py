"""
AeroQ-Route: Quantum-Assisted Air Traffic Deconfliction & Fuel Optimization
==========================================================================
Main execution script for benchmarking Classical, Simulated Annealing,
and Gate-Based Quantum (QAOA) trajectory optimization across Indian airspace corridors.
"""

import os
import sys
import yaml

# Ensure project root is in PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_gen import generate_airspace_graph, generate_flights
from solvers import DijkstraSolver, ExactILPSolver, AnnealerSolver, QAOASolver


def load_config(config_path: str = "config.yaml") -> dict:
    """Loads YAML configuration file."""
    if not os.path.isabs(config_path):
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), config_path)
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_benchmark():
    """Runs end-to-end benchmark across all solvers and prints comparison report."""
    print("=" * 80)
    print("   AeroQ-Route: Quantum Flight Optimization & Airspace Deconfliction   ")
    print("=" * 80)

    # 1. Load configuration
    cfg = load_config()
    print(f"\n[+] Loaded config (Seed: {cfg.get('seed', 42)}, Nodes: {cfg.get('num_nodes', 20)}, Flights: {cfg.get('num_flights', 10)})")

    # 2. Generate airspace network
    print("[+] Building Indian Airspace Corridor Network...")
    G = generate_airspace_graph(
        n_nodes=cfg.get("num_nodes", 20),
        seed=cfg.get("seed", 42),
        default_capacity=cfg.get("capacity_per_edge", 2),
    )
    print(f"    -> Airspace Graph generated: {len(G.nodes)} nodes, {len(G.edges)} airway corridors")

    # 3. Generate scheduled flight demands
    print("[+] Scheduling Commercial Flight Trajectories...")
    flights = generate_flights(
        G=G,
        num_flights=cfg.get("num_flights", 10),
        seed=cfg.get("seed", 42),
        aircraft_specs=cfg.get("aircraft_specs"),
    )
    print(f"    -> {len(flights)} commercial flights scheduled across origin/destinations")

    # 4. Solvers setup
    solvers = [
        ("Dijkstra (Greedy Baseline)", DijkstraSolver(), {}),
        ("Exact ILP (PuLP / HiGHS)", ExactILPSolver(), {"k_candidates": cfg.get("solvers", {}).get("classical_k_candidates", 3)}),
        ("Simulated Annealer (Neal)", AnnealerSolver(), {
            "P_path": cfg.get("penalty_path", 25000.0),
            "P_cap": cfg.get("penalty_cap", 2000.0),
            "num_reads": cfg.get("solvers", {}).get("annealer", {}).get("num_reads", 150),
            "num_sweeps": cfg.get("solvers", {}).get("annealer", {}).get("num_sweeps", 500),
        }),
        ("QAOA (Qiskit Gate-Based)", QAOASolver(), {
            "p_layers": cfg.get("solvers", {}).get("qaoa", {}).get("p_layers", 2),
            "max_qubits": cfg.get("solvers", {}).get("qaoa", {}).get("max_qubits", 12),
            "shots": cfg.get("solvers", {}).get("qaoa", {}).get("shots", 1024),
        }),
    ]

    results = []
    baseline_fuel = None
    baseline_violations = None

    print("\n[+] Executing Trajectory Solvers:")
    for label, solver, kwargs in solvers:
        print(f"    Running {label}...", end=" ", flush=True)
        try:
            res = solver.solve(G, flights, **kwargs)
            results.append(res)
            if baseline_fuel is None:
                baseline_fuel = res["total_fuel"]
                baseline_violations = res["violations"]
            print(f"DONE ({res['runtime_sec']:.4f}s) | Fuel: {res['total_fuel']:,.1f} kg | Violations: {res['violations']}")
        except Exception as e:
            print(f"FAILED: {e}")

    # 5. Print Comparison Table
    print("\n" + "=" * 92)
    print(f"{'Solver':<28} | {'Total Fuel (kg)':<15} | {'CO2 (kg)':<12} | {'Violations':<11} | {'Runtime (s)':<12}")
    print("-" * 92)

    for res in results:
        name = res["solver_name"]
        fuel = f"{res['total_fuel']:,.1f}"
        co2 = f"{res['total_co2']:,.1f}"
        viol = str(res["violations"])
        runtime = f"{res['runtime_sec']:.4f}"
        print(f"{name:<28} | {fuel:<15} | {co2:<12} | {viol:<11} | {runtime:<12}")

    print("=" * 92)

    # Summary analysis
    if len(results) >= 2 and baseline_fuel:
        best_deconfliction = min(results, key=lambda r: (r["violations"], r["total_fuel"]))
        print(f"\n[Summary] Best Deconflicted Solver: '{best_deconfliction['solver_name']}'")
        print(f"          Capacity Violations: {baseline_violations} -> {best_deconfliction['violations']}")
        print(f"          Total Emissions:     {best_deconfliction['total_co2']:,.1f} kg CO2")
    print("\nBenchmark completed successfully!\n")


if __name__ == "__main__":
    run_benchmark()
