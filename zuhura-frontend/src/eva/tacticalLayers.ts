/**
 * ARES-HUD: Tier 5 Tactical EVA Data Overlays
 * NASA Space Apps Challenge 2026: "Interplanetary Survival Guide: Martian Map"
 *
 * Implements 4 high-resolution tactical layers inside the Jezero HiRISE bounding box:
 * 1. Slope & Roughness Hazard Layer (<12° Green, 12°–20° Amber, >20° Red)
 * 2. Thermal Inertia & Regolith Firmness Layer (Bedrock vs Loose Sand Ripples)
 * 3. Astrobiology & Mineral Science Targets (CRISM / Perseverance Waypoints)
 * 4. Solar & Cosmic Radiation Shielding Layer (Cliff Shadow Pockets vs Open Ridges)
 */

import * as Cesium from 'cesium';
import { MARS_ELLIPSOID } from '../lib/cesium/marsEllipsoid';
import {
  JEZERO_SCIENCE_TARGETS,
  THEMIS_REGOLITH_ZONES,
  RADIATION_SHIELDING_ZONES,
  JEZERO_HAB_COORDINATES,
} from './jezeroScienceTargets';
import { EvaPoint, EvaRoutePlan } from './metabolicPathfinder';

export interface TacticalLayerConfig {
  slopeHazardVisible: boolean;
  slopeHazardOpacity: number;
  thermalRegolithVisible: boolean;
  thermalRegolithOpacity: number;
  scienceTargetsVisible: boolean;
  radiationShieldingVisible: boolean;
  radiationShieldingOpacity: number;
}

export const DEFAULT_TACTICAL_CONFIG: TacticalLayerConfig = {
  slopeHazardVisible: true,
  slopeHazardOpacity: 0.35,
  thermalRegolithVisible: true,
  thermalRegolithOpacity: 0.30,
  scienceTargetsVisible: true,
  radiationShieldingVisible: true,
  radiationShieldingOpacity: 0.25,
};

/**
 * Procedural Slope & Roughness Hazard polygons across the Jezero delta scarp.
 */
export const SLOPE_HAZARD_ZONES = [
  // Impassable Cliff Face (>20° - Crimson Red)
  {
    id: 'hazard-scarp-cliff-01',
    name: 'Western Delta Scarp Cliff (Impassable >24°)',
    slope: 24.5,
    level: 'impassable',
    colorHex: '#ef4444',
    polygon: [
      [77.530, 18.420],
      [77.538, 18.422],
      [77.536, 18.445],
      [77.528, 18.440],
    ],
  },
  {
    id: 'hazard-kodiak-cliffs',
    name: 'Kodiak Butte Erosional Escarpment (28°)',
    slope: 28.0,
    level: 'impassable',
    colorHex: '#ef4444',
    polygon: [
      [77.535, 18.394],
      [77.542, 18.395],
      [77.540, 18.401],
      [77.533, 18.399],
    ],
  },
  // High Exertion Slopes (12° - 20° - Amber Yellow)
  {
    id: 'hazard-delta-ramp-01',
    name: 'Delta Toe Ascent Ramp (15° Exertion)',
    slope: 15.2,
    level: 'high_exertion',
    colorHex: '#f59e0b',
    polygon: [
      [77.538, 18.422],
      [77.548, 18.425],
      [77.546, 18.448],
      [77.536, 18.445],
    ],
  },
  {
    id: 'hazard-neretya-channel-slopes',
    name: 'Neretya Inflow Channel Wall (18°)',
    slope: 18.4,
    level: 'high_exertion',
    colorHex: '#f59e0b',
    polygon: [
      [77.514, 18.515],
      [77.526, 18.518],
      [77.522, 18.535],
      [77.510, 18.530],
    ],
  },
  // Safe Walking Pavement (<12° - Emerald Green)
  {
    id: 'safe-crater-floor',
    name: 'Jezero Floor Traversal Corridor (4° Slope)',
    slope: 4.2,
    level: 'safe',
    colorHex: '#10b981',
    polygon: [
      [77.550, 18.410],
      [77.585, 18.415],
      [77.585, 18.465],
      [77.550, 18.460],
    ],
  },
  {
    id: 'safe-delta-top-bench',
    name: 'Delta Top Sedimentary Bench (6° Slope)',
    slope: 6.1,
    level: 'safe',
    colorHex: '#10b981',
    polygon: [
      [77.515, 18.445],
      [77.528, 18.448],
      [77.525, 18.475],
      [77.512, 18.470],
    ],
  },
];

