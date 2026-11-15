/**
 * Zuhura Frontend - Advanced Planetary Features API Client
 * Connects UI components to X-Ray Mars, Optimize Navigation, Hover Intelligence,
 * Location Pinpoint, and Mars Region Discovery endpoints.
 */

export interface GeoJsonObject {
  type: string;
  geometry?: {
    type: string;
    coordinates: number[][];
  };
  properties?: Record<string, string | number | boolean | null>;
  coordinates?: number[][];
  features?: GeoJsonObject[];
}

export interface ScientificProvenance {
  source?: string;
  source_dataset?: string;
  original_dataset_id?: string;
  processing_algorithm?: string;
  coordinate_reference_system?: string;
  vertical_datum?: string;
  geodetic_reference?: string;
  nominal_resolution_m?: number;
  interpolation_method?: string;
  query_timestamp?: string;
  validation_status?: string;
  disclaimer?: string;
  is_synthetic?: boolean;
  classification?: string;
  warning?: string;
  elevation_method?: string;
  roughness?: string;
  note?: string;
}

export interface ScalarRecord {
  [key: string]: string | number | boolean | null;
}

export interface RoverPowerStatus {
  installed_area_m2: number;
  survival_threshold_wh_sol: number;
  nominal_mobility_wh_sol?: number;
  nominal_science_wh_sol?: number;
  current_status: string;
}

export interface KmlWaypoint {
  latitude: number;
  longitude: number;
  elevation_m?: number;
}

export interface RegolithPropertiesData {
  regolith_id: string;
  name: string;
  description: string;
  cohesion_kpa: number;
  internal_friction_deg: number;
  sinkage_modulus_kc: number;
  sinkage_modulus_kphi: number;
  sinkage_exponent_n: number;
  shear_deformation_modulus_k_cm: number;
  typical_rolling_resistance: number;
}

export interface CommunicationPassData {
  target: string;
  pass_type: string;
  start_time_lmst: string;
  end_time_lmst: string;
  duration_minutes: number;
  max_elevation_deg: number;
  data_capacity_mbit: number;
  frequency_band: string;
}

export interface SolTimelineEventData {
  time_window_lmst: string;
  phase_name: string;
  description: string;
  power_draw_w: number;
  is_comm_active: boolean;
}

export interface DailySolScheduleData {
  sol_number: number;
  drive_distance_m: number;
  drive_duration_hours: number;
  daily_energy_consumed_wh: number;
  daily_solar_generated_wh: number;
  net_battery_state_wh: number;
  communication_passes: CommunicationPassData[];
  events: SolTimelineEventData[];
}

export interface TraverseRiskAnalysisData {
  tipping_risk: number;
  high_centering_risk: number;
  sinkage_entrapment_risk: number;
  thermal_deficit_risk: number;
  comm_blackout_risk: number;
  composite_risk: number;
  risk_rating: 'BENIGN' | 'ELEVATED' | 'HAZARDOUS' | 'PROHIBITIVE' | string;
}

export interface RouteFeasibilityReportData {
  geometric_feasible: boolean;
  engineering_feasible: boolean;
  energy_feasible: boolean;
  mission_feasible: boolean;
  limiting_factor?: string | null;
}

export interface RoverComparisonItemData {
  rover_id: string;
  name: string;
  power_source: string;
  mass_kg: number;
  total_sols_required: number;
  total_energy_wh: number;
  energy_rate_wh_per_km: number;
  max_wheel_slip_pct: number;
  mean_sinkage_cm: number;
  tipping_risk: number;
  sinkage_risk: number;
  high_centering_risk: number;
  thermal_risk: number;
  composite_risk: number;
  risk_rating: string;
  feasibility: RouteFeasibilityReportData;
  recommendation: 'RECOMMENDED' | 'VIABLE_WITH_CAUTION' | 'HIGH_RISK' | 'UNFEASIBLE' | string;
}

