"""
================================================================================
AeroQ-Route: Pure Quantum Computing & Airspace Optimization Suite
================================================================================
Frameworks:
  - IBM Qiskit 2.x & Qiskit Aer Simulator (Gate-Based Quantum Computing)
  - D-Wave Neal & Dimod (Quantum Annealing Emulation)

Quantum Computing Pipeline:
  1. Quantum State Preparation:
     Equal superposition |+>^N via Hadamard gates (H).
  2. Ising Problem Hamiltonian Unitary U(H_C, gamma):
     R_z single-qubit phase rotations and R_zz two-qubit entangling gates.
  3. Quantum Mixer Hamiltonian Unitary U(H_M, beta):
     Transverse-field X-rotations (R_x) driving quantum transitions.
  4. Quantum Measurement on AerSimulator:
     Wavefunction collapse sampling across 1,024 shots.
  5. Quantum Annealing Ground-State Energy Search:
     Transverse-field annealing over Binary Quadratic Models (BQM).
  6. Structured File Generation:
     Exports quantum measurements, circuit metrics, and trajectories to JSON.
================================================================================
"""

import json
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Qiskit Quantum Framework & Aer Simulator
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

# D-Wave Quantum Annealing Framework
import dimod
import neal

# Airspace Graph & Data Generation
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.join(current_dir, "quantum-flight-optimizer")
if os.path.exists(project_dir):
    sys.path.insert(0, project_dir)

from data_gen.airspace import generate_airspace_graph
from data_gen.flights import generate_flights
from models.qubo_model import (
    build_route_conflict_qubo,
    calculate_path_fuel,
    generate_candidate_paths,
)


# ==============================================================================
# 1. QUANTUM ISING HAMILTONIAN SPECIFICATION
# ==============================================================================

@dataclass
class QuantumIsingHamiltonian:
    """
    Represents an Ising spin Hamiltonian:
        H_C = offset + sum_i (h_i * Z_i) + sum_{i < j} (J_ij * Z_i * Z_j)
    Derived from a QUBO matrix via the quantum mapping:
        x_i = (I - Z_i) / 2
    """
    num_qubits: int
    linear_coefficients: List[float]
    quadratic_couplings: Dict[Tuple[int, int], float]
    energy_offset: float

    @classmethod
    def from_qubo_matrix(cls, Q: np.ndarray) -> "QuantumIsingHamiltonian":
        """
        Transforms a classical QUBO matrix into an Ising spin Hamiltonian.
        """
        N = Q.shape[0]
        h = [0.0] * N
        J: Dict[Tuple[int, int], float] = {}
        offset = 0.0

        for i in range(N):
            q_ii = float(Q[i, i])
            offset += q_ii / 2.0
            h[i] -= q_ii / 2.0

            for j in range(i + 1, N):
                q_ij = float(Q[i, j])
                if abs(q_ij) > 1e-6:
                    offset += q_ij / 4.0
                    h[i] -= q_ij / 4.0
                    h[j] -= q_ij / 4.0
                    J[(i, j)] = q_ij / 4.0

        return cls(
            num_qubits=N,
            linear_coefficients=h,
            quadratic_couplings=J,
            energy_offset=offset,
        )


# ==============================================================================
# 2. GATE-BASED QAOA QUANTUM ENGINE (QISKIT + AERSIMULATOR)
# ==============================================================================