/**
 * Creates and binds all Tier 5 Tactical EVA entities to the Cesium Viewer.
 */
export function createTacticalEvaEntities(
  viewer: Cesium.Viewer,
  config: TacticalLayerConfig,
  _onTargetClick?: (targetId: string) => void
): Cesium.Entity[] {
  const createdEntities: Cesium.Entity[] = [];

  // 1. Jezero Habitat / Base Pin
  const habEntity = viewer.entities.add({
    id: 'eva-jezero-hab-entity',
    name: `${JEZERO_HAB_COORDINATES.name} (${JEZERO_HAB_COORDINATES.designation})`,
    position: Cesium.Cartesian3.fromDegrees(
      JEZERO_HAB_COORDINATES.longitude,
      JEZERO_HAB_COORDINATES.latitude,
      0,
      MARS_ELLIPSOID
    ),
    point: {
      pixelSize: 14,
      color: Cesium.Color.fromCssColorString('#06b6d4'),
      outlineColor: Cesium.Color.WHITE,
      outlineWidth: 2,
      heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
    },
    label: {
      text: 'BASE-ALPHA-01 (Jezero Hab)',
      font: 'bold 12px monospace',
      style: Cesium.LabelStyle.FILL_AND_OUTLINE,
      fillColor: Cesium.Color.WHITE,
      outlineColor: Cesium.Color.BLACK,
      outlineWidth: 3,
      verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
      pixelOffset: new Cesium.Cartesian2(0, -18),
      heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
      distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0.0, 150000.0),
    },
  });
  createdEntities.push(habEntity);

  // 2. LAYER 1: Slope & Roughness Hazard Layer
  if (config.slopeHazardVisible) {
    SLOPE_HAZARD_ZONES.forEach((zone) => {
      const positions = zone.polygon.map(([lon, lat]) =>
        Cesium.Cartesian3.fromDegrees(lon, lat, 0, MARS_ELLIPSOID)
      );

      const color = Cesium.Color.fromCssColorString(zone.colorHex).withAlpha(
        config.slopeHazardOpacity
      );

      const entity = viewer.entities.add({
        id: `eva-${zone.id}`,
        name: `${zone.name} (${zone.slope}° Gradient)`,
        polygon: {
          hierarchy: positions,
          material: color,
          outline: true,
          outlineColor: Cesium.Color.fromCssColorString(zone.colorHex),
          outlineWidth: 2,
          heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
        },
      });
      createdEntities.push(entity);
    });
  }

  // 3. LAYER 2: Thermal Inertia & Regolith Firmness Layer
  if (config.thermalRegolithVisible) {
    THEMIS_REGOLITH_ZONES.forEach((zone) => {
      const positions = zone.polygon.map(([lon, lat]) =>
        Cesium.Cartesian3.fromDegrees(lon, lat, 0, MARS_ELLIPSOID)
      );

      const color = Cesium.Color.fromCssColorString(zone.color_hex).withAlpha(
        config.thermalRegolithOpacity
      );

      const entity = viewer.entities.add({
        id: `eva-${zone.id}`,
        name: `${zone.name} — TI: ${zone.thermal_inertia_si} J m⁻² K⁻¹ s⁻½`,
        polygon: {
          hierarchy: positions,
          material: color,
          outline: true,
          outlineColor: Cesium.Color.fromCssColorString(zone.color_hex),
          outlineWidth: 2,
          heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
        },
      });
      createdEntities.push(entity);
    });
  }

  // 4. LAYER 3: Astrobiology & Mineral Science Targets
  if (config.scienceTargetsVisible) {
    JEZERO_SCIENCE_TARGETS.forEach((target) => {
      const entity = viewer.entities.add({
        id: `eva-${target.id}`,
        name: `${target.name} [Score: ${target.science_priority_score}/100]`,
        position: Cesium.Cartesian3.fromDegrees(
          target.longitude,
          target.latitude,
          0,
          MARS_ELLIPSOID
        ),
        point: {
          pixelSize: 12,
          color: Cesium.Color.fromCssColorString('#f59e0b'),
          outlineColor: Cesium.Color.WHITE,
          outlineWidth: 2,
          heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
        },
        label: {
          text: `${target.name} [${target.science_priority_score}]`,
          font: 'bold 11px monospace',
          style: Cesium.LabelStyle.FILL_AND_OUTLINE,
          fillColor: Cesium.Color.fromCssColorString('#fde047'),
          outlineColor: Cesium.Color.BLACK,
          outlineWidth: 3,
          verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
          pixelOffset: new Cesium.Cartesian2(0, -14),
          heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
          distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0.0, 100000.0),
        },
      });
      createdEntities.push(entity);
    });
  }

  // 5. LAYER 4: Solar & Cosmic Radiation Shielding Layer
  if (config.radiationShieldingVisible) {
    RADIATION_SHIELDING_ZONES.forEach((zone) => {
      const positions = zone.polygon.map(([lon, lat]) =>
        Cesium.Cartesian3.fromDegrees(lon, lat, 0, MARS_ELLIPSOID)
      );

      const color = Cesium.Color.fromCssColorString(zone.color_hex).withAlpha(
        config.radiationShieldingOpacity
      );

      const entity = viewer.entities.add({
        id: `eva-${zone.id}`,
        name: `${zone.name} — Dose Rate: ${zone.dose_rate_usv_hr} μSv/hr`,
        polygon: {
          hierarchy: positions,
          material: color,
          outline: true,
          outlineColor: Cesium.Color.fromCssColorString(zone.color_hex),
          outlineWidth: 2,
          heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
        },
      });
      createdEntities.push(entity);
    });
  }

  return createdEntities;
}