export interface MultiRoverSimulationResponseData {
  status: string;
  corridor_summary: {
    distance_km: number;
    direct_distance_km: number;
    elevation_gain_m: number;
    elevation_loss_m: number;
    max_slope_degrees: number;
    mean_slope_degrees: number;
    mean_roughness_tri: number;
    hazard_segments_count: number;
  };
  regolith_properties: RegolithPropertiesData;
  environmental_conditions: {
    solar_longitude_ls: number;
    dust_optical_depth_tau: number;
    soil_type: string;
  };
  comparison_results: RoverComparisonItemData[];
  scientific_provenance: ScientificProvenance;
}

export interface FeatureBoundingBoxData {
  min_latitude: number;
  max_latitude: number;
  min_longitude: number;
  max_longitude: number;
  center_latitude: number;
  center_longitude: number;
  width_m: number;
  height_m: number;
}

export interface DetectedPlanetaryFeatureData {
  feature_id: string;
  feature_type:
    | 'impact_crater'
    | 'aeolian_dunes_ripples'
    | 'dust_devil_tracks'
    | 'gullies'
    | 'recurring_slope_lineae'
    | 'layered_sediments'
    | string;
  name?: string;
  bounding_box: FeatureBoundingBoxData;
  confidence_score: number;
  epistemic_classification: string;
  detection_method: string;
  morphological_metrics: ScalarRecord;
  scientific_significance: string;
}

export interface CraterMorphologyProfileData {
  crater_id: string;
  name?: string;
  center_latitude: number;
  center_longitude: number;
  diameter_km: number;
  apparent_depth_m: number;
  rim_height_m: number;
  depth_to_diameter_ratio: number;
  crater_class: 'SIMPLE' | 'COMPLEX' | 'TRANSITIONAL' | 'MULTI_RING_BASIN' | string;
  degradation_state: 'PRISTINE_FRESH' | 'MODERATELY_DEGRADED' | 'HIGHLY_DEGRADED_SUBDUED' | 'GHOST_INFILLED' | string;
  ejecta_blanket_type:
    | 'CONTINUOUS_RAMPART'
    | 'SINGLE_LAYER_LOBATE'
    | 'DOUBLE_LAYER_LOBATE'
    | 'RADIAL_RAYED'
    | 'PERCHED'
    | string;
  central_peak_present: boolean;
  estimated_age_gyr: number;
  infill_material?: string;
  scientific_notes: string;
}

export interface SpectralBandRatioIndicesData {
  iron_oxide_index: number;
  phyllosilicate_clay_index: number;
  olivine_mafic_index: number;
  hydrated_mineral_index: number;
  dominant_mineralogy: string;
  mineral_description: string;
}

export interface ThermalInertiaAssessmentData {
  daytime_ir_temp_k: number;
  nighttime_ir_temp_k: number;
  diurnal_temperature_amplitude_k: number;
  derived_thermal_inertia_tiu: number;
  estimated_grain_size_um: number;
  grain_size_classification: string;
  bearing_capacity_rating: string;
}

export interface MultiSpectralAnalysisResultData {
  latitude: number;
  longitude: number;
  target_name?: string;
  spectral_indices: SpectralBandRatioIndicesData;
  thermal_inertia: ThermalInertiaAssessmentData;
  false_color_rgb: {
    hex: string;
    channels: { red_fe_oxide: number; green_clay: number; blue_olivine: number };
    mapping_scheme: string;
  };
  instrument_sources: string[];
  scientific_provenance: ScientificProvenance;
}

export interface DetectedTemporalChangeData {
  change_id: string;
  change_type:
    | 'NEW_IMPACT_CRATER'
    | 'SLOPE_STREAK'
    | 'DUNE_MIGRATION'
    | 'FROST_SUBLIMATION'
    | 'DUST_DEPOSITION'
    | string;
  location_latitude: number;
  location_longitude: number;
  bounding_box_pixels: { x: number; y: number; w: number; h: number };
  relative_albedo_delta_pct: number;
  confidence_score: number;
  first_observed_epoch: string;
  second_observed_epoch: string;
  description: string;
}

