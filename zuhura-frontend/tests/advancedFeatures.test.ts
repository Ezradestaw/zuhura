import { describe, it, expect, vi } from 'vitest';
import {
  fetchDiscoveredRegions,
} from '../src/lib/advancedApiClient';

describe('Advanced Planetary Features API Client', () => {
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
});