/**
 * Synchronizes Tactical EVA Entities with the Cesium Viewer, removing
 * old entities and creating fresh ones with updated visibilities and opacities.
 */
export function syncTacticalCesiumEntities(
  viewer: Cesium.Viewer,
  config: TacticalLayerConfig,
  existingEntities: Cesium.Entity[],
  onTargetClick?: (targetId: string) => void
): Cesium.Entity[] {
  // Remove existing tactical entities
  existingEntities.forEach((entity) => {
    try {
      viewer.entities.remove(entity);
    } catch (e) {
      // ignore if already removed
    }
  });

  // Re-create with new config
  return createTacticalEvaEntities(viewer, config, onTargetClick);
}

/**
 * Renders an EVA Route Plan as segmented ground-clamped polylines
 * with hazard color coding (Green: safe, Amber: high exertion, Red: critical hazard)
 * and waypoint markers.
 */
export function createEvaRouteEntities(
  viewer: Cesium.Viewer,
  route: EvaRoutePlan
): Cesium.Entity[] {
  const routeEntities: Cesium.Entity[] = [];

  // 1. Render micro-segments with ground clamping & hazard colors
  route.segments.forEach((seg, index) => {
    const p1 = Cesium.Cartesian3.fromDegrees(
      seg.from.longitude,
      seg.from.latitude,
      0,
      MARS_ELLIPSOID
    );
    const p2 = Cesium.Cartesian3.fromDegrees(
      seg.to.longitude,
      seg.to.latitude,
      0,
      MARS_ELLIPSOID
    );

    const segmentColor = Cesium.Color.fromCssColorString(seg.hazard_color);

    const segEntity = viewer.entities.add({
      id: `eva-route-seg-${index}-${route.isEmergencyAbort ? 'abort' : 'plan'}`,
      name: `EVA Segment #${index + 1} (${seg.slope_deg.toFixed(1)}° slope, ${seg.hazard_level.toUpperCase()})`,
      polyline: {
        positions: [p1, p2],
        clampToGround: true,
        width: 5,
        material: new Cesium.PolylineOutlineMaterialProperty({
          color: segmentColor,
          outlineColor: Cesium.Color.BLACK,
          outlineWidth: 1,
        }),
      },
    });
    routeEntities.push(segEntity);
  });

  // 2. Render mission waypoint markers
  route.waypoints.forEach((wp, idx) => {
    const isFirst = idx === 0;
    const isLast = idx === route.waypoints.length - 1;
    const pinColor = isFirst
      ? '#06b6d4'
      : isLast
      ? route.isEmergencyAbort
        ? '#ef4444'
        : '#10b981'
      : '#f59e0b';

    const labelText = wp.name
      ? wp.name
      : isFirst
      ? 'EVA START'
      : isLast
      ? 'EVA OBJECTIVE'
      : `WP-${idx}`;

    const wpEntity = viewer.entities.add({
      id: `eva-wp-entity-${idx}-${route.isEmergencyAbort ? 'abort' : 'plan'}`,
      name: labelText,
      position: Cesium.Cartesian3.fromDegrees(
        wp.longitude,
        wp.latitude,
        0,
        MARS_ELLIPSOID
      ),
      point: {
        pixelSize: isFirst || isLast ? 12 : 8,
        color: Cesium.Color.fromCssColorString(pinColor),
        outlineColor: Cesium.Color.WHITE,
        outlineWidth: 2,
        heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
      },
      label: {
        text: labelText,
        font: 'bold 10px monospace',
        style: Cesium.LabelStyle.FILL_AND_OUTLINE,
        fillColor: Cesium.Color.WHITE,
        outlineColor: Cesium.Color.BLACK,
        outlineWidth: 2,
        verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
        pixelOffset: new Cesium.Cartesian2(0, -12),
        heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
        distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0.0, 80000.0),
      },
    });
    routeEntities.push(wpEntity);
  });

  return routeEntities;
}