export interface TemporalChangeDetectionResultData {
  target_region: string;
  epoch_1_date: string;
  epoch_2_date: string;
  total_changes_detected: number;
  changes: DetectedTemporalChangeData[];
  change_density_per_km2: number;
  scientific_provenance: ScientificProvenance;
}

export interface ImageRegistrationResultData {
  reference_frame_id: string;
  target_frame_id: string;
  matched_keypoints_count: number;
  inlier_matches_count: number;
  inlier_ratio: number;
  homography_matrix_3x3: number[][];
  subpixel_alignment_rmse_pixels: number;
  registration_quality: string;
  projective_scale_factor: number;
  rotation_angle_degrees: number;
  scientific_notes: string;
}

export interface SuperResolutionResultData {
  original_resolution_m_per_px: number;
  enhanced_resolution_m_per_px: number;
  enhancement_factor: number;
  psnr_db: number;
  ssim_score: number;
  features_revealed: string[];
  processing_notes: string;
}

export interface PinpointCandidateData {
  candidate_id: string;
  feature_name: string;
  latitude: number;
  longitude: number;
  elevation_m: number;
  similarity_score: number;
  confidence_level: 'high' | 'medium' | 'low' | 'insufficient_evidence';
  matched_morphology: string[];
  uncertainty_radius_km: number;
  rover_or_mission_association?: string;
  terrain_type: string;
  geological_context: string;
  reference_imagery_source: string;
  matching_rationale: string;
  uncertainty_factors: string[];
}

export interface PinpointResultData {
  query_id: string;
  candidates_found: number;
  top_candidate?: PinpointCandidateData;
  candidates: PinpointCandidateData[];
  model_version: string;
  image_hash_sha256: string;
  overall_confidence: string;
  insufficient_evidence_reason?: string;
  disclaimer: string;
}

export interface DiscoveredRegionData {
  region_id: string;
  name: string;
  naming_status: 'OFFICIAL_IAU' | 'PROVISIONAL_PLATFORM_GENERATED' | 'UNNAMED_CANDIDATE';
  terrain_classification: string;
  center_latitude: number;
  center_longitude: number;
  surface_area_km2: number;
  mean_elevation_m: number;
  elevation_relief_m: number;
  mean_slope_degrees: number;
  roughness_index_tri: number;
  boundary_polygon: Array<{ latitude: number; longitude: number }>;
  confidence_score: number;
  geological_interpretation: string;
  nearby_official_features: string[];
  naming_rationale: string;
}

export interface RegionDiscoveryResponseData {
  status: string;
  total_regions_discovered: number;
  regions: DiscoveredRegionData[];
  geojson: GeoJsonObject;
  search_parameters: ScalarRecord;
  provenance: ScientificProvenance;
  disclaimer: string;
}

// API functions
export async function fetchRegolithTypes(): Promise<{
  status: string;
  regolith_types: Record<string, RegolithPropertiesData>;
  count: number;
}> {
  const res = await fetch('/api/v1/spatial/navigation/regolith-types');
  if (!res.ok) throw new Error('Failed to fetch regolith geotechnical types.');
  return res.json();
}

export async function fetchCommWindows(lat: number, lon: number): Promise<CommunicationPassData[]> {
  const res = await fetch('/api/v1/spatial/navigation/comm-windows', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ latitude: lat, longitude: lon }),
  });
  if (!res.ok) throw new Error('Failed to calculate communications windows.');
  return res.json();
}

export async function fetchMultiRoverSimulation(
  startLat: number,
  startLon: number,
  destLat: number,
  destLon: number,
  rovers?: string[],
  soilType: string = 'basaltic_sand',
  lsDeg: number = 180.0,
  dustTau: number = 0.5,
): Promise<MultiRoverSimulationResponseData> {
  const res = await fetch('/api/v1/spatial/navigation/multi-rover-simulation', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      start_latitude: startLat,
      start_longitude: startLon,
      destination_latitude: destLat,
      destination_longitude: destLon,
      rovers: rovers,
      soil_type: soilType,
      solar_longitude_ls: lsDeg,
      dust_optical_depth_tau: dustTau,
    }),
  });
  if (!res.ok) throw new Error(`Multi-rover simulation failed: ${res.statusText}`);
  return res.json();
}

