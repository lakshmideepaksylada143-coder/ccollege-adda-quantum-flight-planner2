# Models Module (`models`)

The `models` package contains mathematical optimization models and QUBO (Quadratic Unconstrained Binary Optimization) formulations for trajectory selection, fuel minimization, and conflict avoidance.

<p align="center">
  <img src="../docs/images/system_architecture_diagram.jpg" alt="Optimization Pipeline Architecture" width="100%">
</p>

---

## File Structure

```
models/
├── __init__.py      # Module exports: build_qubo, build_route_conflict_qubo, calculate_path_fuel, generate_candidate_paths
├── qubo_model.py    # QUBO formulations, Yen's K-path generator, and Ising transformation
└── README.md        # Documentation for models (this file)
```

---

## 1. What is a QUBO?

A **QUBO** minimizes a quadratic polynomial over binary decision variables $x_i \in \{0, 1\}$:

$$H(x) = \sum_{i} Q_{i,i} x_i + \sum_{i < j} Q_{i,j} x_i x_j = x^T Q x$$

- **Diagonal terms ($Q_{i,i}$)**: Linear objective costs (e.g. estimated fuel burn for choosing candidate route $i$).
- **Off-diagonal terms ($Q_{i,j}$)**: Quadratic pairwise penalty terms (e.g. bottleneck penalties when two flights share an airway during the same departure window).

---

## 2. Quantum Mapping (Ising Spin Hamiltonian)

Gate-based quantum algorithms (QAOA) and quantum annealers operate natively on Pauli-Z spin operators $\sigma_i^z \in \{-1, +1\}$:

$$x_i = \frac{1 - \sigma_i^z}{2}$$

Substituting $x_i$ transforms the QUBO into an Ising spin glass Hamiltonian:

$$H_{\text{Ising}} = \sum_i h_i \sigma_i^z + \sum_{i < j} J_{ij} \sigma_i^z \sigma_j^z + \text{offset}$$

Physical qubits naturally evolve under transverse magnetic fields to relax towards the minimum-energy ground state of $H_{\text{Ising}}$.

---

## 3. Mathematical Formulations in `qubo_model.py`

### A. Candidate Path Generation (`generate_candidate_paths`)
Uses **Yen's K-shortest simple paths algorithm** (`nx.shortest_simple_paths`) weighted by airway fuel burn. For each flight $f$, it discovers $K \in \{2, 3\}$ alternative flight trajectories connecting origin to destination.

### B. Route-Selection Conflict QUBO (`build_route_conflict_qubo`)
This compact formulation is optimized for Quantum Annealers (D-Wave) and Gate-Based QAOA circuits ($\le 16$ qubits).

#### Variable Definition
$$y_{f, k} \in \{0, 1\} \quad (\text{Flight } f \text{ chooses candidate path } k)$$
Total variables: $N = F \times K$.

#### 1. Objective: Fuel Burn
$$Q_{i, i} \mathrel{+}= \text{Fuel}(p_{f, k})$$

#### 2. Hard Constraint: Exactly One Path Per Flight
$$\left(\sum_{k=1}^K y_{f, k} - 1\right)^2 = \sum_k y_k^2 + 2 \sum_{k < l} y_k y_l - 2 \sum_k y_k + 1 = - \sum_k y_k + 2 \sum_{k < l} y_k y_l + 1$$
In the QUBO matrix:
- Diagonal: $Q_{i, i} \mathrel{-}= P_{\text{one}}$
- Off-diagonal: $Q_{i, j} \mathrel{+}= 2.0 \times P_{\text{one}}$

> **Critical Penalty Calibration Rule**:  
> In commercial aviation, individual flight fuel burn typically reaches $7{,}000$ to $12{,}000\text{ kg}$. If $P_{\text{one}} < \text{Fuel}$, choosing 0 paths ($y=0$) yields lower energy than choosing 1 path ($y=1$).  
> To guarantee that the ground state strictly enforces flight paths, `build_route_conflict_qubo` automatically calibrates:
> $$P_{\text{one}}^{\text{effective}} = \max\left(P_{\text{one}}, 1.5 \times \max_{f, k}(\text{Fuel}(p_{f, k}))\right)$$

#### 3. Soft Constraint: Spatiotemporal Bottleneck Conflicts
When two flights $f_1, f_2$ have overlapping departure slots ($|\text{slot}_1 - \text{slot}_2| \le 1$) and share airway corridors:
$$Q_{i, j} \mathrel{+}= P_{\text{conflict}} \times |\text{shared corridors}|$$

### C. Edge-Based QUBO (`build_qubo`)
Formulates direct airway corridor variables $x_{f, e} \in \{0, 1\}$ (indicating flight $f$ traverses edge $e$):
- Diagonal fuel costs.
- Quadratic pairwise capacity penalties on congested edges.
- Flow continuity and degree conservation constraints at departure and arrival endpoints:
  $$\left(\sum_{e \in \text{incident}(\text{origin})} x_{f, e} - 1\right)^2 \times P_{\text{path}}$$

---

## Usage Example

```python
from data_gen import generate_airspace_graph, generate_flights
from models import generate_candidate_paths, build_route_conflict_qubo

# 1. Generate airspace & flights
G = generate_airspace_graph(n_nodes=15, seed=42)
flights = generate_flights(G, num_flights=6, seed=42)

# 2. Candidate paths
candidates = generate_candidate_paths(G, flights, k_paths=2)

# 3. Build QUBO Matrix
Q, var_list, conflicts = build_route_conflict_qubo(
    G, flights, candidates,
    P_one=25000.0, P_conflict=2000.0
)

print(f"QUBO Shape: {Q.shape} ({len(var_list)} binary variables)")
print(f"Airspace Bottleneck Conflicts Detected: {len(conflicts)}")
```