/**
 * Creates or updates the dynamic 3D Astronaut Marker for real-time Marswalk simulations.
 */
export function updateAstronautMarker(
  viewer: Cesium.Viewer,
  position: EvaPoint,
  suitOxygenPct: number,
  suitBatteryPct: number,
  existingMarker?: Cesium.Entity | null
): Cesium.Entity {
  const cartesian = Cesium.Cartesian3.fromDegrees(
    position.longitude,
    position.latitude,
    0,
    MARS_ELLIPSOID
  );

  if (existingMarker && viewer.entities.contains(existingMarker)) {
    existingMarker.position = new Cesium.ConstantPositionProperty(cartesian);
    if (existingMarker.label) {
      existingMarker.label.text = new Cesium.ConstantProperty(
        `ARES-EVA-01\nO₂: ${suitOxygenPct}% | BAT: ${suitBatteryPct}%`
      );
    }
    return existingMarker;
  }

  const marker = viewer.entities.add({
    id: 'eva-astronaut-live-marker',
    name: 'Astronaut EVA-01 (Active Sortie)',
    position: cartesian,
    point: {
      pixelSize: 16,
      color: Cesium.Color.fromCssColorString('#38bdf8'),
      outlineColor: Cesium.Color.WHITE,
      outlineWidth: 3,
      heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
    },
    label: {
      text: `ARES-EVA-01\nO₂: ${suitOxygenPct}% | BAT: ${suitBatteryPct}%`,
      font: 'bold 11px monospace',
      style: Cesium.LabelStyle.FILL_AND_OUTLINE,
      fillColor: Cesium.Color.fromCssColorString('#38bdf8'),
      outlineColor: Cesium.Color.BLACK,
      outlineWidth: 3,
      verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
      pixelOffset: new Cesium.Cartesian2(0, -20),
      heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
    },
  });

  return marker;
}