export async function fetchDetectedFeatures(
  lat: number,
  lon: number,
  radiusKm: number = 150.0,
): Promise<DetectedPlanetaryFeatureData[]> {
  const res = await fetch('/api/v1/spatial/vision/detect-features', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ latitude: lat, longitude: lon, radius_km: radiusKm }),
  });
  if (!res.ok) throw new Error(`Feature detection failed: ${res.statusText}`);
  return res.json();
}

export async function fetchCraterMorphology(
  lat: number,
  lon: number,
  diameterKm: number,
  rimElevM?: number,
  floorElevM?: number,
): Promise<CraterMorphologyProfileData> {
  const res = await fetch('/api/v1/spatial/vision/crater-profile', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      latitude: lat,
      longitude: lon,
      diameter_km: diameterKm,
      rim_elevation_m: rimElevM,
      floor_elevation_m: floorElevM,
    }),
  });
  if (!res.ok) throw new Error(`Crater morphometry failed: ${res.statusText}`);
  return res.json();
}

export async function fetchMultiSpectralAnalysis(lat: number, lon: number): Promise<MultiSpectralAnalysisResultData> {
  const res = await fetch('/api/v1/spatial/vision/multispectral-analysis', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ latitude: lat, longitude: lon }),
  });
  if (!res.ok) throw new Error(`Multi-spectral analysis failed: ${res.statusText}`);
  return res.json();
}

export async function fetchChangeDetection(
  lat: number,
  lon: number,
  epoch1: string = '2021-01-01',
  epoch2: string = '2024-01-01',
): Promise<TemporalChangeDetectionResultData> {
  const res = await fetch('/api/v1/spatial/vision/change-detection', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      latitude: lat,
      longitude: lon,
      epoch_1_date: epoch1,
      epoch_2_date: epoch2,
    }),
  });
  if (!res.ok) throw new Error(`Change detection failed: ${res.statusText}`);
  return res.json();
}

export async function fetchImageRegistration(
  refFrameId: string = 'CTX_D14_032549_1985',
  tgtFrameId: string = 'HiRISE_ESP_04299_1985',
): Promise<ImageRegistrationResultData> {
  const res = await fetch('/api/v1/spatial/vision/image-registration', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      reference_frame_id: refFrameId,
      target_frame_id: tgtFrameId,
    }),
  });
  if (!res.ok) throw new Error(`Image registration failed: ${res.statusText}`);
  return res.json();
}

export async function fetchSuperResolution(
  originalRes: number = 6.0,
  enhancementFactor: number = 2.0,
): Promise<SuperResolutionResultData> {
  const res = await fetch(
    `/api/v1/spatial/vision/super-resolution?original_resolution_m_per_px=${originalRes}&enhancement_factor=${enhancementFactor}`,
    { method: 'POST' },
  );
  if (!res.ok) throw new Error(`Super-resolution failed: ${res.statusText}`);
  return res.json();
}