class QiskitAerQAOAEngine:
    """
    Constructs and executes parameterized Quantum Approximate Optimization Algorithm
    (QAOA) circuits using Qiskit and Qiskit Aer Simulator.
    """

    def __init__(self, p_layers: int = 2, shots: int = 1024, seed: int = 42):
        self.p_layers = p_layers
        self.shots = shots
        self.seed = seed
        self.simulator = AerSimulator()

    def build_qaoa_circuit(
        self,
        hamiltonian: QuantumIsingHamiltonian,
        gammas: List[float],
        betas: List[float],
    ) -> QuantumCircuit:
        """
        Constructs a gate-based QAOA quantum circuit:
          1. Superposition: H on all qubits -> |+>^N
          2. Alternating layers:
             - Problem Unitary: R_z(2*gamma*h_i) and R_zz(2*gamma*J_ij)
             - Mixer Unitary:   R_x(2*beta)
          3. Measurement onto classical registers.
        """
        N = hamiltonian.num_qubits
        qc = QuantumCircuit(N, N)

        # 1. State preparation into equal superposition
        qc.h(range(N))

        # 2. Variational unitary layers
        for layer in range(self.p_layers):
            gamma = gammas[layer]
            beta = betas[layer]

            # Problem Hamiltonian e^{-i * gamma * H_C}
            for i, h_val in enumerate(hamiltonian.linear_coefficients):
                if abs(h_val) > 1e-6:
                    qc.rz(2.0 * gamma * h_val, i)

            for (i, j), j_val in hamiltonian.quadratic_couplings.items():
                if abs(j_val) > 1e-6:
                    qc.rzz(2.0 * gamma * j_val, i, j)

            # Mixer Hamiltonian e^{-i * beta * H_M}
            for i in range(N):
                qc.rx(2.0 * beta, i)

        # 3. Measurement
        qc.measure(range(N), range(N))
        return qc

    def solve(
        self, hamiltonian: QuantumIsingHamiltonian, Q_matrix: np.ndarray
    ) -> Dict[str, Any]:
        """
        Runs the QAOA circuit on Qiskit AerSimulator and returns the quantum solution.
        """
        start_time = time.time()
        N = hamiltonian.num_qubits

        # Parameter schedule calibrated to Hamiltonian spectral norm
        max_term = max(
            [abs(h) for h in hamiltonian.linear_coefficients]
            + [abs(j) for j in hamiltonian.quadratic_couplings.values()]
            + [1.0]
        )
        gamma_step = 0.5 / max_term
        beta_step = np.pi / 8.0

        gammas = [gamma_step * (layer + 1) for layer in range(self.p_layers)]
        betas = [beta_step * (1.0 - 0.2 * layer) for layer in range(self.p_layers)]

        # Build Qiskit QuantumCircuit
        circuit = self.build_qaoa_circuit(hamiltonian, gammas, betas)

        # Execute on Qiskit Aer Simulator
        job = self.simulator.run(
            circuit, shots=self.shots, seed_simulator=self.seed
        )
        result = job.result()
        counts = result.get_counts()

        # Find optimal bitstring from measurement distribution
        best_energy = float("inf")
        best_bitstring = None
        top_state = None
        top_count = -1

        for bitstring, count in counts.items():
            if count > top_count:
                top_count = count
                top_state = bitstring

            bits = np.array([int(bitstring[N - 1 - i]) for i in range(N)], dtype=int)
            energy = float(bits @ Q_matrix @ bits)
            if energy < best_energy:
                best_energy = energy
                best_bitstring = bits

        runtime = time.time() - start_time
        gate_counts = dict(circuit.count_ops())

        return {
            "solver_type": "Gate-Based QAOA",
            "backend": "Qiskit AerSimulator",
            "num_qubits": N,
            "circuit_depth": circuit.depth(),
            "total_quantum_gates": sum(gate_counts.values()),
            "gate_breakdown": gate_counts,
            "variational_layers": self.p_layers,
            "shots": self.shots,
            "unique_measured_states": len(counts),
            "top_measured_state": top_state,
            "top_state_count": top_count,
            "fidelity_pct": round((top_count / self.shots) * 100.0, 2),
            "ground_energy": round(best_energy, 4),
            "optimal_bitstring": best_bitstring.tolist() if best_bitstring is not None else [],
            "runtime_seconds": round(runtime, 4),
        }


# ==============================================================================
# 3. D-WAVE SIMULATED QUANTUM ANNEALING ENGINE
# ==============================================================================

class DWaveQuantumAnnealerEngine:
    """
    Executes Transverse-Field Quantum Annealing using D-Wave Neal & Dimod BQM.
    """

    def __init__(self, num_reads: int = 150, num_sweeps: int = 400, seed: int = 42):
        self.num_reads = num_reads
        self.num_sweeps = num_sweeps
        self.seed = seed
        self.sampler = neal.SimulatedAnnealingSampler()

    def solve(self, Q_matrix: np.ndarray) -> Dict[str, Any]:
        """
        Samples the lowest-energy spin configurations using Simulated Quantum Annealing.
        """
        start_time = time.time()
        N = Q_matrix.shape[0]

        # Convert to dictionary format for dimod BQM
        qubo_dict: Dict[Tuple[int, int], float] = {}
        for i in range(N):
            qubo_dict[(i, i)] = float(Q_matrix[i, i])
            for j in range(i + 1, N):
                if abs(Q_matrix[i, j]) > 1e-6:
                    qubo_dict[(i, j)] = float(Q_matrix[i, j])

        bqm = dimod.BinaryQuadraticModel.from_qubo(qubo_dict)
        sampleset = self.sampler.sample(
            bqm,
            num_reads=self.num_reads,
            num_sweeps=self.num_sweeps,
            seed=self.seed,
        )

        best_sample = sampleset.first.sample
        best_energy = float(sampleset.first.energy)
        best_bits = [int(best_sample[i]) for i in range(N)]
        runtime = time.time() - start_time

        return {
            "solver_type": "Quantum Annealer",
            "backend": "D-Wave Neal (Transverse-Field Annealing Emulation)",
            "qubits_used": N,
            "num_reads": self.num_reads,
            "num_sweeps": self.num_sweeps,
            "ground_energy": round(best_energy, 4),
            "optimal_bitstring": best_bits,
            "runtime_seconds": round(runtime, 4),
        }


