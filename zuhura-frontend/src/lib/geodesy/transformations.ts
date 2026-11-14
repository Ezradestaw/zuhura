import { MARS_SEMI_MAJOR_A, MARS_SEMI_MINOR_C, MARS_MEAN_RADIUS_M } from './constants';

/**
 * Converts Planetographic latitude to Planetocentric latitude in degrees.
 * tan(phi_c) = (C / A)^2 * tan(phi_g)
 */
export function planetographicToPlanetocentricLat(latDeg: number): number {
  if (Math.abs(latDeg) >= 90.0) return latDeg > 0 ? 90.0 : -90.0;
  if (latDeg === 0.0) return 0.0;

  const phiGRad = (latDeg * Math.PI) / 180.0;
  const ratioSq = Math.pow(MARS_SEMI_MINOR_C / MARS_SEMI_MAJOR_A, 2);
  const phiCRad = Math.atan(ratioSq * Math.tan(phiGRad));
  return (phiCRad * 180.0) / Math.PI;
}

/**
 * Converts Planetocentric latitude to Planetographic latitude in degrees.
 * tan(phi_g) = (A / C)^2 * tan(phi_c)
 */
export function planetocentricToPlanetographicLat(latDeg: number): number {
  if (Math.abs(latDeg) >= 90.0) return latDeg > 0 ? 90.0 : -90.0;
  if (latDeg === 0.0) return 0.0;

  const phiCRad = (latDeg * Math.PI) / 180.0;
  const invRatioSq = Math.pow(MARS_SEMI_MAJOR_A / MARS_SEMI_MINOR_C, 2);
  const phiGRad = Math.atan(invRatioSq * Math.tan(phiCRad));
  return (phiGRad * 180.0) / Math.PI;
}

/**
 * Normalizes longitude to standard East-positive convention.
 */
export function normalizeEastLongitude(
  lonDeg: number,
  isWestPositive: boolean = false,
  range180: boolean = false,
): number {
  let lon = lonDeg;
  if (isWestPositive) {
    lon = (360.0 - lon) % 360.0;
  }
  lon = lon % 360.0;
  if (lon < 0.0) lon += 360.0;

  if (range180 && lon > 180.0) {
    lon -= 360.0;
  }
  return lon;
}

/**
 * Calculates Great-Circle surface distance on Mars in kilometers.
 */
export function marsSurfaceDistanceKm(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const phi1 = (lat1 * Math.PI) / 180.0;
  const phi2 = (lat2 * Math.PI) / 180.0;
  const dphi = ((lat2 - lat1) * Math.PI) / 180.0;
  const dlambda = ((lon2 - lon1) * Math.PI) / 180.0;

  const a = Math.sin(dphi / 2.0) ** 2 + Math.cos(phi1) * Math.cos(phi2) * Math.sin(dlambda / 2.0) ** 2;
  const c = 2.0 * Math.atan2(Math.sqrt(a), Math.sqrt(1.0 - a));
  return (MARS_MEAN_RADIUS_M * c) / 1000.0;
}
