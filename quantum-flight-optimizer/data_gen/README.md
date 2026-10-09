# Data Generation Module (`data_gen`)

The `data_gen` package provides realistic graph models of national airspace corridors and commercial flight schedules loosely modeled on the **Indian Subcontinent**.

<p align="center">
  <img src="../docs/images/indian_airspace_network.jpg" alt="Indian Airspace Network" width="100%">
</p>

---

## File Structure

```
data_gen/
├── __init__.py      # Module exports: generate_airspace_graph, generate_flights, haversine_distance
├── airspace.py      # NetworkX graph generator with airports, waypoints, and airway corridors
├── flights.py       # Commercial flight schedule generator with aircraft specifications
└── README.md        # Documentation for data_gen (this file)
```

---

## 1. Airspace Network Modeling (`airspace.py`)

In Air Traffic Management (ATM), national airspace is modeled as an undirected connected graph $G = (V, E)$:
- **Vertices ($V$)**: Major commercial airports and high-altitude navigational fixes (waypoints) defined by geographical coordinates $(\text{Longitude}, \text{Latitude})$.
- **Edges ($E$)**: Airway corridors connecting fixes and airports.

<p align="center">
  <img src="../docs/images/airports_coordinate_graph.jpg" alt="Indian Hub Airports Coordinate Graph" width="90%">
</p>

### Key Functions

#### `haversine_distance(lon1: float, lat1: float, lon2: float, lat2: float) -> float`
Calculates the great-circle distance between two points on the Earth's surface (radius $R \approx 6371.0\text{ km}$):
$$a = \sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1) \cos(\phi_2) \sin^2\left(\frac{\Delta \lambda}{2}\right)$$
$$c = 2 \cdot \text{atan2}\left(\sqrt{a}, \sqrt{1 - a}\right)$$
$$d = R \cdot c$$

#### `generate_airspace_graph(n_nodes: int = 20, seed: int = 42, default_capacity: int = 2) -> nx.Graph`
Constructs a connected NetworkX graph representing the airspace:

1. **Primary Indian Hubs (Base Airports)**:
   - `DEL`: Delhi Indira Gandhi International $(77.1025^\circ\text{E}, 28.7041^\circ\text{N})$
   - `BOM`: Mumbai Chhatrapati Shivaji Maharaj $(72.8777^\circ\text{E}, 19.0760^\circ\text{N})$
   - `HYD`: Hyderabad Rajiv Gandhi International $(78.4867^\circ\text{E}, 17.3850^\circ\text{N})$
   - `BLR`: Bengaluru Kempegowda International $(77.5946^\circ\text{E}, 12.9716^\circ\text{N})$
   - `MAA`: Chennai International $(80.2707^\circ\text{E}, 13.0827^\circ\text{N})$
   - `CCU`: Kolkata Netaji Subhash Chandra Bose $(88.3639^\circ\text{E}, 22.5726^\circ\text{N})$
   - `VTZ`: Visakhapatnam Airport $(83.2242^\circ\text{E}, 17.6868^\circ\text{N})$

2. **Intermediate Waypoints / Regional Hubs**:
   - `NAG` (Nagpur), `BHO` (Bhopal), `JAI` (Jaipur), `LKO` (Lucknow), `GOI` (Goa), `COK` (Kochi), `IXC` (Chandigarh), `GAU` (Guwahati), plus synthetic navigational waypoints (`WP1`, `WP2`, ...).

3. **Airway Corridor Attributes**:
   - `distance`: Haversine distance in kilometers.
   - `wind_factor`: Atmospheric tailwind/headwind factor ($\sim 0.92$ to $1.25$).
   - `fuel_rate`: Base narrowbody fuel rate per km ($\sim 4.5$ to $5.5\text{ kg/km}$).
   - `fuel_burn`: Calculated as $\text{distance} \times \text{fuel\_rate} \times \text{wind\_factor}$.
   - `capacity`: Maximum simultaneous aircraft allowed safely in the airway corridor before triggering a bottleneck violation.

4. **Guaranteed Connectivity**:
   Ensures $G$ is a single connected component so every airport pair has at least one valid path.

---

## 2. Flight Schedule Generator (`flights.py`)

Commercial flights are scheduled between high-demand city pairs with realistic aircraft assignments and departure time windows.

### `AIRCRAFT_DATABASE`
| Aircraft Model | Fuel Rate (kg/km) | Cruise Speed (km/h) | Wake Turbulence Category |
| :--- | :---: | :---: | :---: |
| **Airbus A320neo** | 4.5 | 840 | Medium |
| **Boeing 737-800** | 5.0 | 830 | Medium |
| **Airbus A321neo** | 5.8 | 845 | Medium |
| **ATR 72-600** | 2.8 | 510 | Light |
| **Boeing 787-9** | 6.5 | 900 | Heavy |

### `generate_flights(G, num_flights, seed, num_time_slots, aircraft_specs)`
- Allocates high-demand pairs (e.g. DEL-BOM, DEL-BLR, BOM-HYD, CCU-DEL).
- Assigns discrete departure time slots (`slot` $\in \{0, 1, \dots, \text{num\_time\_slots}-1\}$) to model concurrent airspace occupancy.
- Supports custom fleet specifications from [`config.yaml`](file:///c:/Users/srinadh/New%20folder%20(2)/quantum-flight-optimizer/config.yaml).

---

## Usage Example

```python
from data_gen import generate_airspace_graph, generate_flights

# Generate airspace graph
G = generate_airspace_graph(n_nodes=20, seed=42, default_capacity=2)
print(f"Nodes: {len(G.nodes)}, Corridors: {len(G.edges)}")

# Generate 10 commercial flights
flights = generate_flights(G, num_flights=10, seed=42)
for f in flights[:3]:
    print(f"Flight {f['id']}: {f['origin']} -> {f['destination']} ({f['aircraft']}) at Slot {f['slot']}")
```
