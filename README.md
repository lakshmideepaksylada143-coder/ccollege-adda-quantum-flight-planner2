# AeroQ-Route Workspace

This workspace contains **AeroQ-Route**, a quantum-assisted aviation emissions and flight trajectory optimization system.

<p align="center">
  <img src="./quantum-flight-optimizer/docs/images/indian_airspace_network.jpg" alt="AeroQ-Route Indian Airspace Network" width="100%">
</p>

---

## Projects in this Workspace

### 🛫 [quantum-flight-optimizer](./quantum-flight-optimizer)
The core research, optimization, and benchmarking suite. Formulates commercial airspace corridor deconfliction as a **QUBO (Quadratic Unconstrained Binary Optimization)** problem and benchmarks:
- **Classical Greedy Dijkstra Baseline**
- **Exact Mixed-Integer Linear Programming (MILP / Branch-and-Bound)**
- **Simulated Quantum Annealing (D-Wave Neal)**
- **Gate-Based QAOA (Qiskit 2.x)**

### 🌐 [Interactive Web Visualizer & Radar](./quantum-flight-optimizer/web/index.html)
A real-time flight corridor radar and solver benchmark visualizer.
- **Run locally**: Open `quantum-flight-optimizer/web/index.html` in your web browser.
- **Deploy to GitHub Pages**: In your repository **Settings** > **Pages**:
  - **Source**: Select `Deploy from a branch` (Branch: `main` or `master`, Folder: `/docs` or `/ (root)`), OR
  - **Source**: Select `GitHub Actions` (using the included `.github/workflows/deploy-pages.yml`).

---

## Quick Start

```bash
# Navigate to the project directory
cd "quantum-flight-optimizer"

# Run the benchmark across all four solvers
python main.py

# Run the automated test suite
pytest tests/ -v
```

For complete documentation on mathematical derivations, architecture, configuration, and solver details, see:
- [quantum-flight-optimizer/README.md](./quantum-flight-optimizer/README.md)
- [quantum-flight-optimizer/data_gen/README.md](./quantum-flight-optimizer/data_gen/README.md)
- [quantum-flight-optimizer/models/README.md](./quantum-flight-optimizer/models/README.md)
- [quantum-flight-optimizer/solvers/README.md](./quantum-flight-optimizer/solvers/README.md)
- [quantum-flight-optimizer/tests/README.md](./quantum-flight-optimizer/tests/README.md)
