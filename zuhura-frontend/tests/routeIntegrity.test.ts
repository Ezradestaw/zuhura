import { describe, it, expect, vi, afterEach } from 'vitest';
import {
  generateClientGeodesicRoute,
  marsDistanceKm,
  terrainProfileToRoute,
  resolveRouteWithElevation,
  SYNTHETIC_ROUTE_WARNING,
} from '../src/lib/routeFallback';
import { buildTraverseCsv, buildTraverseGeoJson, buildTraverseKml } from '../src/lib/routeExport';
import { TerrainProfileResult } from '../src/lib/terrainApiClient';

const profileFixture: TerrainProfileResult = {
  transect_summary: {
    total_distance_km: 8.2,
    num_samples: 3,
    sample_step_m: 4100,
    min_elevation_m: -2560,
    max_elevation_m: -2480,
    mean_elevation_m: -2520,
    elevation_relief_m: 80,
    cumulative_elevation_gain_m: 80,
    cumulative_elevation_loss_m: 0,
    mean_slope_deg: 1.1,
    max_slope_deg: 2.2,
  },
  samples: [
    { step: 0, distance_km: 0, latitude: 18.38, longitude: 77.58, elevation_m: -2560, segment_slope_deg: 0 },
    { step: 1, distance_km: 4.1, latitude: 18.41, longitude: 77.52, elevation_m: -2520, segment_slope_deg: 1.1 },
    { step: 2, distance_km: 8.2, latitude: 18.44, longitude: 77.45, elevation_m: -2480, segment_slope_deg: 2.2 },
  ],
  provenance: {
    source_dataset: 'zuhura-mola-global-v3-cog',
    vertical_datum: 'Mars Areoid (MOLA GMM-3)',
    geodetic_reference: 'IAU/IAG 2015 Mars Biaxial Ellipsoid',
    nominal_resolution_m: 463.0577,
    interpolation_method: 'bilinear sub-pixel sampling',
    query_timestamp: '2026-11-14T00:00:00Z',
    validation_status: 'scientifically_validated',
  },
};

describe('Scientific route integrity', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it('labels the offline geodesic as synthetic and keeps it deterministic', () => {
    const start = { lat: 18.38, lon: 77.58, elevation_m: -2530 };
    const end = { lat: 18.44, lon: 77.45, elevation_m: -2480 };
    const first = generateClientGeodesicRoute(start, end, 'rover_perseverance', 10);
    const second = generateClientGeodesicRoute(start, end, 'rover_perseverance', 10);

    expect(first.status).toBe('fallback_synthetic_simulation');
    expect(first.is_synthetic).toBe(true);
    expect(first.disclaimer).toBe(SYNTHETIC_ROUTE_WARNING);
    expect(first.scientific_provenance.source).toBe('DEMO_SYNTHETIC');
    expect(JSON.stringify(first.scientific_provenance)).not.toContain('MOLA Geodesic Solver');
    expect(first.recommended_route.waypoints.map((point) => point.elevation_m)).toEqual(
      second.recommended_route.waypoints.map((point) => point.elevation_m),
    );
    expect(first.recommended_route.waypoints[0].elevation_m).toBe(-2530);
    expect(first.recommended_route.waypoints.at(-1)?.elevation_m).toBe(-2480);
    expect(first.recommended_route.total_distance_km).toBeCloseTo(
      marsDistanceKm(start.lat, start.lon, end.lat, end.lon),
      0,
    );
  });

  it('maps a GDAL transect without inventing MOLA roughness', () => {
    const route = terrainProfileToRoute(profileFixture, 'rover_perseverance');
    expect(route.status).toBe('mola_transect_sampled');
    expect(route.is_synthetic).toBe(false);
    expect(route.scientific_provenance.source_dataset).toBe('zuhura-mola-global-v3-cog');
    expect(route.recommended_route.waypoints.map((point) => point.elevation_m)).toEqual([-2560, -2520, -2480]);
    expect(route.recommended_route.waypoints.every((point) => point.roughness_tri === 0)).toBe(true);
    expect(route.recommended_route.max_slope_degrees).toBe(2.2);
  });

  it('uses the terrain profile endpoint before the synthetic geodesic', async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => profileFixture,
    }));
    vi.stubGlobal('fetch', fetchMock);

    const route = await resolveRouteWithElevation(
      { lat: 18.38, lon: 77.58 },
      { lat: 18.44, lon: 77.45 },
      'rover_perseverance',
      20,
    );

    const calls = fetchMock.mock.calls as unknown as Array<[string]>;
    expect(String(calls[0][0])).toContain('/api/v1/spatial/terrain/profile');
    expect(route.status).toBe('mola_transect_sampled');
    expect(route.recommended_route.waypoints[1].elevation_m).toBe(-2520);
  });

  it('exports GeoJSON, CSV, and KML with distance and slope', () => {
    const route = terrainProfileToRoute(profileFixture, 'rover_perseverance').recommended_route;
    const geojson = buildTraverseGeoJson(route) as {
      type: string;
      features: Array<{ geometry: { type: string }; properties: { cumulative_distance_km?: number; slope_degrees?: number } }>;
    };
    expect(geojson.type).toBe('FeatureCollection');
    expect(geojson.features[0].geometry.type).toBe('LineString');
    expect(geojson.features[2].properties.cumulative_distance_km).toBe(4.1);
    expect(geojson.features[2].properties.slope_degrees).toBe(1.1);

    const csv = buildTraverseCsv(route);
    expect(csv.split('\n')[0]).toContain('cumulative_distance_km');
    expect(csv).toContain('18.41,77.52,-2520,4.1,1.1');

    const kml = buildTraverseKml(route);
    expect(kml).toContain('<kml xmlns="http://www.opengis.net/kml/2.2">');
    expect(kml).toContain('77.58,18.38,-2560');
    expect(kml).toContain('77.45,18.44,-2480');
  });
});
