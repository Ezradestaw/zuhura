import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  fetchDetectedFeatures,
  fetchCraterMorphology,
  fetchMultiSpectralAnalysis,
  fetchChangeDetection,
  fetchImageRegistration,
  fetchSuperResolution,
} from '../src/lib/advancedApiClient';

describe('Visual intelligence API client', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('fetches detected geological features near target coordinates', async () => {
    const mockFeatures = [
      {
        feature_id: 'jezero_main_crater',
        feature_type: 'impact_crater',
        name: 'Jezero Crater Basin',
        bounding_box: {
          min_latitude: 17.98,
          max_latitude: 18.78,
          min_longitude: 77.18,
          max_longitude: 77.98,
          center_latitude: 18.38,
          center_longitude: 77.58,
          width_m: 47500.0,
          height_m: 47500.0,
        },
        confidence_score: 0.97,
        epistemic_classification: 'OBSERVED',
        detection_method: 'Circular Hough Transform & MOLA Topographic Rim Extraction',
        morphological_metrics: { diameter_km: 47.5, apparent_depth_m: 1050.0 },
        scientific_significance: 'Noachian-Hesperian paleolake basin',
      },
      {
        feature_id: 'kodiak_butte_remnant',
        feature_type: 'layered_sediments',
        name: 'Kodiak Butte Delta Front',
        bounding_box: {
          min_latitude: 18.41,
          max_latitude: 18.43,
          min_longitude: 77.47,
          max_longitude: 77.49,
          center_latitude: 18.42,
          center_longitude: 77.48,
          width_m: 850.0,
          height_m: 250.0,
        },
        confidence_score: 0.96,
        epistemic_classification: 'OBSERVED',
        detection_method: 'Multi-Scale Stratigraphic Layering Analysis',
        morphological_metrics: { layer_thickness_cm: 15.0 },
        scientific_significance: 'Erosional mesa proving standing water in Jezero',
      },
    ];

    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => mockFeatures,
    } as any);

    const features = await fetchDetectedFeatures(18.38, 77.58, 50.0);
    expect(features).toHaveLength(2);
    expect(features[0].feature_type).toBe('impact_crater');
    expect(features[0].confidence_score).toBeGreaterThan(0.90);
    expect(features[1].feature_type).toBe('layered_sediments');
  });

  it('fetches analytical crater morphometry profile based on Pike formulations', async () => {
    const mockCrater = {
      crater_id: 'crater_1838_7758_47km',
      name: 'Jezero Crater Basin',
      center_latitude: 18.38,
      center_longitude: 77.58,
      diameter_km: 47.5,
      apparent_depth_m: 1050.0,
      rim_height_m: 220.0,
      depth_to_diameter_ratio: 0.0221,
      crater_class: 'COMPLEX',
      degradation_state: 'MODERATELY_DEGRADED',
      ejecta_blanket_type: 'SINGLE_LAYER_LOBATE',
      central_peak_present: true,
      estimated_age_gyr: 3.82,
      scientific_notes: 'Classified as COMPLEX crater with single layer lobate ejecta.',
    };

    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => mockCrater,
    } as any);

    const result = await fetchCraterMorphology(18.38, 77.58, 47.5);
    expect(result.crater_class).toBe('COMPLEX');
    expect(result.central_peak_present).toBe(true);
    expect(result.depth_to_diameter_ratio).toBeCloseTo(0.0221, 3);
  });

  it('fetches CRISM multi-spectral band ratios and THEMIS thermal inertia', async () => {
    const mockSpectral = {
      latitude: 18.42,
      longitude: 77.48,
      target_name: 'Jezero Delta Front',
      spectral_indices: {
        iron_oxide_index: 1.45,
        phyllosilicate_clay_index: 0.085,
        olivine_mafic_index: 0.040,
        hydrated_mineral_index: 0.065,
        dominant_mineralogy: 'PHYLLOSILICATE_SMECTITE_CLAYS',
        mineral_description: 'Fe/Mg-smectite clays and magnesium carbonates',
      },
      thermal_inertia: {
        daytime_ir_temp_k: 260.0,
        nighttime_ir_temp_k: 190.0,
        diurnal_temperature_amplitude_k: 70.0,
        derived_thermal_inertia_tiu: 320.0,
        estimated_grain_size_um: 580.0,
        grain_size_classification: 'MEDIUM_COARSE_SAND',
        bearing_capacity_rating: 'GOOD (Firm bearing)',
      },
      false_color_rgb: {
        hex: '#61d833',
        channels: { red_fe_oxide: 97, green_clay: 216, blue_olivine: 51 },
        mapping_scheme: 'CRISM R:Fe3+ G:Clay B:Olivine',
      },
      instrument_sources: ['MRO CRISM', '2001 Mars Odyssey THEMIS'],
      scientific_provenance: { classification: 'DERIVED' },
    };

    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => mockSpectral,
    } as any);

    const result = await fetchMultiSpectralAnalysis(18.42, 77.48);
    expect(result.spectral_indices.dominant_mineralogy).toBe('PHYLLOSILICATE_SMECTITE_CLAYS');
    expect(result.thermal_inertia.derived_thermal_inertia_tiu).toBe(320.0);
    expect(result.false_color_rgb.hex).toBe('#61d833');
  });

  it('fetches multi-temporal surface change detection events', async () => {
    const mockChanges = {
      target_region: 'Active Dynamic Mars Surface Surveillance Corridor',
      epoch_1_date: '2021-01-01',
      epoch_2_date: '2024-01-01',
      total_changes_detected: 2,
      changes: [
        {
          change_id: 'change_01',
          change_type: 'NEW_IMPACT_CRATER',
          location_latitude: 3.50,
          location_longitude: 135.20,
          bounding_box_pixels: { x: 512, y: 480, w: 150, h: 150 },
          relative_albedo_delta_pct: -65.0,
          confidence_score: 0.99,
          first_observed_epoch: '2021-12-01',
          second_observed_epoch: '2022-02-11',
          description: 'Fresh 150-meter diameter impact crater detected seismically',
        },
        {
          change_id: 'change_02',
          change_type: 'SLOPE_STREAK',
          location_latitude: 18.45,
          location_longitude: 77.42,
          bounding_box_pixels: { x: 340, y: 612, w: 45, h: 220 },
          relative_albedo_delta_pct: -28.0,
          confidence_score: 0.96,
          first_observed_epoch: '2021-03-15',
          second_observed_epoch: '2023-08-20',
          description: 'Fresh dark slope streak formed by dry granular dust avalanche',
        },
      ],
      change_density_per_km2: 0.00008,
      scientific_provenance: { classification: 'DERIVED' },
    };

    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => mockChanges,
    } as any);

    const result = await fetchChangeDetection(18.38, 77.58);
    expect(result.total_changes_detected).toBe(2);
    expect(result.changes[0].change_type).toBe('NEW_IMPACT_CRATER');
    expect(result.changes[1].relative_albedo_delta_pct).toBe(-28.0);
  });

  it('fetches sub-pixel image registration and super-resolution metrics', async () => {
    const mockRegistration = {
      reference_frame_id: 'CTX_D14_032549_1985',
      target_frame_id: 'HiRISE_ESP_04299_1985',
      matched_keypoints_count: 320,
      inlier_matches_count: 245,
      inlier_ratio: 0.7656,
      homography_matrix_3x3: [
        [1.0235, -0.0330, 12.4],
        [0.0330, 1.0235, -8.7],
        [0.0, 0.0, 1.0],
      ],
      subpixel_alignment_rmse_pixels: 0.285,
      registration_quality: 'SUBPIXEL_EXCELLENT',
      projective_scale_factor: 1.024,
      rotation_angle_degrees: 1.85,
      scientific_notes: 'Registration achieved subpixel_excellent alignment',
    };

    const mockSuperRes = {
      original_resolution_m_per_px: 6.0,
      enhanced_resolution_m_per_px: 3.0,
      enhancement_factor: 2.0,
      psnr_db: 34.2,
      ssim_score: 0.915,
      features_revealed: ['Sub-decameter crater rim crests'],
      processing_notes: 'Super-resolution synthesized 2.0x detail recovery',
    };

    global.fetch = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: async () => mockRegistration } as any)
      .mockResolvedValueOnce({ ok: true, json: async () => mockSuperRes } as any);

    const reg = await fetchImageRegistration();
    expect(reg.subpixel_alignment_rmse_pixels).toBeLessThan(0.40);
    expect(reg.registration_quality).toBe('SUBPIXEL_EXCELLENT');

    const sr = await fetchSuperResolution(6.0, 2.0);
    expect(sr.enhanced_resolution_m_per_px).toBe(3.0);
    expect(sr.psnr_db).toBeGreaterThan(30.0);
  });
});
