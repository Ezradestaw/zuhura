// Client for the A* traverse planner (POST /api/v1/spatial/navigation/astar).

export type Vehicle = 'car' | 'rover';

export interface PathPoint {
  latitude: number;
  longitude: number;
  elevation_m: number;
  distance_km: number;
  slope_degrees: number;
  roughness_tri: number;
}

export interface AStarRoute {
  route_id: string;
  name: string;
  description: string;
  vehicle: Vehicle;
  max_slope_limit_deg: number;
  max_roughness_limit_m: number;
  total_distance_km: number;
  direct_distance_km: number;
  detour_factor: number;
  elevation_gain_m: number;
  elevation_loss_m: number;
  max_slope_degrees: number;
  mean_slope_degrees: number;
  waypoints: PathPoint[];
  grid: {
    rows: number;
    cols: number;
    cell_size_m: number;
    blocked_percent: number;
    cells_expanded: number;
  };
  dataset: string;
}

export async function findPath(
  start: { lat: number; lon: number },
  end: { lat: number; lon: number },
  vehicle: Vehicle,
): Promise<AStarRoute> {
  let res: Response;
  try {
    res = await fetch('/api/v1/spatial/navigation/astar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        start_latitude: start.lat,
        start_longitude: start.lon,
        destination_latitude: end.lat,
        destination_longitude: end.lon,
        vehicle,
      }),
    });
  } catch {
    throw new Error('Could not reach the server. Check that the backend is running.');
  }
  if (!res.ok) {
    let detail = `Path finding failed (HTTP ${res.status}).`;
    try {
      const body = await res.json();
      if (typeof body?.detail === 'string') detail = body.detail;
    } catch {
      // not JSON
    }
    throw new Error(detail);
  }
  return res.json();
}