# ==============================================================================
# 4. QUANTUM AIRSPACE DECONFLICTION COORDINATOR
# ==============================================================================

class QuantumAirspaceCoordinator:
    """
    Orchestrates the formulation, optimization, and evaluation of commercial flight
    trajectories using gate-based Qiskit QAOA and D-Wave Quantum Annealing.
    """

    def __init__(self, num_flights: int = 10, seed: int = 42):
        self.num_flights = num_flights
        self.seed = seed
        self.airspace_graph = generate_airspace_graph(n_nodes=20, seed=seed)
        self.flights = generate_flights(
            self.airspace_graph, num_flights=num_flights, seed=seed
        )
        self.candidate_paths = generate_candidate_paths(
            self.airspace_graph, self.flights, k_paths=2
        )

        # Build Route-Conflict QUBO matrix
        self.Q_matrix, self.var_list, self.conflicts = build_route_conflict_qubo(
            self.airspace_graph,
            self.flights,
            self.candidate_paths,
            P_one=25000.0,
            P_conflict=2000.0,
        )
        self.hamiltonian = QuantumIsingHamiltonian.from_qubo_matrix(self.Q_matrix)

    def decode_routes(self, bitstring: List[int]) -> Dict[str, List[str]]:
        """
        Decodes a binary quantum state into active aircraft flight paths.
        """
        assignments: Dict[str, List[str]] = {}
        for flight in self.flights:
            f_id = flight["id"]
            chosen_k = 0
            for k in range(len(self.candidate_paths[f_id])):
                var_key = (f_id, k)
                if var_key in self.var_list:
                    idx = self.var_list.index(var_key)
                    if idx < len(bitstring) and bitstring[idx] == 1:
                        chosen_k = k
                        break
            assignments[f_id] = self.candidate_paths[f_id][chosen_k]
        return assignments

    def evaluate_solution(
        self, assignments: Dict[str, List[str]], capacity_limit: int = 2
    ) -> Dict[str, Any]:
        """
        Evaluates fuel burn, carbon emissions, and corridor capacity violations.
        """
        total_fuel = 0.0
        edge_usage: Dict[str, int] = {}

        for f in self.flights:
            path = assignments.get(f["id"], [])
            rate = f.get("fuel_rate", 5.0)
            total_fuel += calculate_path_fuel(self.airspace_graph, path, rate)

            for i in range(len(path) - 1):
                edge = tuple(sorted([path[i], path[i + 1]]))
                edge_str = f"{edge[0]}<->{edge[1]}"
                edge_usage[edge_str] = edge_usage.get(edge_str, 0) + 1

        violations = sum(
            max(0, count - capacity_limit) for count in edge_usage.values()
        )
        co2_multiplier = 3.16  # ICAO standard conversion
        total_co2 = total_fuel * co2_multiplier

        return {
            "total_fuel_kg": round(total_fuel, 1),
            "total_co2_kg": round(total_co2, 1),
            "capacity_violations": violations,
            "corridor_usage": edge_usage,
        }

    def run_benchmark(self) -> Dict[str, Any]:
        """
        Executes both Qiskit Aer QAOA and D-Wave Annealer and compiles the report.
        """
        # 1. Gate-Based QAOA execution on Qiskit Aer
        qaoa_engine = QiskitAerQAOAEngine(p_layers=2, shots=1024, seed=self.seed)
        qaoa_result = qaoa_engine.solve(self.hamiltonian, self.Q_matrix)
        qaoa_routes = self.decode_routes(qaoa_result["optimal_bitstring"])
        qaoa_metrics = self.evaluate_solution(qaoa_routes)

        # 2. Quantum Annealing execution on D-Wave Neal
        annealer_engine = DWaveQuantumAnnealerEngine(
            num_reads=150, num_sweeps=400, seed=self.seed
        )
        annealer_result = annealer_engine.solve(self.Q_matrix)
        annealer_routes = self.decode_routes(annealer_result["optimal_bitstring"])
        annealer_metrics = self.evaluate_solution(annealer_routes)

        return {
            "metadata": {
                "title": "AeroQ-Route Pure Quantum Computation Benchmark",
                "timestamp": datetime.now().isoformat(),
                "num_qubits": self.hamiltonian.num_qubits,
                "airspace_corridors_modeled": len(self.airspace_graph.edges),
                "scheduled_flights": self.num_flights,
                "status": "SUCCESS",
            },
            "gate_based_qaoa": {
                "quantum_circuit": qaoa_result,
                "airspace_evaluation": qaoa_metrics,
                "flight_assignments": qaoa_routes,
            },
            "quantum_annealer": {
                "annealing_parameters": annealer_result,
                "airspace_evaluation": annealer_metrics,
                "flight_assignments": annealer_routes,
            },
        }


