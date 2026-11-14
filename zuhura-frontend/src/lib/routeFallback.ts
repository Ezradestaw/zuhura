import { RoutePlanningResponseData, RouteOptionData, RouteWaypoint } from './advancedApiClient';
import { fetchTerrainProfile, TerrainProfileResult } from './terrainApiClient';

export const SYNTHETIC_ROUTE_WARNING = 'Estimated elevations (elevation service unavailable)';
export const SYNTHETIC_ROUTE_STATUS = 'fallback_synthetic_simulation';
export const MOLA_TRANSECT_STATUS = 'mola_transect_sampled';

function toRad(deg: number): number {
  return (deg * Math.PI) / 180;
}

function toDeg(rad: number): number {
  return (rad * 180) / Math.PI;
}

/**
 * Great-circle surface distance in kilometers on the Martian sphere (R = 3,389.5 km).
 */
export function marsDistanceKm(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 3389.5;
  const phi1 = toRad(lat1);
  const phi2 = toRad(lat2);
  const dPhi = toRad(lat2 - lat1);
  const dLam = toRad(lon2 - lon1);

  const a =
    Math.sin(dPhi / 2) * Math.sin(dPhi / 2) + Math.cos(phi1) * Math.cos(phi2) * Math.sin(dLam / 2) * Math.sin(dLam / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

interface RouteEndpoint {
  lat: number;
  lon: number;
  name?: string;
  elevation_m?: number;
}

function slerpLatLon(start: RouteEndpoint, end: RouteEndpoint, fraction: number): { lat: number; lon: number } {
  const lat1 = toRad(start.lat);
  const lon1 = toRad(start.lon);
  const lat2 = toRad(end.lat);
  const lon2 = toRad(end.lon);
  const d = marsDistanceKm(start.lat, start.lon, end.lat, end.lon) / 3389.5;

  if (d < 1e-6) {
    return { lat: start.lat, lon: start.lon };
  }

  const A = Math.sin((1 - fraction) * d) / Math.sin(d);
  const B = Math.sin(fraction * d) / Math.sin(d);
  const x = A * Math.cos(lat1) * Math.cos(lon1) + B * Math.cos(lat2) * Math.cos(lon2);
  const y = A * Math.cos(lat1) * Math.sin(lon1) + B * Math.cos(lat2) * Math.sin(lon2);
  const z = A * Math.sin(lat1) + B * Math.sin(lat2);
  return {
    lat: toDeg(Math.atan2(z, Math.sqrt(x * x + y * y))),
    lon: toDeg(Math.atan2(y, x)),
  };
}

function round4(value: number): number {
  return Math.round(value * 10000) / 10000;
}

function round1(value: number): number {
  return Math.round(value * 10) / 10;
}

function slopeDegrees(deltaElevM: number, distanceM: number): number {
  if (distanceM <= 0) return 0;
  return (Math.atan(Math.abs(deltaElevM) / distanceM) * 180) / Math.PI;
}

function buildRouteOption(
  profile: string,
  waypoints: RouteWaypoint[],
  coordinates: number[][],
  extras: {
    routeId: string;
    name: string;
    description: string;
    isSynthetic: boolean;
    warning?: string;
  },
): RouteOptionData {
  const totalDistKm = waypoints.length ? waypoints[waypoints.length - 1].distance_km : 0;
  let gain = 0;
  let loss = 0;
  for (let i = 1; i < waypoints.length; i++) {
    const delta = waypoints[i].elevation_m - waypoints[i - 1].elevation_m;
    if (delta > 0) gain += delta;
    else loss += -delta;
  }
  const elevations = waypoints.map((w) => w.elevation_m);
  const slopes = waypoints.map((w) => w.slope_degrees);
  const meanSlope = slopes.length ? slopes.reduce((sum, value) => sum + value, 0) / slopes.length : 0;
  const speedKmh = profile.includes('scout') ? 0.35 : profile.includes('crew') ? 0.25 : 0.12;

  return {
    route_id: extras.routeId,
    name: extras.name,
    description: extras.description,
    total_distance_km: round1(totalDistKm),
    direct_distance_km: round1(totalDistKm),
    detour_factor: 1,
    elevation_gain_m: Math.round(gain),
    elevation_loss_m: Math.round(loss),
    min_elevation_m: elevations.length ? Math.min(...elevations) : 0,
    max_elevation_m: elevations.length ? Math.max(...elevations) : 0,
    max_slope_degrees: slopes.length ? round1(Math.max(...slopes)) : 0,
    mean_slope_degrees: round1(meanSlope),
    hazard_segments_count: 0,
    estimated_duration_sols: Math.max(0.5, round1(totalDistKm / speedKmh / 4)),
    is_synthetic: extras.isSynthetic,
    provenance_warning: extras.warning,
    waypoints,
    segments: [],
    geojson: {
      type: 'Feature',
      geometry: {
        type: 'LineString',
        coordinates,
      },
      properties: {
        total_distance_km: round1(totalDistKm),
        vehicle_profile: profile,
        is_synthetic: extras.isSynthetic,
        warning: extras.warning ?? null,
      },
    },
  };
}

/**
 * Offline geodesic used only when the GDAL transect endpoint is unreachable.
 * Elevations are a straight interpolation between the two endpoint values.
 * Roughness is reported as unsampled (0). Nothing here is a MOLA observation.
 */
export function generateClientGeodesicRoute(
  start: RouteEndpoint,
  end: RouteEndpoint,
  profile: string = 'rover_perseverance',
  numSamples: number = 30,
): RoutePlanningResponseData {
  const totalDistKm = marsDistanceKm(start.lat, start.lon, end.lat, end.lon);
  const startElev = start.elevation_m ?? -2000;
  const endElev = end.elevation_m ?? -1500;
  const waypoints: RouteWaypoint[] = [];
  const coordinates: number[][] = [];
  let previousElevation = startElev;
  let previousDistanceKm = 0;

  for (let i = 0; i <= numSamples; i++) {
    const fraction = i / numSamples;
    const { lat, lon } = slerpLatLon(start, end, fraction);
    const elevation = Math.round(startElev + fraction * (endElev - startElev));
    const distanceKm = fraction * totalDistKm;
    const slope = slopeDegrees(elevation - previousElevation, (distanceKm - previousDistanceKm) * 1000);
    previousElevation = elevation;
    previousDistanceKm = distanceKm;

    const latitude = round4(lat);
    const longitude = round4(lon);
    waypoints.push({
      distance_km: round1(distanceKm),
      latitude,
      longitude,
      elevation_m: elevation,
      slope_degrees: round1(slope),
      roughness_tri: 0,
    });
    coordinates.push([longitude, latitude, elevation]);
  }

  const option = buildRouteOption(profile, waypoints, coordinates, {
    routeId: `route-demo-synthetic-${start.lat.toFixed(2)}-${end.lat.toFixed(2)}`,
    name: 'DEMO_SYNTHETIC geodesic',
    description: `${SYNTHETIC_ROUTE_WARNING}. Endpoint elevations were interpolated along a great-circle. Roughness was not sampled.`,
    isSynthetic: true,
    warning: SYNTHETIC_ROUTE_WARNING,
  });

  return {
    status: SYNTHETIC_ROUTE_STATUS,
    is_synthetic: true,
    recommended_route: option,
    alternative_routes: [option],
    mobility_profile: profile,
    cost_model_parameters: {
      profile,
      elevation_method: 'linear_endpoint_interpolation',
      roughness_sampled: false,
    },
    scientific_provenance: {
      source: 'DEMO_SYNTHETIC',
      is_synthetic: true,
      warning: SYNTHETIC_ROUTE_WARNING,
      elevation_method: 'linear interpolation between endpoint elevations',
      roughness: 'not sampled',
      validation_status: SYNTHETIC_ROUTE_STATUS,
    },
    disclaimer: SYNTHETIC_ROUTE_WARNING,
  };
}

/**
 * Maps a GDAL/MOLA great-circle transect into the route payload the globe already renders.
 * This is a sampled profile, not an A* mobility optimum.
 */
export function terrainProfileToRoute(
  profileResult: TerrainProfileResult,
  mobilityProfile: string,
): RoutePlanningResponseData {
  if (!profileResult.samples.length) {
    throw new Error('MOLA transect returned no samples.');
  }
  if (profileResult.samples.some((sample) => sample.elevation_m == null || Number.isNaN(sample.elevation_m))) {
    throw new Error('MOLA transect contained nodata elevations.');
  }

  const waypoints: RouteWaypoint[] = profileResult.samples.map((sample) => ({
    distance_km: round1(sample.distance_km),
    latitude: round4(sample.latitude),
    longitude: round4(sample.longitude),
    elevation_m: sample.elevation_m,
    slope_degrees: round1(sample.segment_slope_deg ?? 0),
    roughness_tri: 0,
  }));
  const coordinates = waypoints.map((waypoint) => [waypoint.longitude, waypoint.latitude, waypoint.elevation_m]);
  const option = buildRouteOption(mobilityProfile, waypoints, coordinates, {
    routeId: `route-mola-transect-${waypoints[0].latitude.toFixed(2)}-${waypoints[waypoints.length - 1].latitude.toFixed(2)}`,
    name: 'MOLA great-circle transect',
    description:
      'Elevations sampled from the backend GDAL MOLA profile. This is a direct geodesic, not a slope-optimized traverse. TRI roughness was not part of the transect product.',
    isSynthetic: false,
  });

  return {
    status: MOLA_TRANSECT_STATUS,
    is_synthetic: false,
    recommended_route: option,
    alternative_routes: [option],
    mobility_profile: mobilityProfile,
    cost_model_parameters: {
      profile: mobilityProfile,
      elevation_method: profileResult.provenance.interpolation_method,
      roughness_sampled: false,
    },
    scientific_provenance: {
      source: profileResult.provenance.source_dataset,
      source_dataset: profileResult.provenance.source_dataset,
      vertical_datum: profileResult.provenance.vertical_datum,
      geodetic_reference: profileResult.provenance.geodetic_reference,
      nominal_resolution_m: profileResult.provenance.nominal_resolution_m,
      interpolation_method: profileResult.provenance.interpolation_method,
      query_timestamp: profileResult.provenance.query_timestamp,
      validation_status: profileResult.provenance.validation_status,
      is_synthetic: false,
      note: 'Great-circle MOLA sample, not a slope-optimized A* route.',
    },
    disclaimer:
      'Elevation samples come from the MOLA transect service along a great-circle. They are not a certified rover path.',
  };
}

/**
 * Prefer the backend GDAL elevation transect. Fall back to an explicitly labeled synthetic geodesic.
 */
export async function resolveRouteWithElevation(
  start: RouteEndpoint,
  end: RouteEndpoint,
  mobilityProfile: string = 'rover_perseverance',
  numSamples: number = 30,
): Promise<RoutePlanningResponseData> {
  try {
    const profileResult = await fetchTerrainProfile(
      { latitude: start.lat, longitude: start.lon },
      { latitude: end.lat, longitude: end.lon },
      Math.min(500, Math.max(5, numSamples + 1)),
      true,
    );
    return terrainProfileToRoute(profileResult, mobilityProfile);
  } catch {
    return generateClientGeodesicRoute(start, end, mobilityProfile, numSamples);
  }
}
