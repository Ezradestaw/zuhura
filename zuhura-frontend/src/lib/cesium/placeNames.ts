import * as Cesium from 'cesium';

/** An IAU-named surface feature, as stored in public/data/mars-features.json. */
export interface PlaceFeature {
  name: string;
  category: string;
  lat: number;
  lon: number;
  diameter_km: number;
  rank: number;
}

export interface PlaceNamesLayer {
  setVisible: (visible: boolean) => void;
  destroy: () => void;
}

const MARS_MEAN_RADIUS_KM = 3389.5;

// Features drawn as a circle of their diameter. Elongated features (chasmata, valles, fossae)
// and very large regions (terrae, planitiae, polar caps) are labelled only.
const OUTLINED = new Set(['crater', 'mons', 'tholus', 'patera']);
const MAX_OUTLINE_DIAMETER_KM = 1500;

const OUTLINE_COLOR = Cesium.Color.fromCssColorString('#e3cca3').withAlpha(0.75);
const LABEL_FILL = Cesium.Color.WHITE;
const LABEL_OUTLINE = Cesium.Color.fromCssColorString('#011c2b');

/** Camera distance (m) beyond which a feature's label and outline are hidden. */
function visibleWithin(feature: PlaceFeature): number {
  if (feature.rank === 1) return Number.POSITIVE_INFINITY;
  const byDiameter = Math.max(feature.diameter_km, 5) * 45_000;
  const limit = feature.rank === 2 ? 25_000_000 : 6_000_000;
  return Math.min(byDiameter, limit);
}

/** Points on a small circle of the given radius around (lat, lon), using a spherical approximation. */
function circlePositions(lat: number, lon: number, radiusKm: number, ellipsoid: Cesium.Ellipsoid): Cesium.Cartesian3[] {
  const angular = radiusKm / MARS_MEAN_RADIUS_KM;
  const lat1 = Cesium.Math.toRadians(lat);
  const lon1 = Cesium.Math.toRadians(lon);
  const steps = Math.min(96, Math.max(24, Math.round(radiusKm / 2)));
  const positions: Cesium.Cartesian3[] = [];
  for (let i = 0; i <= steps; i++) {
    const bearing = (2 * Math.PI * i) / steps;
    const lat2 = Math.asin(Math.sin(lat1) * Math.cos(angular) + Math.cos(lat1) * Math.sin(angular) * Math.cos(bearing));
    const lon2 =
      lon1 +
      Math.atan2(
        Math.sin(bearing) * Math.sin(angular) * Math.cos(lat1),
        Math.cos(angular) - Math.sin(lat1) * Math.sin(lat2),
      );
    positions.push(Cesium.Cartesian3.fromRadians(lon2, lat2, 0, ellipsoid));
  }
  return positions;
}

/**
 * Adds labels for every named feature, plus outline circles for craters and volcanoes.
 * Small features appear only when the camera is close, so the globe stays readable.
 */
export function addPlaceNames(
  viewer: Cesium.Viewer,
  features: PlaceFeature[],
  ellipsoid: Cesium.Ellipsoid,
  skipNames: Set<string> = new Set(),
): PlaceNamesLayer {
  const labels = viewer.scene.primitives.add(
    new Cesium.LabelCollection({ scene: viewer.scene }),
  ) as Cesium.LabelCollection;
  const outlines = viewer.scene.primitives.add(new Cesium.PolylineCollection()) as Cesium.PolylineCollection;

  for (const feature of features) {
    if (skipNames.has(feature.name)) continue;
    const range = visibleWithin(feature);
    const display = new Cesium.DistanceDisplayCondition(0, range);
    const large = feature.rank === 1 || feature.diameter_km >= 500;

    labels.add({
      position: Cesium.Cartesian3.fromDegrees(feature.lon, feature.lat, 0, ellipsoid),
      text: feature.name,
      font: large ? '600 13px Inter, sans-serif' : '12px Inter, sans-serif',
      fillColor: LABEL_FILL,
      outlineColor: LABEL_OUTLINE,
      outlineWidth: 3,
      style: Cesium.LabelStyle.FILL_AND_OUTLINE,
      horizontalOrigin: Cesium.HorizontalOrigin.CENTER,
      verticalOrigin: Cesium.VerticalOrigin.CENTER,
      distanceDisplayCondition: display,
      // Draw slightly toward the camera so nearby terrain does not clip the text.
      eyeOffset: new Cesium.Cartesian3(0, 0, -20_000),
    });

    if (OUTLINED.has(feature.category) && feature.diameter_km > 0 && feature.diameter_km <= MAX_OUTLINE_DIAMETER_KM) {
      outlines.add({
        positions: circlePositions(feature.lat, feature.lon, feature.diameter_km / 2, ellipsoid),
        width: 1.5,
        material: Cesium.Material.fromType('Color', { color: OUTLINE_COLOR }),
        distanceDisplayCondition: display,
      });
    }
  }

  return {
    setVisible: (visible) => {
      labels.show = visible;
      outlines.show = visible;
    },
    destroy: () => {
      if (!viewer.isDestroyed()) {
        viewer.scene.primitives.remove(labels);
        viewer.scene.primitives.remove(outlines);
      }
    },
  };
}

export async function loadPlaceFeatures(): Promise<PlaceFeature[]> {
  const response = await fetch('/data/mars-features.json');
  if (!response.ok) throw new Error(`Could not load place names (HTTP ${response.status})`);
  return response.json();
}