export async function uploadPinpointImage(formData: FormData): Promise<PinpointResultData> {
  const res = await fetch('/api/v1/spatial/pinpoint/analyze-image', {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const errorData = (await res.json().catch(() => ({}))) as { detail?: string };
    throw new Error(errorData.detail || `Landscape localization failed: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchDiscoveredRegions(
  centerLat: number,
  centerLon: number,
  radiusKm: number = 60.0,
): Promise<RegionDiscoveryResponseData> {
  const res = await fetch('/api/v1/spatial/regions/discover', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      center_latitude: centerLat,
      center_longitude: centerLon,
      search_radius_km: radiusKm,
      min_region_area_km2: 25.0,
      cluster_sensitivity: 0.7,
    }),
  });
  if (!res.ok) throw new Error(`Region discovery failed: ${res.statusText}`);
  return res.json();
}

// -------------------------------------------------------------
// Workspace types and API calls.
// -------------------------------------------------------------

export interface StudyWorkspaceData {
  study_id: string;
  name: string;
  description: string;
  lead_investigator: string;
  target_region: string;
  target_latitude: number;
  target_longitude: number;
  active_layers: string[];
  date_created: string;
  date_modified: string;
  status: 'ACTIVE' | 'ARCHIVED' | 'PUBLISHED';
  observations_count: number;
  hypotheses_count: number;
}

export interface ScientificObservationData {
  obs_id: string;
  study_id: string;
  timestamp: string;
  latitude: number;
  longitude: number;
  elevation_m: number;
  observation_type: string;
  title: string;
  notes: string;
  tags: string[];
  epistemic_classification: string;
  attached_data_products: string[];
  uncertainty_m: number;
}

export interface ScientificHypothesisData {
  hypothesis_id: string;
  study_id: string;
  statement: string;
  status: 'HYPOTHESIZED' | 'SUPPORTED' | 'CONTRADICTED' | 'REFINED' | 'ABANDONED';
  confidence_rating: number;
  linked_evidence_ids: string[];
  competing_hypotheses: string[];
  falsification_criteria: string;
  date_formulated: string;
  date_updated: string;
}

export interface ActivityFeedItemData {
  activity_id: string;
  study_id: string;
  author: string;
  action_type: string;
  content: string;
  timestamp: string;
}

export interface StudyPackageManifestData {
  study_manifest: {
    study_id: string;
    title: string;
    description: string;
    lead_investigator: string;
    target_region: string;
    target_coordinates: { lat: number; lon: number };
    status: string;
    export_date_utc: string;
    total_observations: number;
    total_hypotheses: number;
  };
  observations: ScientificObservationData[];
  hypotheses: ScientificHypothesisData[];
  geojson: GeoJsonObject;
  scientific_provenance: ScientificProvenance;
  citation: string;
}

export async function fetchStudyWorkspaces(): Promise<StudyWorkspaceData[]> {
  const res = await fetch('/api/v1/spatial/workspace/studies');
  if (!res.ok) throw new Error(`Failed to fetch studies: ${res.statusText}`);
  return res.json();
}

export async function createStudyWorkspace(study: StudyWorkspaceData): Promise<StudyWorkspaceData> {
  const res = await fetch('/api/v1/spatial/workspace/studies', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(study),
  });
  if (!res.ok) throw new Error(`Failed to create study: ${res.statusText}`);
  return res.json();
}

export async function fetchStudyObservations(studyId: string): Promise<ScientificObservationData[]> {
  const res = await fetch(`/api/v1/spatial/workspace/studies/${studyId}/observations`);
  if (!res.ok) throw new Error(`Failed to fetch observations: ${res.statusText}`);
  return res.json();
}

export async function addStudyObservation(
  studyId: string,
  data: Partial<ScientificObservationData>,
): Promise<ScientificObservationData> {
  const res = await fetch(`/api/v1/spatial/workspace/studies/${studyId}/observations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`Failed to add observation: ${res.statusText}`);
  return res.json();
}

export async function fetchStudyHypotheses(studyId: string): Promise<ScientificHypothesisData[]> {
  const res = await fetch(`/api/v1/spatial/workspace/studies/${studyId}/hypotheses`);
  if (!res.ok) throw new Error(`Failed to fetch hypotheses: ${res.statusText}`);
  return res.json();
}

export async function addStudyHypothesis(
  studyId: string,
  data: Partial<ScientificHypothesisData>,
): Promise<ScientificHypothesisData> {
  const res = await fetch(`/api/v1/spatial/workspace/studies/${studyId}/hypotheses`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`Failed to add hypothesis: ${res.statusText}`);
  return res.json();
}

export async function fetchStudyActivity(studyId: string): Promise<ActivityFeedItemData[]> {
  const res = await fetch(`/api/v1/spatial/workspace/studies/${studyId}/activity`);
  if (!res.ok) throw new Error(`Failed to fetch activity feed: ${res.statusText}`);
  return res.json();
}

export async function exportStudyPackageManifest(studyId: string): Promise<StudyPackageManifestData> {
  const res = await fetch(`/api/v1/spatial/workspace/studies/${studyId}/export/manifest`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error(`Failed to export study package: ${res.statusText}`);
  return res.json();
}

export async function exportKmlTraverse(routeName: string, waypoints: KmlWaypoint[]): Promise<string> {
  const res = await fetch('/api/v1/spatial/workspace/export/kml', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ route_name: routeName, waypoints }),
  });
  if (!res.ok) throw new Error(`Failed to export KML: ${res.statusText}`);
  return res.text();
}

