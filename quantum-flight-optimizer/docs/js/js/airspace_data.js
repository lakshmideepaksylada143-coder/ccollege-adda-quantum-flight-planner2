/**
 * AeroQ-Route Airspace Network & Aviation Fleet Database
 */

const AIRPORTS_DB = {
  DEL: { lon: 77.1025, lat: 28.7041, name: "Indira Gandhi Int'l (Delhi)", region: "North", type: "hub" },
  BOM: { lon: 72.8777, lat: 19.0760, name: "Chhatrapati Shivaji Maharaj (Mumbai)", region: "West", type: "hub" },
  HYD: { lon: 78.4867, lat: 17.3850, name: "Rajiv Gandhi Int'l (Hyderabad)", region: "Central", type: "hub" },
  BLR: { lon: 77.5946, lat: 12.9716, name: "Kempegowda Int'l (Bengaluru)", region: "South", type: "hub" },
  MAA: { lon: 80.2707, lat: 13.0827, name: "Chennai Int'l (Chennai)", region: "South", type: "hub" },
  CCU: { lon: 88.3639, lat: 22.5726, name: "Netaji Subhash Chandra Bose (Kolkata)", region: "East", type: "hub" },
  VTZ: { lon: 83.2242, lat: 17.6868, name: "Visakhapatnam Airport (Vizag)", region: "East", type: "hub" },
  AMD: { lon: 72.6347, lat: 23.0734, name: "Sardar Vallabhbhai Patel (Ahmedabad)", region: "West", type: "hub" }
};

const WAYPOINTS_DB = {
  NAG: { lon: 79.0882, lat: 21.1458, name: "Nagpur (Central India Crossroads)", region: "Central", type: "fix" },
  BHO: { lon: 77.4126, lat: 23.2599, name: "Bhopal Corridor Fix", region: "Central", type: "fix" },
  JAI: { lon: 75.7873, lat: 26.9124, name: "Jaipur Waypoint", region: "North", type: "fix" },
  LKO: { lon: 80.9462, lat: 26.8467, name: "Lucknow Waypoint", region: "North", type: "fix" },
  GOI: { lon: 73.8315, lat: 15.3800, name: "Goa Coastal Fix", region: "West", type: "fix" },
  COK: { lon: 76.2673, lat: 9.9312, name: "Kochi Oceanic Fix", region: "South", type: "fix" },
  IXC: { lon: 76.7794, lat: 30.7333, name: "Chandigarh Fix", region: "North", type: "fix" },
  GAU: { lon: 91.7362, lat: 26.1445, name: "Guwahati Eastern Fix", region: "East", type: "fix" },
  WP1: { lon: 75.4000, lat: 21.8000, name: "West-Central Corridor WP1", region: "Central", type: "fix" },
  WP2: { lon: 79.8000, lat: 15.6000, name: "Deccan Plateau Fix WP2", region: "South", type: "fix" },
  WP3: { lon: 84.5000, lat: 21.0000, name: "Bay of Bengal Inland WP3", region: "East", type: "fix" },
  WP4: { lon: 78.1000, lat: 25.4000, name: "Gangetic Plain WP4", region: "North", type: "fix" }
};

const AIRCRAFT_SPECS = {
  "A320neo": { name: "Airbus A320neo", fuel_rate: 4.5, speed: 840, wake: "Medium" },
  "B737-800": { name: "Boeing 737-800", fuel_rate: 5.0, speed: 830, wake: "Medium" },
  "A321neo": { name: "Airbus A321neo", fuel_rate: 5.8, speed: 845, wake: "Medium" },
  "ATR72": { name: "ATR 72-600", fuel_rate: 2.8, speed: 510, wake: "Light" },
  "B787-9": { name: "Boeing 787-9", fuel_rate: 6.5, speed: 900, wake: "Heavy" }
};

// Haversine Great Circle distance in km
function haversineDist(lon1, lat1, lon2, lat2) {
  const R = 6371.0;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

// Scheduled commercial flights
const SAMPLE_FLIGHTS = [
  { id: "F0", origin: "DEL", dest: "BOM", aircraft: "A320neo", slot: 0,
    paths: [
      ["DEL", "JAI", "AMD", "BOM"],
      ["DEL", "BHO", "WP1", "BOM"]
    ]
  },
  { id: "F1", origin: "BOM", dest: "DEL", aircraft: "B737-800", slot: 0,
    paths: [
      ["BOM", "AMD", "JAI", "DEL"],
      ["BOM", "WP1", "BHO", "DEL"]
    ]
  },
  { id: "F2", origin: "DEL", dest: "BLR", aircraft: "A321neo", slot: 1,
    paths: [
      ["DEL", "BHO", "NAG", "HYD", "BLR"],
      ["DEL", "WP4", "NAG", "WP2", "BLR"]
    ]
  },
  { id: "F3", origin: "BLR", dest: "DEL", aircraft: "A320neo", slot: 1,
    paths: [
      ["BLR", "HYD", "NAG", "BHO", "DEL"],
      ["BLR", "WP2", "NAG", "WP4", "DEL"]
    ]
  },
  { id: "F4", origin: "BOM", dest: "HYD", aircraft: "ATR72", slot: 0,
    paths: [
      ["BOM", "WP1", "HYD"],
      ["BOM", "GOI", "BLR", "HYD"]
    ]
  },
  { id: "F5", origin: "HYD", dest: "BOM", aircraft: "B737-800", slot: 0,
    paths: [
      ["HYD", "WP1", "BOM"],
      ["HYD", "BLR", "GOI", "BOM"]
    ]
  },
  { id: "F6", origin: "DEL", dest: "MAA", aircraft: "B787-9", slot: 2,
    paths: [
      ["DEL", "LKO", "WP3", "VTZ", "MAA"],
      ["DEL", "BHO", "NAG", "HYD", "MAA"]
    ]
  },
  { id: "F7", origin: "CCU", dest: "DEL", aircraft: "A320neo", slot: 2,
    paths: [
      ["CCU", "WP3", "LKO", "DEL"],
      ["CCU", "WP3", "BHO", "DEL"]
    ]
  },
  { id: "F8", origin: "BLR", dest: "HYD", aircraft: "ATR72", slot: 1,
    paths: [
      ["BLR", "WP2", "HYD"],
      ["BLR", "MAA", "HYD"]
    ]
  },
  { id: "F9", origin: "BOM", dest: "CCU", aircraft: "A321neo", slot: 1,
    paths: [
      ["BOM", "WP1", "NAG", "WP3", "CCU"],
      ["BOM", "HYD", "VTZ", "CCU"]
    ]
  }
];

window.AeroData = {
  airports: AIRPORTS_DB,
  waypoints: WAYPOINTS_DB,
  aircraft: AIRCRAFT_SPECS,
  sampleFlights: SAMPLE_FLIGHTS,
  haversineDist: haversineDist
};
