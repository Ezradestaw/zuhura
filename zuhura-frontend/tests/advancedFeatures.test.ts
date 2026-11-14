import { describe, it, expect, vi } from 'vitest';
import {
  fetchInteriorModel,
  fetchOptimizedRoute,
  fetchHoverInspection,
  fetchDiscoveredRegions,
} from '../src/lib/advancedApiClient';

describe('Advanced Planetary Features API Client', () => {
  it('fetches Mars interior geophysical model', async () => {
    const mockModel = {
      planetary_radius_km: 3389.5,
      planetary_mass_kg: 6.4171e23,
      surface_gravity_m_s2: 3.72,
      seismic_station: 'InSight SEIS',
      layers: [
        {
          id: 'upper_crust',
          name: 'Upper Fractured Crust',
          classification: 'crust',
          depth_top_km: 0.0,
          depth_bottom_km: 10.0,
          thickness_km: 10.0,
          thickness_uncertainty_km: 2.0,
          radius_top_km: 3389.5,
          radius_bottom_km: 3379.5,
          state_of_matter: 'Solid',
          primary_composition: 'Basaltic impact regolith',
          density_kg_m3: 2550.0,
          density_range_kg_m3: [2300, 2700],
          temperature_k: 220.0,
          temperature_range_k: [200, 250],
          evidence_type: 'Measured',
          scientific_significance: 'Regolith fracturing',
          source_citation: 'Knapmeyer-Endrun et al. (2021)',
          doi: '10.1126/science.abf8966',
          model_notes: 'Receiver functions',
        },
      ],
      crustal_dichotomy_notes: 'Hemispheric dichotomy',
      core_composition_notes: 'High sulfur fraction',
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockModel,
    } as any);

    const result = await fetchInteriorModel();
    expect(result.planetary_radius_km).toBe(3389.5);
    expect(result.layers.length).toBe(1);
    expect(result.layers[0].id).toBe('upper_crust');
  });

  it('fetches optimized traverse route', async () => {
    const mockRoute = {
      status: 'success',
      recommended_route: {
        route_id: 'rec_1',
        name: 'Recommended Route',
        total_distance_km: 12.5,
        direct_distance_km: 11.2,
        detour_factor: 1.12,
        elevation_gain_m: 85.0,
        elevation_loss_m: 120.0,
        min_elevation_m: -2600.0,
        max_elevation_m: -2500.0,
        max_slope_degrees: 14.2,
        mean_slope_degrees: 4.8,
        hazard_segments_count: 0,
        waypoints: [],
        segments: [],
        geojson: { type: 'FeatureCollection', features: [] },
      },
      alternative_routes: [],
      mobility_profile: 'rover_perseverance',
      cost_model_parameters: {},
      scientific_provenance: {},
      disclaimer: 'Research simulation only',
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockRoute,
    } as any);

    const result = await fetchOptimizedRoute(18.38, 77.58, 18.44, 77.45);
    expect(result.status).toBe('success');
    expect(result.recommended_route.total_distance_km).toBe(12.5);
    expect(result.recommended_route.max_slope_degrees).toBe(14.2);
  });

  it('fetches hover intelligence contextual telemetry', async () => {
    const mockHover = {
      latitude: 18.38,
      longitude: 77.58,
      planetographic_latitude: 18.62,
      elevation_m: -2530.0,
      vertical_datum: 'Mars Areoid (MOLA GMM-3)',
      slope_degrees: 3.5,
      surface_description: 'Jezero paleolake basin',
      geological_era: 'Late Noachian',
      nearest_feature: {
        name: 'Jezero Crater',
        feature_type: 'crater',
        distance_km: 0.0,
        diameter_km: 49.0,
        is_inside: true,
        elevation_m: -2530.0,
        description: 'Paleolake basin',
      },
      imagery_coverage: {
        viking_global_232m: true,
        ctx_regional_5m: true,
        hirise_local_submeter: true,
        themis_ir_100m: true,
        details: 'Sub-meter HiRISE available',
      },
      solar_status: {
        is_daylight: true,
        solar_elevation_deg: 52.0,
        solar_azimuth_deg: 180.0,
      },
      data_source: 'MOLA MEGDR',
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockHover,
    } as any);

    const result = await fetchHoverInspection(18.38, 77.58);
    expect(result.elevation_m).toBe(-2530.0);
    expect(result.nearest_feature?.name).toBe('Jezero Crater');
    expect(result.imagery_coverage.hirise_local_submeter).toBe(true);
  });

  it('fetches candidate discovered geological regions', async () => {
    const mockRegions = {
      status: 'success',
      total_regions_discovered: 2,
      regions: [
        {
          region_id: 'r1',
          name: 'Provisional Deltaic Unit 18N',
          naming_status: 'PROVISIONAL_PLATFORM_GENERATED',
          terrain_classification: 'Sedimentary Delta Fan',
          center_latitude: 18.42,
          center_longitude: 77.48,
          surface_area_km2: 240.5,
          mean_elevation_m: -2520.0,
          elevation_relief_m: 140.0,
          mean_slope_degrees: 3.2,
          roughness_index_tri: 2.4,
          boundary_polygon: [
            { latitude: 18.4, longitude: 77.4 },
            { latitude: 18.5, longitude: 77.4 },
            { latitude: 18.5, longitude: 77.5 },
            { latitude: 18.4, longitude: 77.4 },
          ],
          confidence_score: 0.88,
          geological_interpretation: 'Delta fan',
          nearby_official_features: ['Jezero Crater'],
          naming_rationale: 'Topographic clustering',
        },
      ],
      geojson: { type: 'FeatureCollection', features: [] },
      search_parameters: {},
      provenance: {},
      disclaimer: 'Provisional only',
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockRegions,
    } as any);

    const result = await fetchDiscoveredRegions(18.38, 77.58, 50.0);
    expect(result.total_regions_discovered).toBe(2);
    expect(result.regions[0].naming_status).toBe('PROVISIONAL_PLATFORM_GENERATED');
    expect(result.regions[0].surface_area_km2).toBe(240.5);
  });

  it('dynamically changes place description as mouse moves across Martian locations', async () => {
    const { getHoverPlaceDescription } = await import('../src/lib/hoverData');

    // 1. Hover over Jezero Crater (Delta area)
    const jezero = getHoverPlaceDescription(18.38, 77.58);
    expect(jezero.name).toContain('Jezero');
    expect(jezero.description).toBeTruthy();
    expect(jezero.description).toContain('delta');

    // 2. Move mouse to Olympus Mons
    const olympus = getHoverPlaceDescription(18.65, -133.8);
    expect(olympus.name).toContain('Olympus Mons');
    expect(olympus.description).toBeTruthy();
    expect(olympus.description).toContain('volcano');

    // 3. Move mouse to Valles Marineris (Candor Chasma)
    const candor = getHoverPlaceDescription(-6.5, -75.5);
    expect(candor.description).toBeTruthy();
    expect(candor.name).not.toBe(jezero.name);

    // 4. Move mouse to North Pole
    const northPole = getHoverPlaceDescription(82.0, 10.0);
    expect(northPole.name).toContain('Planum Boreum');
    expect(northPole.description).toContain('water ice');

    // Confirm descriptions are dynamically distinct
    expect(jezero.description).not.toEqual(olympus.description);
    expect(olympus.description).not.toEqual(northPole.description);
  });

  it('generates client geodesic route between departure and arrival pins', async () => {
    const { generateClientGeodesicRoute, marsDistanceKm } = await import('../src/lib/routeFallback');

    const dep = { lat: 18.38, lon: 77.58, name: 'Jezero Crater', elevation_m: -2530 };
    const arr = { lat: -4.59, lon: 137.44, name: 'Gale Crater', elevation_m: -4500 };

    const distance = marsDistanceKm(dep.lat, dep.lon, arr.lat, arr.lon);
    expect(distance).toBeGreaterThan(1000);

    const route = generateClientGeodesicRoute(dep, arr, 'rover_perseverance', 20);
    expect(route.status).toBe('fallback_synthetic_simulation');
    expect(route.is_synthetic).toBe(true);
    expect(route.scientific_provenance.source).toBe('DEMO_SYNTHETIC');
    expect(route.disclaimer).toContain('Simulated Heuristic - Not Calibrated Planetary Data');
    expect(route.recommended_route.waypoints.length).toBe(21);
    expect(route.recommended_route.waypoints.every((point) => point.roughness_tri === 0)).toBe(true);
    expect(route.recommended_route.total_distance_km).toBeCloseTo(distance, 0);
    expect(route.recommended_route.geojson.geometry?.coordinates?.length).toBe(21);
  });
});