export async function fetchLatexTable(
  tableType: string = 'crater_morphometry',
): Promise<{ table_type: string; latex: string }> {
  const res = await fetch(`/api/v1/spatial/workspace/export/latex?table_type=${tableType}`);
  if (!res.ok) throw new Error(`Failed to fetch LaTeX table: ${res.statusText}`);
  return res.json();
}

// ---------------------------------------------------------------------------
// Environment and climate API types.
// ---------------------------------------------------------------------------

export interface MarsOrbitalData {
  solar_longitude_deg: number;
  heliocentric_distance_au: number;
  top_of_atmosphere_solar_flux_w_m2: number;
  solar_declination_deg: number;
  season_northern: string;
  season_southern: string;
  dust_season_risk: string;
}

export interface AtmosphericLayerData {
  altitude_above_surface_km: number;
  elevation_above_areoid_m: number;
  pressure_pa: number;
  pressure_mbar: number;
  density_kg_m3: number;
  temperature_k: number;
  temperature_c: number;
  speed_of_sound_m_s: number;
  earth_equivalent_altitude_km: number;
}

export interface VerticalAtmosphericProfileData {
  latitude: number;
  longitude: number;
  surface_elevation_m: number;
  solar_longitude_deg: number;
  surface_pressure_pa: number;
  surface_pressure_mbar: number;
  surface_density_kg_m3: number;
  scale_height_km: number;
  adiabatic_lapse_rate_k_km: number;
  above_water_triple_point: boolean;
  gas_composition_molar_pct: Record<string, number>;
  layers: AtmosphericLayerData[];
  provenance?: ScientificProvenance;
}

export interface DustOpticalDepthData {
  latitude: number;
  longitude: number;
  elevation_m: number;
  solar_longitude_deg: number;
  tau_visible: number;
  opacity_category: string;
  dust_storm_risk_index: number;
  direct_transmission_zenith: number;
  diffuse_scattering_fraction: number;
  is_basin_amplified: boolean;
  operational_recommendations: string[];
  provenance?: ScientificProvenance;
}

export interface DiurnalHourPointData {
  local_solar_time_hours: number;
  solar_zenith_angle_deg: number;
  solar_irradiance_w_m2: number;
  surface_temperature_k: number;
  surface_temperature_c: number;
  air_temperature_2m_k: number;
  air_temperature_2m_c: number;
  co2_frost_risk: boolean;
}

export interface DiurnalTemperatureProfileData {
  latitude: number;
  elevation_m: number;
  solar_longitude_deg: number;
  thermal_inertia_tiu: number;
  albedo: number;
  min_surface_temp_k: number;
  max_surface_temp_k: number;
  diurnal_temperature_swing_k: number;
  mean_surface_temp_k: number;
  regolith_type: string;
  co2_frost_present: boolean;
  hourly_curve: DiurnalHourPointData[];
  provenance?: ScientificProvenance;
}

export interface SolarPowerBudgetData {
  latitude: number;
  solar_longitude_deg: number;
  tau_visible: number;
  panel_area_m2: number;
  cell_efficiency: number;
  dust_deposition_factor: number;
  peak_power_w: number;
  daily_energy_wh_sol: number;
  average_daytime_power_w: number;
  operational_status: string;
  rover_compatibility: Record<string, RoverPowerStatus>;
  hourly_power_w: number[];
  provenance?: ScientificProvenance;
}

