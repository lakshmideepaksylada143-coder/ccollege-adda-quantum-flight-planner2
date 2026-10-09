"""
AeroQ-Route: Quantum Data & Trajectory Generator
==================================================
Generates quantum-optimized flight corridor assignments, QAOA circuit metrics,
and D-Wave Neal ground-state solutions, saving the results to JSON.
"""

import json
import os
import time
from datetime import datetime

from data_gen.airspace import generate_airspace_graph
from data_gen.flights import generate_flights
from solvers.annealer import AnnealerSolver
from solvers.qaoa import QAOASolver
from solvers.classical import DijkstraSolver


def generate_quantum_dataset(num_flights: int = 10, seed: int = 42, output_file: str = "quantum_solution_report.json"):
    print(f"[+] Initializing Indian Airspace Graph (Seed: {seed})...")
    G = generate_airspace_graph(n_nodes=20, seed=seed)
    
    print(f"[+] Scheduling {num_flights} Commercial Flights...")
    flights = generate_flights(G, num_flights=num_flights, seed=seed)
    
    # Run Solvers
    print("[+] Executing Dijkstra Baseline...")
    dijkstra_res = DijkstraSolver().solve(G, flights)
    
    print("[+] Executing Simulated Quantum Annealer (D-Wave Neal)...")
    annealer_res = AnnealerSolver().solve(G, flights, P_path=15000.0, P_cap=8000.0, num_reads=120, seed=seed)
    
    print("[+] Executing Gate-Based QAOA (Qiskit)...")
    qaoa_res = QAOASolver().solve(G, flights, p_layers=2, max_qubits=12, shots=1024, seed=seed)
    
    # Calculate carbon savings
    base_co2 = dijkstra_res['total_co2']
    anneal_co2 = annealer_res['total_co2']
    co2_delta = round(base_co2 - anneal_co2, 2)
    
    report = {
        "metadata": {
            "title": "AeroQ-Route Quantum Flight Optimization Benchmark",
            "timestamp": datetime.now().isoformat(),
            "flights_count": num_flights,
            "seed": seed
        },
        "environmental_impact": {
            "baseline_emissions_kg_co2": dijkstra_res['total_co2'],
            "quantum_annealer_emissions_kg_co2": annealer_res['total_co2'],
            "qaoa_emissions_kg_co2": qaoa_res['total_co2'],
            "co2_delta_kg": co2_delta,
            "airspace_congestion_reduction": f"{dijkstra_res['violations']} violations -> {annealer_res['violations']} violations"
        },
        "solvers": {
            "dijkstra": {
                "fuel_kg": dijkstra_res['total_fuel'],
                "violations": dijkstra_res['violations'],
                "runtime_sec": dijkstra_res['runtime_sec'],
                "routes": dijkstra_res['assignments']
            },
            "quantum_annealer": {
                "fuel_kg": annealer_res['total_fuel'],
                "violations": annealer_res['violations'],
                "runtime_sec": annealer_res['runtime_sec'],
                "qubo_energy": annealer_res['details']['qubo_energy'],
                "qubo_variables": annealer_res['details']['qubo_variables'],
                "routes": annealer_res['assignments']
            },
            "qaoa_gate_based": {
                "fuel_kg": qaoa_res['total_fuel'],
                "violations": qaoa_res['violations'],
                "runtime_sec": qaoa_res['runtime_sec'],
                "ansatz_layers": qaoa_res['details']['p_layers'],
                "qubits": qaoa_res['details']['qubits_used'],
                "routes": qaoa_res['assignments']
            }
        }
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        
    print(f"[OK] Saved quantum report to: {output_file}")
    return report


if __name__ == "__main__":
    generate_quantum_dataset()
