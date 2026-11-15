import { afterEach, describe, expect, it, vi } from 'vitest';
import { findPath, type AStarRoute } from '../src/lib/traverse';
import { buildTraverseCsv, buildTraverseGeoJson, buildTraverseKml } from '../src/lib/routeExport';

const route: AStarRoute = {
  route_id: 'astar_car',
  name: 'A* path',
  description: 'test',
  vehicle: 'car',
  max_slope_limit_deg: 10,
  max_roughness_limit_m: 60,
  total_distance_km: 8.2,
  direct_distance_km: 8.1,
  detour_factor: 1.01,
  elevation_gain_m: 80,
  elevation_loss_m: 0,
  max_slope_degrees: 2.2,
  mean_slope_degrees: 1.1,
  waypoints: [
    { latitude: 18.38, longitude: 77.58, elevation_m: -2560, distance_km: 0, slope_degrees: 0.5, roughness_tri: 3 },
    { latitude: 18.41, longitude: 77.52, elevation_m: -2520, distance_km: 4.1, slope_degrees: 1.1, roughness_tri: 4 },
    { latitude: 18.44, longitude: 77.45, elevation_m: -2480, distance_km: 8.2, slope_degrees: 2.2, roughness_tri: 5 },
  ],
  grid: { rows: 48, cols: 57, cell_size_m: 463, blocked_percent: 5, cells_expanded: 139 },
  dataset: 'MOLA',
};

describe('traverse planner client', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('posts both points and the vehicle', async () => {
    const fetchMock = vi.fn(async () => ({ ok: true, json: async () => route }));
    vi.stubGlobal('fetch', fetchMock);

    const result = await findPath({ lat: 18.38, lon: 77.58 }, { lat: 18.44, lon: 77.45 }, 'car');

    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe('/api/v1/spatial/navigation/astar');
    expect(JSON.parse(String(init.body))).toEqual({
      start_latitude: 18.38,
      start_longitude: 77.58,
      destination_latitude: 18.44,
      destination_longitude: 77.45,
      vehicle: 'car',
    });
    expect(result.waypoints).toHaveLength(3);
  });

  it('shows the server message when no path exists', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => ({ ok: false, status: 422, json: async () => ({ detail: 'No drivable path was found.' }) })),
    );
    await expect(findPath({ lat: 0, lon: 0 }, { lat: 1, lon: 1 }, 'car')).rejects.toThrow('No drivable path');
  });
});

describe('route export', () => {
  it('writes GeoJSON, CSV and KML', () => {
    const geojson = buildTraverseGeoJson(route) as {
      type: string;
      features: Array<{ geometry: { type: string }; properties: { cumulative_distance_km?: number } }>;
    };
    expect(geojson.type).toBe('FeatureCollection');
    expect(geojson.features[0].geometry.type).toBe('LineString');
    expect(geojson.features[2].properties.cumulative_distance_km).toBe(4.1);

    expect(buildTraverseCsv(route)).toContain('18.41,77.52,-2520,4.1,1.1');

    const kml = buildTraverseKml(route);
    expect(kml).toContain('77.58,18.38,-2560');
    expect(kml).toContain('77.45,18.44,-2480');
  });
});
