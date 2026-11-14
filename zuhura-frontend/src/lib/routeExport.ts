import { RouteOptionData, RouteWaypoint } from './advancedApiClient';

export interface TraverseExportPoint {
  latitude: number;
  longitude: number;
  elevation_m: number;
  distance_km: number;
  slope_degrees: number;
  roughness_tri?: number;
}

function xmlEscape(value: string): string {
  return value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function csvCell(value: string | number): string {
  const text = String(value);
  if (/[",\n]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

export function routeWaypoints(route: RouteOptionData): TraverseExportPoint[] {
  return (route.waypoints || []).map((waypoint: RouteWaypoint) => ({
    latitude: waypoint.latitude,
    longitude: waypoint.longitude,
    elevation_m: waypoint.elevation_m,
    distance_km: waypoint.distance_km,
    slope_degrees: waypoint.slope_degrees,
    roughness_tri: waypoint.roughness_tri,
  }));
}

export function buildTraverseGeoJson(route: RouteOptionData): Record<string, unknown> {
  const points = routeWaypoints(route);
  return {
    type: 'FeatureCollection',
    features: [
      {
        type: 'Feature',
        geometry: {
          type: 'LineString',
          coordinates: points.map((point) => [point.longitude, point.latitude, point.elevation_m]),
        },
        properties: {
          route_id: route.route_id,
          name: route.name,
          total_distance_km: route.total_distance_km,
          elevation_gain_m: route.elevation_gain_m,
          elevation_loss_m: route.elevation_loss_m,
          max_slope_degrees: route.max_slope_degrees,
          mean_slope_degrees: route.mean_slope_degrees,
          is_synthetic: route.is_synthetic ?? false,
          warning: route.provenance_warning ?? null,
        },
      },
      ...points.map((point, index) => ({
        type: 'Feature',
        geometry: {
          type: 'Point',
          coordinates: [point.longitude, point.latitude, point.elevation_m],
        },
        properties: {
          station_index: index,
          latitude: point.latitude,
          longitude: point.longitude,
          elevation_m: point.elevation_m,
          cumulative_distance_km: point.distance_km,
          slope_degrees: point.slope_degrees,
          roughness_tri: point.roughness_tri ?? null,
        },
      })),
    ],
  };
}

export function buildTraverseCsv(route: RouteOptionData): string {
  const header = [
    'station_index',
    'latitude',
    'longitude',
    'elevation_m',
    'cumulative_distance_km',
    'slope_degrees',
    'roughness_tri',
  ];
  const rows = routeWaypoints(route).map((point, index) =>
    [
      index,
      point.latitude,
      point.longitude,
      point.elevation_m,
      point.distance_km,
      point.slope_degrees,
      point.roughness_tri ?? '',
    ]
      .map(csvCell)
      .join(','),
  );
  return [header.join(','), ...rows].join('\n');
}

export function buildTraverseKml(route: RouteOptionData): string {
  const points = routeWaypoints(route);
  const coordinates = points.map((point) => `${point.longitude},${point.latitude},${point.elevation_m}`).join(' ');
  const name = xmlEscape(route.name || 'Zuhura traverse');
  const description = xmlEscape(route.provenance_warning || route.description || 'Zuhura planned traverse');
  return `<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>${name}</name>
    <description>${description}</description>
    <Placemark>
      <name>${name}</name>
      <description>${description}</description>
      <LineString>
        <altitudeMode>absolute</altitudeMode>
        <coordinates>${coordinates}</coordinates>
      </LineString>
    </Placemark>
  </Document>
</kml>
`;
}

export function downloadTextFile(filename: string, contents: string, mimeType: string): void {
  const blob = new Blob([contents], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
}