export interface MartianSitePreset {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  elevation_m: number;
  thermal_inertia_tiu: number;
  geological_context: string;
}

export interface MissionEnvironmentAssessmentData {
  target_name: string;
  latitude: number;
  longitude: number;
  elevation_m: number;
  solar_longitude_deg: number;
  orbital: MarsOrbitalData;
  atmosphere: VerticalAtmosphericProfileData;
  dust: DustOpticalDepthData;
  thermal: DiurnalTemperatureProfileData;
  power_budget: SolarPowerBudgetData;
  overall_site_viability_score: number;
  environmental_hazards: string[];
  provenance?: ScientificProvenance;
}

export async function fetchEnvironmentOverview(ls_deg: number = 0.0): Promise<{
  status: string;
  orbital: MarsOrbitalData;
  mean_datum_pressure_pa: number;
  mean_datum_pressure_mbar: number;
  water_triple_point_pa: number;
}> {
  const res = await fetch(`/api/v1/spatial/environment/overview?ls_deg=${ls_deg}`);
  if (!res.ok) throw new Error(`Failed to fetch orbital overview: ${res.statusText}`);
  return res.json();
}

export async function fetchEnvironmentPresets(): Promise<{
  status: string;
  count: number;
  presets: MartianSitePreset[];
}> {
  const res = await fetch('/api/v1/spatial/environment/presets');
  if (!res.ok) throw new Error(`Failed to fetch environmental presets: ${res.statusText}`);
  return res.json();
}

export async function fetchAtmosphericProfile(req: {
  latitude: number;
  longitude: number;
  elevation_m: number;
  ls_deg: number;
  max_altitude_km?: number;
  step_km?: number;
}): Promise<{ status: string; profile: VerticalAtmosphericProfileData }> {
  const res = await fetch('/api/v1/spatial/environment/atmospheric-profile', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(`Failed to compute atmospheric profile: ${res.statusText}`);
  return res.json();
}

export async function fetchDustOpticalDepth(req: {
  latitude: number;
  longitude: number;
  elevation_m: number;
  ls_deg: number;
  global_dust_multiplier?: number;
}): Promise<{ status: string; result: DustOpticalDepthData }> {
  const res = await fetch('/api/v1/spatial/environment/dust-optical-depth', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(`Failed to compute dust optical depth: ${res.statusText}`);
  return res.json();
}

export async function fetchDiurnalTemperature(req: {
  latitude: number;
  elevation_m: number;
  ls_deg: number;
  thermal_inertia_tiu?: number;
  albedo?: number;
  tau?: number;
}): Promise<{ status: string; profile: DiurnalTemperatureProfileData }> {
  const res = await fetch('/api/v1/spatial/environment/diurnal-temperature', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(`Failed to compute diurnal temperature: ${res.statusText}`);
  return res.json();
}

export async function fetchSolarPowerBudget(req: {
  latitude: number;
  ls_deg: number;
  tau?: number;
  panel_area_m2?: number;
  cell_efficiency?: number;
  dust_deposition_factor?: number;
}): Promise<{ status: string; budget: SolarPowerBudgetData }> {
  const res = await fetch('/api/v1/spatial/environment/solar-power-budget', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(`Failed to compute solar power budget: ${res.statusText}`);
  return res.json();
}

export async function fetchMissionEnvironmentAssessment(req: {
  target_name: string;
  latitude: number;
  longitude: number;
  elevation_m: number;
  ls_deg: number;
  thermal_inertia_tiu?: number;
  panel_area_m2?: number;
}): Promise<{ status: string; assessment: MissionEnvironmentAssessmentData }> {
  const res = await fetch('/api/v1/spatial/environment/mission-assessment', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(`Failed to run mission environment assessment: ${res.statusText}`);
  return res.json();
}
