"""
Quantum Annealer Emulation Solver for AeroQ-Route.
==================================================
Uses dimod and dwave-neal (SimulatedAnnealingSampler) to emulate quantum annealing locally.

For First-Year B.Tech Students:
- Physical Quantum Annealers (such as D-Wave Advantage) utilize transverse-field quantum tunneling
  to traverse rugged multi-dimensional energy barriers, finding the global ground state of an Ising model.
- D-Wave Neal emulates this physical tunneling process classically on CPU using simulated annealing
  with a geometric inverse temperature schedule (beta_0 -> beta_1) and Metropolis-Hastings state transitions.
- This solver builds the compact Route-Conflict QUBO matrix, instantiates a dimod Binary Quadratic Model (BQM),
  samples low-energy states, filters constraint-compliant bitstrings, and selects the optimal deconflicted flight paths.
"""

import time
from typing import Any, Dict, List, Optional
import dimod
import neal
import networkx as nx

from .base import BaseSolver
from .classical import DijkstraSolver
from models.qubo_model import (
    generate_candidate_paths,
    build_route_conflict_qubo,
    calculate_path_fuel,
)


class AnnealerSolver(BaseSolver):
    """
    Quantum Annealer Emulator using dwave-neal.
    Finds the ground state of the Route-Conflict Airspace QUBO.
    """

    def __init__(self, name: str = "Sim Annealer (Neal)"):
        super().__init__(name=name)

    def _decode_sample(
        self,
        sample: Dict[int, int],
        flights: List[Dict],
        candidate_paths: Dict[str, List[List[str]]],
        var_list: List[tuple],
        G: nx.Graph
    ) -> Dict[str, List[str]]:
        """
        Decodes a binary sample dictionary into a complete flight assignment dictionary.
        Applies minimum-fuel tie-breaking if multiple candidate paths are active for a flight.
        """
        assignments = {}
        for flight in flights:
            f_id = flight['id']
            rate = flight.get('fuel_rate', 5.0)
            paths = candidate_paths.get(f_id, [])

            if not paths:
                continue

            # Identify candidate indices where the decision variable bit is 1
            active_ks = []
            for k in range(len(paths)):
                var_key = (f_id, k)
                if var_key in var_list:
                    var_idx = var_list.index(var_key)
                    if sample.get(var_idx, sample.get(var_key, 0)) == 1:
                        active_ks.append(k)

            # Constraint resolution:
            # 1. Exactly one active candidate -> select it directly
            # 2. Multiple active candidates -> pick the one with lowest fuel burn
            # 3. Zero active candidates -> fallback to candidate 0 (shortest path)
            if len(active_ks) == 1:
                chosen_k = active_ks[0]
            elif len(active_ks) > 1:
                chosen_k = min(active_ks, key=lambda k: calculate_path_fuel(G, paths[k], rate))
            else:
                chosen_k = 0

            assignments[f_id] = paths[chosen_k]

        return assignments

    def solve(
        self,
        G: nx.Graph,
        flights: List[Dict],
        P_path: float = 15000.0,
        P_cap: float = 8000.0,
        num_reads: int = 150,
        num_sweeps: int = 500,
        k_paths: int = 2,
        seed: Optional[int] = 42,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Solves the airspace flight deconfliction problem using D-Wave Neal Simulated Annealing.

        Parameters:
        -----------
        G : nx.Graph
            Airspace graph network with edge distances and capacities.
        flights : List[Dict]
            List of commercial flight schedules.
        P_path : float
            Penalty coefficient enforcing exactly one path per aircraft.
        P_cap : float
            Penalty coefficient penalizing simultaneous airway corridor congestion.
        num_reads : int
            Number of simulated annealing spin configuration reads.
        num_sweeps : int
            Number of Monte Carlo sweeps per annealing run.
        k_paths : int
            Number of candidate trajectories generated per flight (default: 2).
        seed : Optional[int]
            Random seed for deterministic reproducibility.

        Returns:
        --------
        Dict[str, Any]:
            Dictionary containing assignments, fuel burn, CO2, violations, latency, and QUBO details.
        """
        start_time = time.time()

        if not flights:
            return DijkstraSolver().solve(G, flights)

        # 1. Generate K candidate paths per flight
        candidate_paths = generate_candidate_paths(G, flights, k_paths=k_paths)

        # 2. Build the Route-Conflict QUBO Matrix
        Q, var_list, conflicts = build_route_conflict_qubo(
            G, flights, candidate_paths,
            P_one=P_path, P_conflict=P_cap
        )

        if len(var_list) == 0 or Q.shape[0] == 0:
            return DijkstraSolver().solve(G, flights)

        # 3. Create Binary Quadratic Model directly from the QUBO numpy array
        bqm = dimod.BinaryQuadraticModel(Q, 'BINARY')

        # 4. Sample ground states via Neal Simulated Annealing
        sampler = neal.SimulatedAnnealingSampler()
        sampleset = sampler.sample(
            bqm,
            num_reads=num_reads,
            num_sweeps=num_sweeps,
            seed=seed
        )

        # 5. Multi-Sample Spectrum Evaluation:
        # Explore the lowest-energy states to select the physical minimum (fuel + penalty * violations)
        best_score = float('inf')
        best_assignments: Dict[str, List[str]] = {}
        best_fuel = 0.0
        best_co2 = 0.0
        best_violations = 0
        best_edge_usage: Dict[str, int] = {}
        best_energy = float(sampleset.first.energy) if len(sampleset) > 0 else 0.0
        evaluated_samples = 0

        # Evaluate unique low-energy samples from the read distribution
        for record in sampleset.data(['sample', 'energy', 'num_occurrences']):
            sample_dict = record.sample
            sample_energy = float(record.energy)
            evaluated_samples += 1

            # Decode candidate route assignment
            candidate_assign = self._decode_sample(
                sample_dict, flights, candidate_paths, var_list, G
            )

            # Evaluate physical airspace metrics
            fuel, co2, viols, usage = self.evaluate_solution(G, flights, candidate_assign)

            # Combinatorial objective score: Fuel burn + large violation barrier
            score = fuel + 50000.0 * viols

            if score < best_score:
                best_score = score
                best_assignments = candidate_assign
                best_fuel = fuel
                best_co2 = co2
                best_violations = viols
                best_edge_usage = usage
                best_energy = sample_energy

            # Limit evaluation to top 25 low-energy unique configurations for maximum speed
            if evaluated_samples >= 25:
                break

        # Fallback if no valid sample was selected
        if not best_assignments:
            for f in flights:
                best_assignments[f['id']] = candidate_paths[f['id']][0]
            best_fuel, best_co2, best_violations, best_edge_usage = self.evaluate_solution(
                G, flights, best_assignments
            )

        runtime = time.time() - start_time

        return {
            'solver_name': self.name,
            'assignments': best_assignments,
            'total_fuel': best_fuel,
            'total_co2': best_co2,
            'violations': best_violations,
            'runtime_sec': round(runtime, 4),
            'edge_usage': best_edge_usage,
            'details': {
                'qubo_energy': round(best_energy, 2),
                'qubo_variables': int(Q.shape[0]),
                'conflicts_modeled': len(conflicts),
                'num_reads': num_reads,
                'num_sweeps': num_sweeps,
                'samples_evaluated': evaluated_samples,
                'method': 'D-Wave Neal BQM Metropolis-Hastings Sampling'
            }
        }
