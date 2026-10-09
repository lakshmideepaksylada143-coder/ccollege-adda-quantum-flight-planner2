# Tests Module (`tests`)

The `tests` package provides automated test suites and validation routines for **AeroQ-Route** using `pytest`.

---

## File Structure

```
tests/
├── test_solvers.py   # Complete test suite (9 test cases covering all modules)
└── README.md         # Documentation for tests (this file)
```

---

## Test Cases Breakdown (`test_solvers.py`)

| Test Function | Target Module | Description | Assertions |
| :--- | :--- | :--- | :--- |
| `test_haversine_distance` | `data_gen.airspace` | Validates Great-Circle distance formula | Delhi–Mumbai distance falls between $1{,}100\text{ km}$ and $1{,}250\text{ km}$ |
| `test_airspace_graph_generation` | `data_gen.airspace` | Validates network topology | Graph has requested node count, is fully connected, and edges have `distance`, `fuel_burn`, and `capacity` |
| `test_flight_generation` | `data_gen.flights` | Validates commercial schedule | Origin and destination exist in graph, unique IDs, positive fuel consumption rates |
| `test_candidate_paths` | `models.qubo_model` | Validates Yen's K-shortest paths | Exactly $K$ alternative paths per flight, each correctly connecting origin to destination |
| `test_route_conflict_qubo` | `models.qubo_model` | Validates QUBO matrix formulation | Matrix dimension matches $N = F \times K$, symmetric variable mapping |
| `test_dijkstra_solver` | `solvers.classical` | Validates Dijkstra greedy solver | Non-zero fuel, valid assignment for every flight, zero crashes |
| `test_exact_ilp_solver` | `solvers.classical` | Validates Exact ILP / Branch-and-Bound | Computes exact mathematical deconfliction without external solver failure |
| `test_annealer_solver` | `solvers.annealer` | Validates D-Wave Neal Simulated Annealer | Correctly samples BQM, decodes bitstrings, and enforces valid routes |
| `test_qaoa_solver` | `solvers.qaoa` | Validates Qiskit Gate-Based QAOA | Evaluates quantum circuit ansatz, optimizes ground state, and maps assignments |

---

## Running the Tests

From the `quantum-flight-optimizer` directory, run:

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run a specific test
pytest tests/test_solvers.py -k test_qaoa_solver

# Run tests silently
pytest
```

### Expected Output:
```text
tests/test_solvers.py::test_haversine_distance PASSED                    [ 11%]
tests/test_solvers.py::test_airspace_graph_generation PASSED             [ 22%]
tests/test_solvers.py::test_flight_generation PASSED                     [ 33%]
tests/test_solvers.py::test_candidate_paths PASSED                       [ 44%]
tests/test_solvers.py::test_route_conflict_qubo PASSED                   [ 55%]
tests/test_solvers.py::test_dijkstra_solver PASSED                       [ 66%]
tests/test_solvers.py::test_exact_ilp_solver PASSED                      [ 77%]
tests/test_solvers.py::test_annealer_solver PASSED                       [ 88%]
tests/test_solvers.py::test_qaoa_solver PASSED                           [100%]

============================== 9 passed in 1.12s ==============================
```