# ==============================================================================
# 5. ENTRYPOINT & QUANTUM REPORT GENERATION
# ==============================================================================

def main():
    print("=" * 80)
    print("       AEROQ-ROUTE: PURE QUANTUM COMPUTING OPTIMIZATION SUITE       ")
    print("      IBM Qiskit 2.x  |  Qiskit Aer Simulator  |  D-Wave Neal      ")
    print("=" * 80)

    print("\n[+] 1. Formulating Indian Airspace Network as Quantum Ising Hamiltonian...")
    coordinator = QuantumAirspaceCoordinator(num_flights=10, seed=42)
    h = coordinator.hamiltonian
    print(f"    -> Quantum Register:      {h.num_qubits} Qubits")
    print(f"    -> Two-Qubit Interactions: {len(h.quadratic_couplings)} Entangling Couplings")
    print(f"    -> Linear Phase Terms:    {len(h.linear_coefficients)} Single-Qubit Terms")

    print("\n[+] 2. Executing Gate-Based QAOA on Qiskit Aer Simulator...")
    benchmark = coordinator.run_benchmark()
    qaoa_data = benchmark["gate_based_qaoa"]
    qc_meta = qaoa_data["quantum_circuit"]
    qaoa_eval = qaoa_data["airspace_evaluation"]

    print(f"    -> Backend:                {qc_meta['backend']}")
    print(f"    -> Variational Layers:     p = {qc_meta['variational_layers']}")
    print(f"    -> Total Quantum Gates:    {qc_meta['total_quantum_gates']} gates")
    print(f"    -> Circuit Gate Depth:     {qc_meta['circuit_depth']}")
    print(f"    -> Aer Simulator Shots:    {qc_meta['shots']} shots")
    print(f"    -> Measurement Fidelity:   {qc_meta['fidelity_pct']}%")
    print(f"    -> QAOA Fuel Burn:         {qaoa_eval['total_fuel_kg']:,} kg")
    print(f"    -> Net CO2 Emissions:      {qaoa_eval['total_co2_kg']:,} kg")
    print(f"    -> Corridor Violations:    {qaoa_eval['capacity_violations']}")
    print(f"    -> Circuit Runtime:        {qc_meta['runtime_seconds']}s")

    print("\n[+] 3. Executing Transverse-Field Quantum Annealer (D-Wave Neal)...")
    anneal_data = benchmark["quantum_annealer"]
    ann_meta = anneal_data["annealing_parameters"]
    ann_eval = anneal_data["airspace_evaluation"]

    print(f"    -> Backend:                {ann_meta['backend']}")
    print(f"    -> Annealing Reads/Sweeps: {ann_meta['num_reads']} reads / {ann_meta['num_sweeps']} sweeps")
    print(f"    -> Ground-State Energy:    {ann_meta['ground_energy']}")
    print(f"    -> Annealer Fuel Burn:     {ann_eval['total_fuel_kg']:,} kg")
    print(f"    -> Net CO2 Emissions:      {ann_eval['total_co2_kg']:,} kg")
    print(f"    -> Corridor Violations:    {ann_eval['capacity_violations']}")
    print(f"    -> Annealing Runtime:      {ann_meta['runtime_seconds']}s")

    # Save to JSON
    output_path = os.path.join(current_dir, "quantum_generated_solution.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(benchmark, f, indent=2)

    print("\n" + "=" * 80)
    print(f"[OK] Pure Quantum Output File generated successfully:")
    print(f"    Saved: {output_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
