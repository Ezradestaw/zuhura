import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  fetchEnvironmentOverview,
  fetchEnvironmentPresets,
  fetchAtmosphericProfile,
  fetchDustOpticalDepth,
  fetchDiurnalTemperature,
  fetchSolarPowerBudget,
  fetchMissionEnvironmentAssessment,
} from '../src/lib/advancedApiClient';
import { useEnvironmentStore } from '../src/store/environmentStore';

describe('Environment API client', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('fetches Mars orbital overview and seasonal datum pressure', async () => {
    const mockOverview = {
      status: 'success',
      orbital: {
        solar_longitude_deg: 180.0,
        heliocentric_distance_au: 1.55,
        top_of_atmosphere_solar_flux_w_m2: 566.0,
        solar_declination_deg: 0.0,
        season_northern: 'Autumn (Approaching Perihelion)',
        season_southern: 'Spring (Approaching Perihelion)',
        dust_season_risk: 'HIGH (Southern Spring Perihelion Dust Storm Season)',
      },
      mean_datum_pressure_pa: 760.5,
      mean_datum_pressure_mbar: 7.605,
      water_triple_point_pa: 611.65,
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockOverview,
    } as any);

    const res = await fetchEnvironmentOverview(180.0);
    expect(res.status).toBe('success');
    expect(res.orbital.solar_longitude_deg).toBe(180.0);
    expect(res.mean_datum_pressure_pa).toBeGreaterThan(600.0);
    expect(res.water_triple_point_pa).toBe(611.65);
  });

  it('fetches environmental benchmark site presets', async () => {
    const mockPresets = {
      status: 'success',
      count: 3,
      presets: [
        {
          id: 'jezero_crater',
          name: 'Jezero Crater (Perseverance Touchdown)',
          latitude: 18.38,
          longitude: 77.58,
          elevation_m: -2500.0,
          thermal_inertia_tiu: 360.0,
          geological_context: 'Lacustrine delta deposit in ancient impact basin.',
        },
        {
          id: 'olympus_mons_caldera',
          name: 'Olympus Mons Summit Caldera',
          latitude: 18.65,
          longitude: 226.20,
          elevation_m: 21229.0,
          thermal_inertia_tiu: 110.0,
          geological_context: 'Highest volcanic summit in the solar system.',
        },
      ],
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockPresets,
    } as any);

    const res = await fetchEnvironmentPresets();
    expect(res.status).toBe('success');
    expect(res.presets.length).toBeGreaterThanOrEqual(2);
    expect(res.presets[0].id).toBe('jezero_crater');
  });

  it('computes vertical atmospheric profile and checks water triple point', async () => {
    const mockProfile = {
      status: 'success',
      profile: {
        latitude: -42.70,
        longitude: 70.00,
        surface_elevation_m: -7152.0,
        solar_longitude_deg: 180.0,
        surface_pressure_pa: 1390.2,
        surface_pressure_mbar: 13.902,
        surface_density_kg_m3: 0.033,
        scale_height_km: 11.1,
        adiabatic_lapse_rate_k_km: -1.8,
        above_water_triple_point: true,
        gas_composition_molar_pct: {
          'Carbon Dioxide (CO2)': 95.32,
          'Nitrogen (N2)': 2.60,
        },
        layers: [
          {
            altitude_above_surface_km: 0.0,
            elevation_above_areoid_m: -7152.0,
            pressure_pa: 1390.2,
            pressure_mbar: 13.902,
            density_kg_m3: 0.033,
            temperature_k: 220.0,
            temperature_c: -53.15,
            speed_of_sound_m_s: 233.0,
            earth_equivalent_altitude_km: 31.5,
          },
        ],
      },
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockProfile,
    } as any);

    const res = await fetchAtmosphericProfile({
      latitude: -42.70,
      longitude: 70.00,
      elevation_m: -7152.0,
      ls_deg: 180.0,
    });

    expect(res.status).toBe('success');
    expect(res.profile.surface_pressure_pa).toBeGreaterThan(1000.0);
    expect(res.profile.above_water_triple_point).toBe(true);
    expect(res.profile.layers.length).toBe(1);
  });

  it('computes visible dust optical depth and operational recommendations', async () => {
    const mockDust = {
      status: 'success',
      result: {
        latitude: 18.38,
        longitude: 77.58,
        elevation_m: -2500.0,
        solar_longitude_deg: 260.0,
        tau_visible: 1.45,
        opacity_category: 'REGIONAL_STORM',
        dust_storm_risk_index: 0.67,
        direct_transmission_zenith: 0.235,
        diffuse_scattering_fraction: 0.22,
        is_basin_amplified: false,
        operational_recommendations: [
          'WARNING: Regional dust storm activity detected.',
          'Suspend long-distance mobility traverses.',
        ],
      },
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockDust,
    } as any);

    const res = await fetchDustOpticalDepth({
      latitude: 18.38,
      longitude: 77.58,
      elevation_m: -2500.0,
      ls_deg: 260.0,
    });

    expect(res.status).toBe('success');
    expect(res.result.tau_visible).toBe(1.45);
    expect(res.result.opacity_category).toBe('REGIONAL_STORM');
    expect(res.result.operational_recommendations.length).toBeGreaterThanOrEqual(1);
  });

  it('computes diurnal temperature cycle and regolith classification', async () => {
    const mockThermal = {
      status: 'success',
      profile: {
        latitude: 18.38,
        elevation_m: -2500.0,
        solar_longitude_deg: 180.0,
        thermal_inertia_tiu: 360.0,
        albedo: 0.22,
        min_surface_temp_k: 185.0,
        max_surface_temp_k: 255.0,
        diurnal_temperature_swing_k: 70.0,
        mean_surface_temp_k: 220.0,
        regolith_type: 'Indurated Duricrust & Pebble Pavement',
        co2_frost_present: false,
        hourly_curve: [
          {
            local_solar_time_hours: 12.0,
            solar_zenith_angle_deg: 18.4,
            solar_irradiance_w_m2: 520.0,
            surface_temperature_k: 255.0,
            surface_temperature_c: -18.15,
            air_temperature_2m_k: 235.0,
            air_temperature_2m_c: -38.15,
            co2_frost_risk: false,
          },
        ],
      },
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockThermal,
    } as any);

    const res = await fetchDiurnalTemperature({
      latitude: 18.38,
      elevation_m: -2500.0,
      ls_deg: 180.0,
      thermal_inertia_tiu: 360.0,
    });

    expect(res.status).toBe('success');
    expect(res.profile.diurnal_temperature_swing_k).toBe(70.0);
    expect(res.profile.regolith_type).toContain('Duricrust');
  });

  it('computes solar power budget and rover feasibility status', async () => {
    const mockBudget = {
      status: 'success',
      budget: {
        latitude: 18.38,
        solar_longitude_deg: 180.0,
        tau_visible: 0.40,
        panel_area_m2: 1.3,
        cell_efficiency: 0.295,
        dust_deposition_factor: 0.85,
        peak_power_w: 145.2,
        daily_energy_wh_sol: 850.5,
        average_daytime_power_w: 70.0,
        operational_status: 'SURPLUS_FULL_OPERATION',
        rover_compatibility: {
          mer_opportunity_spirit: {
            installed_area_m2: 1.3,
            current_status: 'FEASIBLE',
          },
        },
        hourly_power_w: [0, 0, 0, 0, 0, 0, 20, 60, 110, 140, 145, 140, 110, 60, 20, 0, 0, 0, 0, 0, 0, 0, 0, 0],
      },
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockBudget,
    } as any);

    const res = await fetchSolarPowerBudget({
      latitude: 18.38,
      ls_deg: 180.0,
      panel_area_m2: 1.3,
    });

    expect(res.status).toBe('success');
    expect(res.budget.daily_energy_wh_sol).toBeGreaterThan(800.0);
    expect(res.budget.operational_status).toBe('SURPLUS_FULL_OPERATION');
  });

  it('runs composite mission environment assessment', async () => {
    const mockAssessment = {
      status: 'success',
      assessment: {
        target_name: 'Jezero Crater Science Zone',
        latitude: 18.38,
        longitude: 77.58,
        elevation_m: -2500.0,
        solar_longitude_deg: 180.0,
        orbital: {
          solar_longitude_deg: 180.0,
          heliocentric_distance_au: 1.55,
          top_of_atmosphere_solar_flux_w_m2: 566.0,
          solar_declination_deg: 0.0,
          season_northern: 'Autumn',
          season_southern: 'Spring',
          dust_season_risk: 'HIGH',
        },
        atmosphere: {
          surface_pressure_pa: 855.0,
          above_water_triple_point: true,
        },
        dust: {
          tau_visible: 0.38,
          opacity_category: 'CLEAR',
        },
        thermal: {
          diurnal_temperature_swing_k: 65.0,
        },
        power_budget: {
          daily_energy_wh_sol: 890.0,
        },
        overall_site_viability_score: 91.5,
        environmental_hazards: [],
      },
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockAssessment,
    } as any);

    const res = await fetchMissionEnvironmentAssessment({
      target_name: 'Jezero Crater Science Zone',
      latitude: 18.38,
      longitude: 77.58,
      elevation_m: -2500.0,
      ls_deg: 180.0,
    });

    expect(res.status).toBe('success');
    expect(res.assessment.target_name).toBe('Jezero Crater Science Zone');
    expect(res.assessment.overall_site_viability_score).toBe(91.5);
  });

  it('manages environmental state in useEnvironmentStore', () => {
    const store = useEnvironmentStore.getState();

    // Toggle modal
    store.setIsEnvironmentModalOpen(true);
    expect(useEnvironmentStore.getState().isEnvironmentModalOpen).toBe(true);

    // Set solar longitude
    store.setSelectedLs(251.0);
    expect(useEnvironmentStore.getState().selectedLs).toBe(251.0);

    // Set panel area
    store.setPanelArea(7.0);
    expect(useEnvironmentStore.getState().panelArea).toBe(7.0);

    // Set thermal inertia
    store.setThermalInertia(600.0);
    expect(useEnvironmentStore.getState().thermalInertia).toBe(600.0);

    // Set active tab
    store.setActiveTab('dust');
    expect(useEnvironmentStore.getState().activeTab).toBe('dust');
  });
});
