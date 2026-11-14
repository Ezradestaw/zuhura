import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fetchRegolithTypes, fetchCommWindows, fetchMultiRoverSimulation } from '../src/lib/advancedApiClient';

describe('Rover simulation API client', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('fetches Martian regolith geotechnical types with Bekker moduli', async () => {
    const mockRegolith = {
      status: 'operational',
      regolith_types: {
        basaltic_sand: {
          regolith_id: 'basaltic_sand',
          name: 'Basaltic Sand & Fine Regolith',
          description: 'Pervasive aeolian basaltic sand drifts',
          cohesion_kpa: 0.2,
          internal_friction_deg: 35.0,
          sinkage_modulus_kc: 0.5,
          sinkage_modulus_kphi: 1800.0,
          sinkage_exponent_n: 1.0,
          shear_deformation_modulus_k_cm: 1.8,
          typical_rolling_resistance: 0.08,
        },
        dune_fields: {
          regolith_id: 'dune_fields',
          name: 'Active Aeolian Dune Fields (TARs)',
          description: 'Severe wheel sinkage and entrapment hazard',
          cohesion_kpa: 0.05,
          internal_friction_deg: 26.0,
          sinkage_modulus_kc: 0.05,
          sinkage_modulus_kphi: 400.0,
          sinkage_exponent_n: 1.0,
          shear_deformation_modulus_k_cm: 3.2,
          typical_rolling_resistance: 0.14,
        },
      },
      count: 2,
    };

    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => mockRegolith,
    } as any);

    const result = await fetchRegolithTypes();
    expect(result.status).toBe('operational');
    expect(result.regolith_types.basaltic_sand.internal_friction_deg).toBe(35.0);
    expect(result.regolith_types.dune_fields.sinkage_modulus_kphi).toBe(400.0);
    expect(result.regolith_types.dune_fields.sinkage_exponent_n).toBe(1.0);
  });

  it('fetches daily communications relay and DTE passes for Martian surface asset', async () => {
    const mockPasses = [
      {
        target: 'MRO',
        pass_type: 'ORBITER_RELAY',
        start_time_lmst: '15:10',
        end_time_lmst: '15:22',
        duration_minutes: 12.0,
        max_elevation_deg: 74.5,
        data_capacity_mbit: 144.0,
        frequency_band: 'UHF (400 MHz Electra)',
      },
      {
        target: 'ODYSSEY',
        pass_type: 'ORBITER_RELAY',
        start_time_lmst: '17:05',
        end_time_lmst: '17:18',
        duration_minutes: 13.0,
        max_elevation_deg: 58.2,
        data_capacity_mbit: 36.0,
        frequency_band: 'UHF (400 MHz CE505)',
      },
      {
        target: 'DTE_MADRID',
        pass_type: 'DIRECT_TO_EARTH',
        start_time_lmst: '09:15',
        end_time_lmst: '10:30',
        duration_minutes: 75.0,
        max_elevation_deg: 42.0,
        data_capacity_mbit: 8.5,
        frequency_band: 'X-Band (7.1 GHz HGA)',
      },
    ];

    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => mockPasses,
    } as any);

    const passes = await fetchCommWindows(18.38, 77.58);
    expect(passes).toHaveLength(3);
    expect(passes[0].target).toBe('MRO');
    expect(passes[0].duration_minutes).toBe(12.0);
    expect(passes[2].pass_type).toBe('DIRECT_TO_EARTH');
  });

  it('executes multi-rover simulation comparing performance and risk profiles', async () => {
    const mockComparison = {
      status: 'success',
      corridor_summary: {
        distance_km: 2.45,
        direct_distance_km: 2.1,
        elevation_gain_m: 38.5,
        elevation_loss_m: 12.0,
        max_slope_degrees: 14.2,
        mean_slope_degrees: 5.6,
        mean_roughness_tri: 1.35,
        hazard_segments_count: 0,
      },
      regolith_properties: {
        regolith_id: 'basaltic_sand',
        name: 'Basaltic Sand',
        cohesion_kpa: 0.2,
        internal_friction_deg: 35.0,
      },
      environmental_conditions: {
        solar_longitude_ls: 180.0,
        dust_optical_depth_tau: 0.5,
        soil_type: 'basaltic_sand',
      },
      comparison_results: [
        {
          rover_id: 'rover_perseverance',
          name: 'Mars 2020 Perseverance Rover',
          power_source: 'mmrtg',
          mass_kg: 1025.0,
          total_sols_required: 6.0,
          total_energy_wh: 1240.5,
          energy_rate_wh_per_km: 506.3,
          max_wheel_slip_pct: 12.4,
          mean_sinkage_cm: 2.4,
          tipping_risk: 47.3,
          sinkage_risk: 18.5,
          high_centering_risk: 22.0,
          thermal_risk: 5.0,
          composite_risk: 23.5,
          risk_rating: 'BENIGN',
          feasibility: {
            geometric_feasible: true,
            engineering_feasible: true,
            energy_feasible: true,
            mission_feasible: true,
          },
          recommendation: 'RECOMMENDED',
        },
        {
          rover_id: 'scout_hexacopter',
          name: 'Autonomous Aerial Scout',
          power_source: 'battery',
          mass_kg: 2.4,
          total_sols_required: 1.0,
          total_energy_wh: 42.0,
          energy_rate_wh_per_km: 17.1,
          max_wheel_slip_pct: 0.0,
          mean_sinkage_cm: 0.0,
          tipping_risk: 18.9,
          sinkage_risk: 0.0,
          high_centering_risk: 0.0,
          thermal_risk: 15.0,
          composite_risk: 12.1,
          risk_rating: 'BENIGN',
          feasibility: {
            geometric_feasible: true,
            engineering_feasible: true,
            energy_feasible: true,
            mission_feasible: true,
          },
          recommendation: 'RECOMMENDED',
        },
      ],
      scientific_provenance: {
        classification: 'SIMULATED',
        dataset_name: 'Multi-Rover Terramechanics & Mission Simulator',
      },
    };

    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => mockComparison,
    } as any);

    const result = await fetchMultiRoverSimulation(
      18.38,
      77.58,
      18.44,
      77.45,
      ['rover_perseverance', 'scout_hexacopter'],
      'basaltic_sand',
      180.0,
      0.5,
    );

    expect(result.status).toBe('success');
    expect(result.comparison_results).toHaveLength(2);

    const persev = result.comparison_results[0];
    const scout = result.comparison_results[1];

    expect(persev.total_sols_required).toBeGreaterThan(scout.total_sols_required);
    expect(scout.max_wheel_slip_pct).toBe(0.0);
    expect(result.scientific_provenance.classification).toBe('SIMULATED');
  });
});
