/**
 * Zuhura Frontend - Scientific Terrain Intelligence API Client
 * Client for the /api/v1/spatial/terrain/* endpoints.
 */

export interface Coordinate {
  latitude: number;
  longitude: number;
}

export interface PointAnalysisResult {
  coordinate: {
    latitude: number;
    longitude: number;
    latitude_type: string;
    longitude_convention: string;
  };
  elevation: {
    elevation_m: number | null;
    vertical_datum: string;
    vertical_accuracy_m: number;
    nodata_status: boolean;
  };
  derivatives: {
    slope_deg: number | null;
    aspect_deg: number | null;
    aspect_cardinal: string;
    is_flat: boolean;
    calculation_method?: string;
    metric_cell_size_m?: {
      dx_m: number;
      dy_m: number;
    };
    profile_curvature?: number;
  };
  morphometry: {
    kernel_dimensions: [number, number];
    cell_count: number;
    center_elevation_m: number;
    min_elevation_m: number;
    max_elevation_m: number;
    mean_elevation_m: number;
    median_elevation_m: number;
    std_dev_m: number;
    local_relief_m: number;
    tri_roughness_m: number;
    tpi_m: number;
    tpi_classification: string;
  } | null;
  provenance: {
    source_dataset: string;
    source_resolution_m: number;
    vertical_datum?: string;
    native_crs?: string;
    query_timestamp: string;
    validation_status: string;
  };
}

export interface ProfileStation {
  step: number;
  distance_km: number;
  latitude: number;
  longitude: number;
  elevation_m: number;
  segment_slope_deg?: number;
}

export interface TransectSummary {
  total_distance_km: number;
  num_samples: number;
  sample_step_m: number;
  min_elevation_m: number;
  max_elevation_m: number;
  mean_elevation_m: number;
  elevation_relief_m: number;
  cumulative_elevation_gain_m: number;
  cumulative_elevation_loss_m: number;
  mean_slope_deg: number;
  max_slope_deg: number;
}

export interface TerrainProfileResult {
  transect_summary: TransectSummary;
  samples: ProfileStation[];
  provenance: {
    source_dataset: string;
    vertical_datum: string;
    geodetic_reference: string;
    nominal_resolution_m: number;
    interpolation_method: string;
    query_timestamp: string;
    validation_status: string;
  };
}

export interface AreaStatisticsResult {
  query_region: {
    type: string;
    center: Coordinate;
    radius_km: number;
    area_km2: number;
  };
  elevation_statistics: {
    cell_count: number;
    min_m: number;
    max_m: number;
    mean_m: number;
    median_m: number;
    std_dev_m: number;
    relief_m: number;
  };
  slope_statistics: {
    mean_deg: number;
    median_deg: number;
    std_dev_deg: number;
    max_deg: number;
    trafficability_grade: string;
  };
  roughness_indices: {
    mean_tri_m: number;
    max_tri_m: number;
    vector_ruggedness_measure: number;
  };
  provenance: {
    source_dataset: string;
    source_resolution_m: number;
    vertical_datum: string;
    geodetic_reference: string;
  };
}

export async function fetchPointAnalysis(
  latitude: number,
  longitude: number,
  kernelSize: number = 3,
  includeMorphometry: boolean = true,
): Promise<PointAnalysisResult> {
  const res = await fetch('/api/v1/spatial/terrain/point-analysis', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      latitude,
      longitude,
      kernel_size: kernelSize,
      include_morphometry: includeMorphometry,
    }),
  });
  if (!res.ok) {
    throw new Error(`Terrain point analysis failed: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchTerrainProfile(
  startPoint: Coordinate,
  endPoint: Coordinate,
  numSamples: number = 50,
  includeDerivatives: boolean = true,
): Promise<TerrainProfileResult> {
  const res = await fetch('/api/v1/spatial/terrain/profile', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      start_point: startPoint,
      end_point: endPoint,
      num_samples: numSamples,
      include_derivatives: includeDerivatives,
      interpolation_method: 'bilinear',
    }),
  });
  if (!res.ok) {
    throw new Error(`Transect profile query failed: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchAreaStatistics(
  centerPoint: Coordinate,
  radiusKm: number = 15.0,
): Promise<AreaStatisticsResult> {
  const res = await fetch('/api/v1/spatial/terrain/statistics', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      center_point: centerPoint,
      radius_km: radiusKm,
    }),
  });
  if (!res.ok) {
    throw new Error(`Area statistics query failed: ${res.statusText}`);
  }
  return res.json();
}
