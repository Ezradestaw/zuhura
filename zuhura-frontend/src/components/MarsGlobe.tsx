import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as Cesium from 'cesium';
import { MARS_ELLIPSOID, initializeMarsViewer } from '../lib/cesium/marsEllipsoid';
import { addPlaceNames, loadPlaceFeatures, type PlaceNamesLayer } from '../lib/cesium/placeNames';
import {
  createVikingImageryProvider,
  createCtxImageryProvider,
  createHiRiseImageryProvider,
  createMolaColormapImageryProvider,
  createMolaHrscBlendImageryProvider,
  createThemisDayIrImageryProvider,
  createTesClinopyroxeneImageryProvider,
} from '../lib/cesium/imageryProviders';
import { useGlobeStore, PlanetaryFeature } from '../store/globeStore';
import { useLayerStore } from '../store/layerStore';
import { useTerrainAnalysisStore } from '../store/terrainAnalysisStore';
import { AresHudOverlay } from '../eva/AresHudOverlay';
import {
  DEFAULT_TACTICAL_CONFIG,
  TacticalLayerConfig,
  syncTacticalCesiumEntities,
  createEvaRouteEntities,
  updateAstronautMarker,
} from '../eva/tacticalLayers';
import { EvaPoint, EvaRoutePlan } from '../eva/metabolicPathfinder';
import { JEZERO_HAB_COORDINATES } from '../eva/jezeroScienceTargets';
import { useWorkspaceStore } from '../store/workspaceStore';
import { CompassOrientationHUD } from './CompassOrientationHUD';
import { SurfaceExplorationHUD } from './SurfaceExplorationHUD';
import { GlobeMeasurementHUD } from './GlobeMeasurementHUD';
import { ImagerySplitSwipeHUD } from './ImagerySplitSwipeHUD';
import { TileLoadingProgressHUD } from './TileLoadingProgressHUD';
import { getHoverPlaceDescription } from '../lib/hoverData';

const TARGET_VIEWS: Record<string, { lon: number; lat: number; alt: number }> = {
  global: { lon: 77.45, lat: 18.44, alt: 3500000.0 },
  jezero: { lon: 77.58, lat: 18.38, alt: 180000.0 },
  gale: { lon: 137.44, lat: -4.59, alt: 180000.0 },
  valles_marineris: { lon: 283.0, lat: -9.5, alt: 850000.0 },
  olympus_mons: { lon: 226.2, lat: 18.65, alt: 500000.0 },
};

const LANDMARK_FEATURES: Record<string, PlanetaryFeature> = {
  jezero: {
    id: 'jezero-crater',
    name: 'Jezero Crater',
    type: 'crater',
    latitude: 18.38,
    longitude: 77.58,
    diameter_km: 49.0,
    elevation_m: -2648.0,
    description: 'Ancient paleolake basin and delta investigated by NASA Mars 2020 Perseverance rover.',
  },
  gale: {
    id: 'gale-crater',
    name: 'Gale Crater (Mount Sharp)',
    type: 'crater',
    latitude: -4.59,
    longitude: 137.44,
    diameter_km: 154.0,
    elevation_m: -4503.0,
    description: 'Layered sedimentary mound Aeolis Mons explored by NASA Curiosity rover.',
  },
  valles_marineris: {
    id: 'valles-marineris',
    name: 'Valles Marineris (Chasmata)',
    type: 'canyon_system',
    latitude: -9.5,
    longitude: 283.0,
    diameter_km: 4000.0,
    elevation_m: -1372.0,
    description: 'Vast canyon system stretching over 4,000 km across the Martian equator.',
  },
  olympus_mons: {
    id: 'olympus-mons',
    name: 'Olympus Mons',
    type: 'shield_volcano',
    latitude: 18.65,
    longitude: 226.2,
    diameter_km: 624.0,
    elevation_m: 20015.0,
    description: 'Largest volcano in the Solar System, rising over 21 km above the datum.',
  },
};

export const MarsGlobe: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<Cesium.Viewer | null>(null);

  // Progressive multi-resolution imagery layer references
  const vikingImageryLayerRef = useRef<Cesium.ImageryLayer | null>(null);
  const ctxImageryLayerRef = useRef<Cesium.ImageryLayer | null>(null);
  const hiriseImageryLayerRef = useRef<Cesium.ImageryLayer | null>(null);
  const molaImageryLayerRef = useRef<Cesium.ImageryLayer | null>(null);
  const molaHrscImageryLayerRef = useRef<Cesium.ImageryLayer | null>(null);
  const themisDayIrImageryLayerRef = useRef<Cesium.ImageryLayer | null>(null);
  const tesImageryLayerRef = useRef<Cesium.ImageryLayer | null>(null);

  const scientificEntitiesRef = useRef<Map<string, Cesium.Entity>>(new Map());
  const landmarkEntitiesRef = useRef<Cesium.Entity[]>([]);
  const mountSharpEntitiesRef = useRef<Cesium.Entity[]>([]);
  const roverTraverseEntitiesRef = useRef<Cesium.Entity[]>([]);
  const transectEntitiesRef = useRef<Cesium.Entity[]>([]);
  const navigationEntitiesRef = useRef<Cesium.Entity[]>([]);
  const regionEntitiesRef = useRef<Cesium.Entity[]>([]);
  const measurementEntitiesRef = useRef<Cesium.Entity[]>([]);

  const [viewerInstance, setViewerInstance] = useState<Cesium.Viewer | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const {
    setCameraPosition,
    setCameraOrientation,
    setCursorPosition,
    selectedTerrain,
    setSelectedTerrain,
    selectedFeature,
    setSelectedFeature,
    enableLighting,
    solarAzimuth,
    solarElevation,
    activeNavigationRoute,
    activeDiscoveredRegions,
    routePickTarget,
    setRoutePickTarget,
    departurePoint,
    arrivalPoint,
    setDeparturePoint,
    setArrivalPoint,
    setTilesLoadingMetrics,
    setIsMountSharpModalOpen,
    setIsRoverRawImagesOpen,
    isAresHudOpen,
    setIsAresHudOpen,
    isVisorPovActive,
    setIsVisorPovActive,
    cameraHeading,
    cameraPitch,
    setActiveEvaTargetId,
    isPlaceNamesVisible,
  } = useGlobeStore();

  const placeNamesRef = useRef<PlaceNamesLayer | null>(null);

  const { measurementToolActive, measurementPoints, addMeasurementPoint } = useWorkspaceStore();

  const measurementToolActiveRef = useRef(measurementToolActive);
  measurementToolActiveRef.current = measurementToolActive;
  const addMeasurementPointRef = useRef(addMeasurementPoint);
  addMeasurementPointRef.current = addMeasurementPoint;

  const routePickTargetRef = useRef(routePickTarget);
  routePickTargetRef.current = routePickTarget;

  const { layers } = useLayerStore();
  const { isTransectMode, transectStart, transectEnd, profileData, hoveredSampleIndex } = useTerrainAnalysisStore();

  // Terrain switching effect with smooth target navigation
  // IAU place names and feature outlines. The mission pins label these four sites already.
  useEffect(() => {
    if (!viewerInstance) return;
    let cancelled = false;
    loadPlaceFeatures()
      .then((features) => {
        if (cancelled || viewerInstance.isDestroyed()) return;
        placeNamesRef.current = addPlaceNames(
          viewerInstance,
          features,
          MARS_ELLIPSOID,
          new Set(['Jezero', 'Gale', 'Valles Marineris', 'Olympus Mons']),
        );
        placeNamesRef.current.setVisible(useGlobeStore.getState().isPlaceNamesVisible);
      })
      .catch((error) => console.warn(error));
    return () => {
      cancelled = true;
      placeNamesRef.current?.destroy();
      placeNamesRef.current = null;
    };
  }, [viewerInstance]);

  useEffect(() => {
    placeNamesRef.current?.setVisible(isPlaceNamesVisible);
  }, [isPlaceNamesVisible]);

  useEffect(() => {
    if (!viewerInstance || viewerInstance.isDestroyed()) return;

    const terrainUrl = `/api/v1/tiles/terrain/${selectedTerrain}`;
    Cesium.CesiumTerrainProvider.fromUrl(terrainUrl, {
      ellipsoid: MARS_ELLIPSOID,
      requestVertexNormals: true,
    })
      .then((provider) => {
        if (!viewerInstance.isDestroyed()) {
          viewerInstance.terrainProvider = provider;
          viewerInstance.scene.requestRender();
        }
      })
      .catch((err) => {
        console.warn(`Terrain load notice for ${selectedTerrain}:`, err);
      });

    const target = TARGET_VIEWS[selectedTerrain];
    if (target) {
      viewerInstance.camera.flyTo({
        destination: Cesium.Cartesian3.fromDegrees(target.lon, target.lat, target.alt, MARS_ELLIPSOID),
        duration: 1.5,
      });
    }

    if (LANDMARK_FEATURES[selectedTerrain]) {
      setSelectedFeature(LANDMARK_FEATURES[selectedTerrain]);
    }
  }, [viewerInstance, selectedTerrain, setSelectedFeature]);

  // Dynamic Lighting effect with oct-normal hillshading and day/night terminator
  useEffect(() => {
    if (!viewerInstance || viewerInstance.isDestroyed()) return;
    viewerInstance.scene.globe.enableLighting = enableLighting;
    viewerInstance.scene.globe.dynamicAtmosphereLighting = enableLighting;
    if (enableLighting) {
      const azRad = Cesium.Math.toRadians(solarAzimuth);
      const elRad = Cesium.Math.toRadians(solarElevation);
      const x = -Math.sin(azRad) * Math.cos(elRad);
      const y = -Math.cos(azRad) * Math.cos(elRad);
      const z = Math.sin(elRad);
      viewerInstance.scene.light = new Cesium.DirectionalLight({
        direction: new Cesium.Cartesian3(x, y, z),
      });
    }
    viewerInstance.scene.requestRender();
  }, [viewerInstance, enableLighting, solarAzimuth, solarElevation]);

  // Keep imagery layers in sync with the layer panel
  useEffect(() => {
    if (!viewerInstance || viewerInstance.isDestroyed()) return;

    // 1. Sync Base Viking MDIM 2.1 Natural Color Basemap Layer (Tier 1)
    const vikingConfig = layers.find((l) => l.id === 'zuhura-viking-mdim21');
    if (vikingImageryLayerRef.current && vikingConfig) {
      vikingImageryLayerRef.current.show = vikingConfig.visible;
      vikingImageryLayerRef.current.alpha = vikingConfig.opacity;
    }

    // 2. Sync CTX Regional Context Layer (Tier 2, Jezero Footprint)
    const ctxConfig = layers.find((l) => l.id === 'zuhura-ctx-jezero');
    if (ctxImageryLayerRef.current && ctxConfig) {
      ctxImageryLayerRef.current.show = ctxConfig.visible;
      ctxImageryLayerRef.current.alpha = ctxConfig.opacity;
    }

    // 3. Sync HiRISE Local High-Resolution Layer (Tier 3, Touchdown & Delta)
    const hiriseConfig = layers.find((l) => l.id === 'zuhura-hirise-jezero');
    if (hiriseImageryLayerRef.current && hiriseConfig) {
      hiriseImageryLayerRef.current.show = hiriseConfig.visible;
      hiriseImageryLayerRef.current.alpha = hiriseConfig.opacity;
    }

    // 4. Sync Optional MOLA COG Elevation Colormap Layer (Tier 4)
    const molaLayerConfig =
      layers.find((l) => l.id === 'zuhura-mola-global-v3-cog') || layers.find((l) => l.id === 'zuhura-mola-megdr-128');
    if (molaImageryLayerRef.current && molaLayerConfig) {
      molaImageryLayerRef.current.show = molaLayerConfig.visible;
      molaImageryLayerRef.current.alpha = molaLayerConfig.opacity;
    }

    // 4b. Sync MGS MOLA + MEX HRSC Blended Color Hillshade Layer (Tier 5)
    const molaHrscConfig = layers.find((l) => l.id === 'zuhura-mola-hrsc-blend');
    if (molaHrscImageryLayerRef.current && molaHrscConfig) {
      molaHrscImageryLayerRef.current.show = molaHrscConfig.visible;
      molaHrscImageryLayerRef.current.alpha = molaHrscConfig.opacity;
    }

    // 4c. Sync THEMIS Day IR Global Radiance Mosaic (Tier 6)
    const themisDayConfig = layers.find((l) => l.id === 'zuhura-themis-day-ir');
    if (themisDayIrImageryLayerRef.current && themisDayConfig) {
      themisDayIrImageryLayerRef.current.show = themisDayConfig.visible;
      themisDayIrImageryLayerRef.current.alpha = themisDayConfig.opacity;
    }

    // 4d. Sync MGS TES Clinopyroxene Mineralogy (Tier 7)
    const tesConfig = layers.find((l) => l.id === 'zuhura-tes-clinopyroxene');
    if (tesImageryLayerRef.current && tesConfig) {
      tesImageryLayerRef.current.show = tesConfig.visible;
      tesImageryLayerRef.current.alpha = tesConfig.opacity;
    }

    // 5. Sync Missions & Landing Sites pins
    const missionsConfig = layers.find((l) => l.id === 'zuhura-landing-sites');
    if (missionsConfig) {
      landmarkEntitiesRef.current.forEach((entity) => {
        entity.show = missionsConfig.visible;
      });
      roverTraverseEntitiesRef.current.forEach((entity) => {
        entity.show = missionsConfig.visible;
      });
    }

    // 5b. Sync Mount Sharp Exploration Route
    const mountSharpConfig = layers.find((l) => l.id === 'zuhura-mount-sharp-route');
    if (mountSharpConfig) {
      mountSharpEntitiesRef.current.forEach((entity) => {
        entity.show = mountSharpConfig.visible;
      });
    }

    // 6. Sync THEMIS, CTX, and HiRISE scientific footprint outline entities
    const themisConfig = layers.find((l) => l.id === 'zuhura-themis-ir-jezero');
    const themisEntity = scientificEntitiesRef.current.get('themis');
    if (themisEntity && themisConfig) {
      themisEntity.show = themisConfig.visible;
      if (themisEntity.polygon) {
        themisEntity.polygon.material = new Cesium.ColorMaterialProperty(
          Cesium.Color.CYAN.withAlpha(0.2 * themisConfig.opacity),
        );
      }
    }

    const ctxEntity = scientificEntitiesRef.current.get('ctx');
    if (ctxEntity && ctxConfig) {
      ctxEntity.show = ctxConfig.visible;
      if (ctxEntity.polygon) {
        ctxEntity.polygon.material = new Cesium.ColorMaterialProperty(
          Cesium.Color.GOLD.withAlpha(0.08 * ctxConfig.opacity),
        );
      }
    }

    const hiriseEntity = scientificEntitiesRef.current.get('hirise');
    if (hiriseEntity && hiriseConfig) {
      hiriseEntity.show = hiriseConfig.visible;
      if (hiriseEntity.rectangle) {
        hiriseEntity.rectangle.material = new Cesium.ColorMaterialProperty(
          Cesium.Color.RED.withAlpha(0.08 * hiriseConfig.opacity),
        );
      }
    }

    viewerInstance.scene.requestRender();
  }, [viewerInstance, layers]);

  // Geodesic Transect 3D Visualization
  useEffect(() => {
    if (!viewerInstance || viewerInstance.isDestroyed()) return;

    // Clear previous transect entities
    transectEntitiesRef.current.forEach((entity) => {
      viewerInstance.entities.remove(entity);
    });
    transectEntitiesRef.current = [];

    if (!isTransectMode) {
      viewerInstance.scene.requestRender();
      return;
    }

    const newEntities: Cesium.Entity[] = [];

    // If profile data is available, draw full polyline along great-circle arc
    if (profileData && profileData.samples && profileData.samples.length > 1) {
      const positions = profileData.samples.map((s) =>
        Cesium.Cartesian3.fromDegrees(s.longitude, s.latitude, Math.max(s.elevation_m, 0) + 50.0, MARS_ELLIPSOID),
      );

      const polyline = viewerInstance.entities.add({
        id: 'transect-great-circle-line',
        polyline: {
          positions: positions,
          width: 3.5,
          material: new Cesium.PolylineGlowMaterialProperty({
            glowPower: 0.2,
            color: Cesium.Color.fromCssColorString('#e07a5f'),
          }),
          clampToGround: true,
        },
      });
      newEntities.push(polyline);

      // Start station pin
      const startS = profileData.samples[0];
      const startPin = viewerInstance.entities.add({
        id: 'transect-station-start',
        position: Cesium.Cartesian3.fromDegrees(startS.longitude, startS.latitude, 500.0, MARS_ELLIPSOID),
        point: {
          pixelSize: 8,
          color: Cesium.Color.fromCssColorString('#10b981'),
          outlineColor: Cesium.Color.WHITE,
          outlineWidth: 2,
        },
        label: {
          text: 'Transect Station A',
          font: '10px monospace',
          fillColor: Cesium.Color.WHITE,
          outlineColor: Cesium.Color.BLACK,
          outlineWidth: 2,
          style: Cesium.LabelStyle.FILL_AND_OUTLINE,
          pixelOffset: new Cesium.Cartesian2(0, -12),
        },
      });
      newEntities.push(startPin);

      // End station pin
      const endS = profileData.samples[profileData.samples.length - 1];
      const endPin = viewerInstance.entities.add({
        id: 'transect-station-end',
        position: Cesium.Cartesian3.fromDegrees(endS.longitude, endS.latitude, 500.0, MARS_ELLIPSOID),
        point: {
          pixelSize: 8,
          color: Cesium.Color.fromCssColorString('#f43f5e'),
          outlineColor: Cesium.Color.WHITE,
          outlineWidth: 2,
        },
        label: {
          text: 'Transect Station B',
          font: '10px monospace',
          fillColor: Cesium.Color.WHITE,
          outlineColor: Cesium.Color.BLACK,
          outlineWidth: 2,
          style: Cesium.LabelStyle.FILL_AND_OUTLINE,
          pixelOffset: new Cesium.Cartesian2(0, -12),
        },
      });
      newEntities.push(endPin);

      // Highlight hovered station
      if (hoveredSampleIndex !== null && profileData.samples[hoveredSampleIndex]) {
        const hs = profileData.samples[hoveredSampleIndex];
        const hoverPin = viewerInstance.entities.add({
          id: 'transect-hover-marker',
          position: Cesium.Cartesian3.fromDegrees(hs.longitude, hs.latitude, 1000.0, MARS_ELLIPSOID),
          point: {
            pixelSize: 10,
            color: Cesium.Color.CYAN,
            outlineColor: Cesium.Color.WHITE,
            outlineWidth: 2,
          },
          label: {
            text: `${hs.elevation_m.toFixed(0)}m (${hs.distance_km.toFixed(1)}km)`,
            font: '11px monospace',
            fillColor: Cesium.Color.CYAN,
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 2,
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            pixelOffset: new Cesium.Cartesian2(0, -14),
          },
        });
        newEntities.push(hoverPin);
      }
    } else if (transectStart && transectEnd) {
      // Draw straight fallback line between start and end
      const line = viewerInstance.entities.add({
        id: 'transect-initial-line',
        polyline: {
          positions: [
            Cesium.Cartesian3.fromDegrees(transectStart.longitude, transectStart.latitude, 500, MARS_ELLIPSOID),
            Cesium.Cartesian3.fromDegrees(transectEnd.longitude, transectEnd.latitude, 500, MARS_ELLIPSOID),
          ],
          width: 2,
          material: Cesium.Color.YELLOW.withAlpha(0.7),
          clampToGround: true,
        },
      });
      newEntities.push(line);
    }

    transectEntitiesRef.current = newEntities;
    viewerInstance.scene.requestRender();
  }, [viewerInstance, isTransectMode, profileData, transectStart, transectEnd, hoveredSampleIndex]);

  // Traverse: start/destination markers, the A* path and a dashed straight line for comparison
  useEffect(() => {
    if (!viewerInstance || viewerInstance.isDestroyed()) return;

    navigationEntitiesRef.current.forEach((entity) => viewerInstance.entities.remove(entity));
    const added: Cesium.Entity[] = [];

    const addMarker = (point: { lat: number; lon: number }, label: string, color: string) => {
      added.push(
        viewerInstance.entities.add({
          position: Cesium.Cartesian3.fromDegrees(point.lon, point.lat, 0, MARS_ELLIPSOID),
          point: {
            pixelSize: 12,
            color: Cesium.Color.fromCssColorString(color),
            outlineColor: Cesium.Color.WHITE,
            outlineWidth: 2,
            heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
            disableDepthTestDistance: Number.POSITIVE_INFINITY,
          },
          label: {
            text: label,
            font: '600 12px sans-serif',
            fillColor: Cesium.Color.WHITE,
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 3,
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            pixelOffset: new Cesium.Cartesian2(0, -18),
            heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
            disableDepthTestDistance: Number.POSITIVE_INFINITY,
          },
        }),
      );
    };

    if (departurePoint) addMarker(departurePoint, 'Start', '#014166');
    if (arrivalPoint) addMarker(arrivalPoint, 'Destination', '#b45309');

    if (departurePoint && arrivalPoint) {
      added.push(
        viewerInstance.entities.add({
          polyline: {
            positions: Cesium.Cartesian3.fromDegreesArray(
              [departurePoint.lon, departurePoint.lat, arrivalPoint.lon, arrivalPoint.lat],
              MARS_ELLIPSOID,
            ),
            width: 2,
            material: new Cesium.PolylineDashMaterialProperty({ color: Cesium.Color.WHITE.withAlpha(0.7) }),
            clampToGround: true,
          },
        }),
      );
    }

    const waypoints: { latitude: number; longitude: number }[] | undefined = activeNavigationRoute?.waypoints;
    if (waypoints && waypoints.length >= 2) {
      added.push(
        viewerInstance.entities.add({
          polyline: {
            positions: Cesium.Cartesian3.fromDegreesArray(
              waypoints.flatMap((w) => [w.longitude, w.latitude]),
              MARS_ELLIPSOID,
            ),
            width: 5,
            material: new Cesium.PolylineOutlineMaterialProperty({
              color: Cesium.Color.fromCssColorString('#facc15'),
              outlineColor: Cesium.Color.BLACK,
              outlineWidth: 1.5,
            }),
            clampToGround: true,
          },
        }),
      );
    }

    navigationEntitiesRef.current = added;
    viewerInstance.scene.requestRender();
  }, [viewerInstance, activeNavigationRoute, departurePoint, arrivalPoint]);

  // 3D Geological Discovered Regions Polygon Boundaries
  useEffect(() => {
    if (!viewerInstance || viewerInstance.isDestroyed()) return;

    // Clear previous region entities
    regionEntitiesRef.current.forEach((entity) => {
      viewerInstance.entities.remove(entity);
    });
    regionEntitiesRef.current = [];

    if (!activeDiscoveredRegions || activeDiscoveredRegions.length === 0) {
      viewerInstance.scene.requestRender();
      return;
    }

    const newEntities: Cesium.Entity[] = [];

    activeDiscoveredRegions.forEach((reg: any, idx: number) => {
      if (!reg.boundary_polygon || reg.boundary_polygon.length < 3) return;

      const hierarchy = reg.boundary_polygon.map((p: any) =>
        Cesium.Cartesian3.fromDegrees(p.longitude, p.latitude, 0.0, MARS_ELLIPSOID),
      );

      const polygonEntity = viewerInstance.entities.add({
        id: `discovered-region-${reg.region_id || idx}`,
        polygon: {
          hierarchy: hierarchy,
          material: Cesium.Color.fromCssColorString('#a855f7').withAlpha(0.22),
          outline: true,
          outlineColor: Cesium.Color.fromCssColorString('#c084fc'),
          outlineWidth: 2,
          heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
        },
      });
      newEntities.push(polygonEntity);

      // Center annotation label
      const labelEntity = viewerInstance.entities.add({
        id: `discovered-region-label-${reg.region_id || idx}`,
        position: Cesium.Cartesian3.fromDegrees(reg.center_longitude, reg.center_latitude, 500.0, MARS_ELLIPSOID),
        label: {
          text: `${reg.name}\n(${reg.surface_area_km2} km²)`,
          font: '10px monospace',
          fillColor: Cesium.Color.fromCssColorString('#f3e8ff'),
          outlineColor: Cesium.Color.BLACK,
          outlineWidth: 2,
          style: Cesium.LabelStyle.FILL_AND_OUTLINE,
          pixelOffset: new Cesium.Cartesian2(0, -10),
        },
      });
      newEntities.push(labelEntity);
    });

    regionEntitiesRef.current = newEntities;
    viewerInstance.scene.requestRender();
  }, [viewerInstance, activeDiscoveredRegions]);

  // Measurement tool rendering (distance and polygon area).
  useEffect(() => {
    if (!viewerInstance || viewerInstance.isDestroyed()) return;

    // Clear previous measurement entities
    measurementEntitiesRef.current.forEach((entity) => {
      viewerInstance.entities.remove(entity);
    });
    measurementEntitiesRef.current = [];

    if (measurementToolActive === 'none' || measurementPoints.length === 0) {
      viewerInstance.scene.requestRender();
      return;
    }

    const newEntities: Cesium.Entity[] = [];

    // Render vertex pins & elevation labels
    measurementPoints.forEach((pt, idx) => {
      const pin = viewerInstance.entities.add({
        id: `measurement-vertex-${idx}`,
        position: Cesium.Cartesian3.fromDegrees(pt.lon, pt.lat, Math.max(pt.elevation_m, 0) + 120.0, MARS_ELLIPSOID),
        point: {
          pixelSize: 8,
          color: Cesium.Color.fromCssColorString('#3d8dbf'),
          outlineColor: Cesium.Color.WHITE,
          outlineWidth: 2,
        },
        label: {
          text: `V${idx + 1}: ${Math.round(pt.elevation_m)}m`,
          font: 'bold 10px monospace',
          fillColor: Cesium.Color.fromCssColorString('#7fb3d4'),
          outlineColor: Cesium.Color.BLACK,
          outlineWidth: 2,
          style: Cesium.LabelStyle.FILL_AND_OUTLINE,
          pixelOffset: new Cesium.Cartesian2(0, -14),
        },
      });
      newEntities.push(pin);
    });

    // Render Geodesic Polyline connecting vertices
    if (measurementPoints.length >= 2) {
      const positions = measurementPoints.map((p) =>
        Cesium.Cartesian3.fromDegrees(p.lon, p.lat, Math.max(p.elevation_m, 0) + 60.0, MARS_ELLIPSOID),
      );

      const polylineEntity = viewerInstance.entities.add({
        id: 'measurement-geodesic-line',
        polyline: {
          positions: positions,
          width: 3.5,
          material: new Cesium.PolylineGlowMaterialProperty({
            glowPower: 0.25,
            color: Cesium.Color.fromCssColorString('#3d8dbf'),
          }),
          arcType: Cesium.ArcType.GEODESIC,
          clampToGround: true,
        },
      });
      newEntities.push(polylineEntity);
    }

    // Render Clamped Polygon if in Area Mode with >= 3 vertices
    if (measurementToolActive === 'area' && measurementPoints.length >= 3) {
      const hierarchy = measurementPoints.map((p) => Cesium.Cartesian3.fromDegrees(p.lon, p.lat, 0.0, MARS_ELLIPSOID));

      const polygonEntity = viewerInstance.entities.add({
        id: 'measurement-area-polygon',
        polygon: {
          hierarchy: hierarchy,
          material: Cesium.Color.fromCssColorString('#3d8dbf').withAlpha(0.2),
          outline: true,
          outlineColor: Cesium.Color.fromCssColorString('#7fb3d4'),
          outlineWidth: 2,
          heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
        },
      });
      newEntities.push(polygonEntity);
    }

    measurementEntitiesRef.current = newEntities;
    viewerInstance.scene.requestRender();
  }, [viewerInstance, measurementToolActive, measurementPoints]);

  // Viewer Initialization
  useEffect(() => {
    if (!containerRef.current) return;

    try {
      const viewer = initializeMarsViewer(containerRef.current);
      viewerRef.current = viewer;
      (window as any).viewer = viewer;
      (window as any).Cesium = Cesium;

      // -------------------------------------------------------------
      // Multi-resolution imagery layers.
      // Order: Viking MDIM 2.1 (Base) -> CTX (Regional) -> HiRISE (Local) -> MOLA Colormap (Optional)
      // -------------------------------------------------------------
      // Tier 1: Viking MDIM 2.1 Natural Color Basemap (Zoom 0-10)
      const vikingProvider = createVikingImageryProvider();
      const vikingLayer = viewer.imageryLayers.addImageryProvider(vikingProvider);
      (vikingLayer as any).zuhuraLayerId = 'zuhura-viking-mdim21';
      vikingLayer.minificationFilter = Cesium.TextureMinificationFilter.LINEAR;
      vikingLayer.magnificationFilter = Cesium.TextureMagnificationFilter.LINEAR;
      vikingImageryLayerRef.current = vikingLayer;

      // Tier 2: CTX Regional Context Imagery (Zoom 9-15, Jezero Footprint)
      const ctxProvider = createCtxImageryProvider();
      const ctxLayer = viewer.imageryLayers.addImageryProvider(ctxProvider);
      (ctxLayer as any).zuhuraLayerId = 'zuhura-ctx-jezero';
      ctxLayer.minificationFilter = Cesium.TextureMinificationFilter.LINEAR;
      ctxLayer.magnificationFilter = Cesium.TextureMagnificationFilter.LINEAR;
      ctxImageryLayerRef.current = ctxLayer;

      // Tier 3: HiRISE Targeted High-Resolution Imagery (Zoom 13-18, Perseverance Ellipse)
      const hiriseProvider = createHiRiseImageryProvider();
      const hiriseLayer = viewer.imageryLayers.addImageryProvider(hiriseProvider);
      (hiriseLayer as any).zuhuraLayerId = 'zuhura-hirise-jezero';
      hiriseLayer.minificationFilter = Cesium.TextureMinificationFilter.LINEAR;
      hiriseLayer.magnificationFilter = Cesium.TextureMagnificationFilter.LINEAR;
      hiriseImageryLayerRef.current = hiriseLayer;

      // Tier 4: MOLA MEG128 Scientific Topographic Colormap (Zoom 0-7, Hidden by default)
      const molaProvider = createMolaColormapImageryProvider();
      const molaLayer = viewer.imageryLayers.addImageryProvider(molaProvider);
      (molaLayer as any).zuhuraLayerId = 'zuhura-mola-global-v3-cog';
      molaLayer.minificationFilter = Cesium.TextureMinificationFilter.LINEAR;
      molaLayer.magnificationFilter = Cesium.TextureMagnificationFilter.LINEAR;
      molaLayer.show = false; // Optional visualization layer; Viking is natural default
      molaImageryLayerRef.current = molaLayer;

      // Tier 5: MGS MOLA + MEX HRSC Blended Color Hillshade (Zoom 0-9)
      const molaHrscProvider = createMolaHrscBlendImageryProvider();
      const molaHrscLayer = viewer.imageryLayers.addImageryProvider(molaHrscProvider);
      (molaHrscLayer as any).zuhuraLayerId = 'zuhura-mola-hrsc-blend';
      molaHrscLayer.show = false;
      molaHrscImageryLayerRef.current = molaHrscLayer;

      // Tier 6: THEMIS-IR Daytime Global Radiance Mosaic (Zoom 0-9)
      const themisDayProvider = createThemisDayIrImageryProvider();
      const themisDayLayer = viewer.imageryLayers.addImageryProvider(themisDayProvider);
      (themisDayLayer as any).zuhuraLayerId = 'zuhura-themis-day-ir';
      themisDayLayer.show = false;
      themisDayIrImageryLayerRef.current = themisDayLayer;

      // Tier 7: MGS TES Clinopyroxene Mineralogy (Zoom 0-6)
      const tesProvider = createTesClinopyroxeneImageryProvider();
      const tesLayer = viewer.imageryLayers.addImageryProvider(tesProvider);
      (tesLayer as any).zuhuraLayerId = 'zuhura-tes-clinopyroxene';
      tesLayer.show = false;
      tesImageryLayerRef.current = tesLayer;

      // Camera change listener
      viewer.camera.changed.addEventListener(() => {
        const cartographic = viewer.camera.positionCartographic;
        if (cartographic) {
          const lat = Cesium.Math.toDegrees(cartographic.latitude);
          const lon = Cesium.Math.toDegrees(cartographic.longitude);
          const alt = cartographic.height;
          setCameraPosition(lat, lon, alt);
        }
        const heading = Cesium.Math.toDegrees(viewer.camera.heading);
        const pitch = Cesium.Math.toDegrees(viewer.camera.pitch);
        const roll = Cesium.Math.toDegrees(viewer.camera.roll);
        setCameraOrientation(heading, pitch, roll);
      });

      // Tile loading progress listener
      viewer.scene.globe.tileLoadProgressEvent.addEventListener((queueLength: number) => {
        setTilesLoadingMetrics(queueLength, false);
      });

      const canvas = viewer.scene.canvas;
      const onContextLost = (event: Event) => {
        event.preventDefault();
        setLoadError(
          'WebGL context lost. The Cesium Mars globe stopped rendering. Reload the viewer to create a new context.',
        );
      };
      canvas.addEventListener('webglcontextlost', onContextLost, false);

      // Mouse move coordinate tracking
      const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
      handler.setInputAction((movement: { endPosition: Cesium.Cartesian2 }) => {
        const ray = viewer.camera.getPickRay(movement.endPosition);
        if (ray) {
          const cartesian = viewer.scene.globe.pick(ray, viewer.scene);
          if (cartesian) {
            const carto = MARS_ELLIPSOID.cartesianToCartographic(cartesian);
            if (carto) {
              const lat = Cesium.Math.toDegrees(carto.latitude);
              const lon = Cesium.Math.toDegrees(carto.longitude);
              setCursorPosition(lat, lon, carto.height);
            }
          }
        }
      }, Cesium.ScreenSpaceEventType.MOUSE_MOVE);

      // Left click: measurement points, traverse start/end, landmarks
      handler.setInputAction((click: { position: Cesium.Cartesian2 }) => {
        // 0. If in Geodesic Measurement Mode, handle vertex placement
        if (measurementToolActiveRef.current !== 'none') {
          const ray = viewer.camera.getPickRay(click.position);
          if (ray) {
            const cartesian = viewer.scene.globe.pick(ray, viewer.scene);
            if (cartesian) {
              const carto = MARS_ELLIPSOID.cartesianToCartographic(cartesian);
              if (carto) {
                const lat = Cesium.Math.toDegrees(carto.latitude);
                const lon = Cesium.Math.toDegrees(carto.longitude);
                const elev = carto.height;
                addMeasurementPointRef.current({ lat, lon, elevation_m: elev });
                return;
              }
            }
          }
        }

        // Traverse planner: the panel asked for a start or destination point.
        const pickTarget = routePickTargetRef.current;
        if (pickTarget) {
          const ray = viewer.camera.getPickRay(click.position);
          const cartesian = ray && viewer.scene.globe.pick(ray, viewer.scene);
          const carto = cartesian && MARS_ELLIPSOID.cartesianToCartographic(cartesian);
          if (carto) {
            const lat = Cesium.Math.toDegrees(carto.latitude);
            const lon = Cesium.Math.toDegrees(carto.longitude);
            const point = {
              lat,
              lon,
              name: getHoverPlaceDescription(lat, lon, carto.height).name,
              elevation_m: carto.height,
            };
            if (pickTarget === 'start') setDeparturePoint(point);
            else setArrivalPoint(point);
            setRoutePickTarget(null);
          }
          return;
        }

        const picked = viewer.scene.pick(click.position);
        if (Cesium.defined(picked) && picked.id) {
          const id = picked.id.id;
          if (id === 'jezero-pin') {
            setSelectedTerrain('jezero');
            setSelectedFeature(LANDMARK_FEATURES['jezero']);
          } else if (id === 'gale-pin') {
            setSelectedTerrain('gale');
            setSelectedFeature(LANDMARK_FEATURES['gale']);
            setIsMountSharpModalOpen(true);
          } else if (typeof id === 'string' && id.startsWith('ms-')) {
            setSelectedTerrain('gale');
            setIsMountSharpModalOpen(true);
          } else if (id === 'jezero-pin') {
            setSelectedTerrain('jezero');
            setSelectedFeature(LANDMARK_FEATURES['jezero']);
            setIsRoverRawImagesOpen(true);
          } else if (id === 'valles-pin') {
            setSelectedTerrain('valles_marineris');
            setSelectedFeature(LANDMARK_FEATURES['valles_marineris']);
          } else if (id === 'olympus-pin') {
            setSelectedTerrain('olympus_mons');
            setSelectedFeature(LANDMARK_FEATURES['olympus_mons']);
          }
        }
      }, Cesium.ScreenSpaceEventType.LEFT_CLICK);

      // Landmark Billboards
      const landmarks = [
        { id: 'jezero-pin', name: 'Jezero Crater (Perseverance)', lon: 77.58, lat: 18.38, color: '#e07a5f' },
        { id: 'gale-pin', name: 'Gale Crater (Curiosity)', lon: 137.44, lat: -4.59, color: '#f4a261' },
        { id: 'valles-pin', name: 'Valles Marineris (Chasmata)', lon: 283.0, lat: -9.5, color: '#2a9d8f' },
        { id: 'olympus-pin', name: 'Olympus Mons (+21.2 km Peak)', lon: 226.2, lat: 18.65, color: '#e76f51' },
      ];

      const landmarkEntities: Cesium.Entity[] = [];
      for (const lm of landmarks) {
        const entity = viewer.entities.add({
          id: lm.id,
          position: Cesium.Cartesian3.fromDegrees(lm.lon, lm.lat, 1000.0, MARS_ELLIPSOID),
          point: {
            pixelSize: 9,
            color: Cesium.Color.fromCssColorString(lm.color),
            outlineColor: Cesium.Color.WHITE,
            outlineWidth: 2,
          },
          label: {
            text: lm.name,
            font: '11px sans-serif',
            fillColor: Cesium.Color.WHITE,
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 2,
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
            pixelOffset: new Cesium.Cartesian2(0, -9),
          },
        });
        landmarkEntities.push(entity);
      }
      landmarkEntitiesRef.current = landmarkEntities;

      // Mount Sharp (Aeolis Mons) Curiosity Exploration Route (PIA23179)
      const mountSharpUnits = [
        { id: 'ms-bradbury', name: 'Bradbury Landing (-4501m)', lon: 137.4416, lat: -4.5895 },
        { id: 'ms-yellowknife', name: 'Yellowknife Bay (-4520m)', lon: 137.4489, lat: -4.5904 },
        { id: 'ms-verarubin', name: 'Vera Rubin Hematite Ridge (-4200m)', lon: 137.382, lat: -4.685 },
        { id: 'ms-glentorridon', name: 'Glen Torridon Smectite Clays (-4150m)', lon: 137.391, lat: -4.712 },
        { id: 'ms-greenheugh', name: 'Greenheugh Sandstone Pediment (-4000m)', lon: 137.375, lat: -4.735 },
        { id: 'ms-sulfate', name: 'Sulfate Hydrated Salts (-3850m)', lon: 137.388, lat: -4.76 },
        { id: 'ms-gediz', name: 'Gediz Vallis Debris Flow (-3700m)', lon: 137.405, lat: -4.778 },
      ];

      const msEntities: Cesium.Entity[] = [];
      const msPositions: Cesium.Cartesian3[] = [];

      for (const u of mountSharpUnits) {
        const pos = Cesium.Cartesian3.fromDegrees(u.lon, u.lat, 200.0, MARS_ELLIPSOID);
        msPositions.push(pos);
        const pin = viewer.entities.add({
          id: u.id,
          position: pos,
          point: {
            pixelSize: 7,
            color: Cesium.Color.GOLD,
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 1.5,
          },
          label: {
            text: u.name,
            font: '10px monospace',
            fillColor: Cesium.Color.GOLD,
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 2,
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
            pixelOffset: new Cesium.Cartesian2(0, -7),
            distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0.0, 150000.0),
          },
        });
        msEntities.push(pin);
      }

      const msLine = viewer.entities.add({
        id: 'ms-traverse-polyline',
        polyline: {
          positions: msPositions,
          width: 3.0,
          material: new Cesium.PolylineGlowMaterialProperty({
            glowPower: 0.25,
            color: Cesium.Color.GOLD,
          }),
        },
      });
      msEntities.push(msLine);
      mountSharpEntitiesRef.current = msEntities;

      // Add Scientific Dataset Footprint Boundaries over Jezero
      // 1. THEMIS Calibrated Infrared Corridor (100 m/px)
      const themisEntity = viewer.entities.add({
        id: 'themis-overlay',
        name: 'THEMIS Daytime IR (100 m/px, 12.57 µm)',
        show: false,
        polygon: {
          hierarchy: Cesium.Cartesian3.fromDegreesArray(
            [76.815, 24.494, 78.507, 12.485, 77.952, 12.452, 76.207, 24.458],
            MARS_ELLIPSOID,
          ),
          material: Cesium.Color.CYAN.withAlpha(0.2),
          outline: true,
          outlineColor: Cesium.Color.CYAN,
          outlineWidth: 2,
        },
      });
      scientificEntitiesRef.current.set('themis', themisEntity);

      // 2. CTX Western Delta Mosaic Swath Boundary (5.55 m/px)
      const ctxEntity = viewer.entities.add({
        id: 'ctx-overlay',
        name: 'MRO CTX Western Delta Mosaic Footprint (5.55 m/px)',
        show: true,
        polygon: {
          hierarchy: Cesium.Cartesian3.fromDegreesArray(
            [77.53, 18.654, 77.62, 17.9408, 77.13, 17.8814, 77.04, 18.5946],
            MARS_ELLIPSOID,
          ),
          material: Cesium.Color.GOLD.withAlpha(0.08),
          outline: true,
          outlineColor: Cesium.Color.GOLD,
          outlineWidth: 2,
        },
      });
      scientificEntitiesRef.current.set('ctx', ctxEntity);

      // 3. HiRISE Perseverance Touchdown Footprint Boundary (0.50 m/px)
      const hiriseEntity = viewer.entities.add({
        id: 'hirise-overlay',
        name: 'MRO HiRISE Perseverance Touchdown Footprint (0.50 m/px)',
        show: true,
        rectangle: {
          coordinates: Cesium.Rectangle.fromDegrees(77.5158, 18.2876, 77.6537, 18.5834),
          material: Cesium.Color.RED.withAlpha(0.08),
          outline: true,
          outlineColor: Cesium.Color.RED,
          outlineWidth: 2,
        },
      });
      scientificEntitiesRef.current.set('hirise', hiriseEntity);

      setViewerInstance(viewer);

      return () => {
        canvas.removeEventListener('webglcontextlost', onContextLost, false);
        handler.destroy();
        if (!viewer.isDestroyed()) {
          viewer.destroy();
        }
      };
    } catch (err: any) {
      console.warn('Cesium initialization notice:', err);
      setLoadError(err.message || 'WebGL initialization notice');
    }
  }, [setCameraPosition, setCursorPosition, setSelectedTerrain, setSelectedFeature]);

  // Fly camera when selectedFeature changes (e.g. from AI Scientist recommendations)
  useEffect(() => {
    if (viewerInstance && selectedFeature && !viewerInstance.isDestroyed()) {
      try {
        const ellipsoid = viewerInstance.scene.globe.ellipsoid;
        const targetAlt = Math.max(80000.0, (selectedFeature.diameter_km || 100) * 8000.0);
        viewerInstance.camera.flyTo({
          destination: Cesium.Cartesian3.fromDegrees(
            selectedFeature.longitude,
            selectedFeature.latitude,
            targetAlt,
            ellipsoid,
          ),
          duration: 2.0,
        });
      } catch (e) {
        console.warn('Camera flyTo feature notice:', e);
      }
    }
  }, [viewerInstance, selectedFeature]);

  // EVA planner layers and route state.
  const [tacticalConfig, setTacticalConfig] = useState<TacticalLayerConfig>(DEFAULT_TACTICAL_CONFIG);
  const evaEntitiesRef = useRef<Cesium.Entity[]>([]);
  const evaRouteEntitiesRef = useRef<Cesium.Entity[]>([]);
  const astronautMarkerRef = useRef<Cesium.Entity | null>(null);

  // Synchronize Tier 5 Tactical Entities when ARES-HUD is open or config changes
  useEffect(() => {
    if (!viewerInstance || viewerInstance.isDestroyed()) return;

    if (isAresHudOpen) {
      evaEntitiesRef.current = syncTacticalCesiumEntities(
        viewerInstance,
        tacticalConfig,
        evaEntitiesRef.current,
        (targetId) => {
          setActiveEvaTargetId(targetId);
        },
      );
    } else {
      // Clear tactical entities when HUD closed
      evaEntitiesRef.current.forEach((entity) => {
        try {
          viewerInstance.entities.remove(entity);
        } catch (e) {}
      });
      evaEntitiesRef.current = [];

      // Clear route entities
      evaRouteEntitiesRef.current.forEach((entity) => {
        try {
          viewerInstance.entities.remove(entity);
        } catch (e) {}
      });
      evaRouteEntitiesRef.current = [];

      // Clear astronaut marker
      if (astronautMarkerRef.current) {
        try {
          viewerInstance.entities.remove(astronautMarkerRef.current);
        } catch (e) {}
        astronautMarkerRef.current = null;
      }
    }
  }, [viewerInstance, isAresHudOpen, tacticalConfig, setActiveEvaTargetId]);

  // Fly to Jezero Crater HiRISE footprint when ARES-HUD opens
  const hasFlownToEvaRef = useRef<boolean>(false);
  useEffect(() => {
    if (isAresHudOpen && viewerInstance && !viewerInstance.isDestroyed() && !hasFlownToEvaRef.current) {
      hasFlownToEvaRef.current = true;
      try {
        viewerInstance.camera.flyTo({
          destination: Cesium.Cartesian3.fromDegrees(
            JEZERO_HAB_COORDINATES.longitude,
            JEZERO_HAB_COORDINATES.latitude,
            18000.0,
            MARS_ELLIPSOID,
          ),
          orientation: {
            heading: Cesium.Math.toRadians(290.0),
            pitch: Cesium.Math.toRadians(-55.0),
            roll: 0.0,
          },
          duration: 2.0,
        });
      } catch (e) {
        console.warn('EVA initial flyTo notice:', e);
      }
    }
    if (!isAresHudOpen) {
      hasFlownToEvaRef.current = false;
    }
  }, [isAresHudOpen, viewerInstance]);

  // Handle route planning and rendering
  const handleEvaRoutePlanned = useCallback(
    (route: EvaRoutePlan) => {
      if (!viewerInstance || viewerInstance.isDestroyed()) return;
      // Clean up previous route entities
      evaRouteEntitiesRef.current.forEach((entity) => {
        try {
          viewerInstance.entities.remove(entity);
        } catch (e) {}
      });
      evaRouteEntitiesRef.current = createEvaRouteEntities(viewerInstance, route);
    },
    [viewerInstance],
  );

  // Handle simulation step
  const handleEvaSimulationStep = useCallback(
    (currentPos: EvaPoint, progressFrac: number) => {
      if (!viewerInstance || viewerInstance.isDestroyed()) return;
      const remainingO2 = Math.max(0, Math.round(100 - progressFrac * 40));
      const remainingBat = Math.max(0, Math.round(100 - progressFrac * 35));

      astronautMarkerRef.current = updateAstronautMarker(
        viewerInstance,
        currentPos,
        remainingO2,
        remainingBat,
        astronautMarkerRef.current,
      );

      // In Visor POV mode, move camera with astronaut
      if (isVisorPovActive) {
        viewerInstance.camera.setView({
          destination: Cesium.Cartesian3.fromDegrees(
            currentPos.longitude,
            currentPos.latitude,
            (currentPos.elevation_m || -2560.0) + 1.75,
            MARS_ELLIPSOID,
          ),
          orientation: {
            heading: Cesium.Math.toRadians(cameraHeading || 285.0),
            pitch: Cesium.Math.toRadians(-5.0),
            roll: 0.0,
          },
        });
      }
    },
    [viewerInstance, isVisorPovActive, cameraHeading],
  );

  // Handle Visor POV Toggle
  const handleVisorPovToggle = useCallback(
    (active: boolean) => {
      setIsVisorPovActive(active);
      if (!viewerInstance || viewerInstance.isDestroyed()) return;

      if (active) {
        viewerInstance.camera.flyTo({
          destination: Cesium.Cartesian3.fromDegrees(
            JEZERO_HAB_COORDINATES.longitude,
            JEZERO_HAB_COORDINATES.latitude,
            JEZERO_HAB_COORDINATES.elevation_m + 1.75,
            MARS_ELLIPSOID,
          ),
          orientation: {
            heading: Cesium.Math.toRadians(285.0),
            pitch: Cesium.Math.toRadians(-5.0),
            roll: 0.0,
          },
          duration: 1.5,
        });
      } else {
        viewerInstance.camera.flyTo({
          destination: Cesium.Cartesian3.fromDegrees(
            JEZERO_HAB_COORDINATES.longitude,
            JEZERO_HAB_COORDINATES.latitude,
            18000.0,
            MARS_ELLIPSOID,
          ),
          orientation: {
            heading: Cesium.Math.toRadians(290.0),
            pitch: Cesium.Math.toRadians(-55.0),
            roll: 0.0,
          },
          duration: 1.5,
        });
      }
    },
    [viewerInstance, setIsVisorPovActive],
  );

  return (
    <div className={`relative w-full h-full bg-white ${routePickTarget ? 'cursor-crosshair' : ''}`}>
      <div ref={containerRef} className="w-full h-full" />


      {/* Compass */}
      <CompassOrientationHUD />

      {/* First-person surface walk */}
      <SurfaceExplorationHUD />

      {/* Measurement tool */}
      <GlobeMeasurementHUD />

      {/* Layer comparison slider */}
      <ImagerySplitSwipeHUD />

      {/* Tile loading status */}
      <TileLoadingProgressHUD />

      {/* EVA planner overlay */}
      <AresHudOverlay
        isOpen={isAresHudOpen}
        onClose={() => setIsAresHudOpen(false)}
        tacticalConfig={tacticalConfig}
        onTacticalConfigChange={setTacticalConfig}
        onRoutePlanned={handleEvaRoutePlanned}
        onSimulationStep={handleEvaSimulationStep}
        onVisorPovToggle={handleVisorPovToggle}
        isVisorPovActive={isVisorPovActive}
        cameraHeading={cameraHeading}
        cameraPitch={cameraPitch}
      />

      {loadError && (
        <div className="absolute inset-0 flex items-center justify-center bg-white p-6 text-center">
          <div className="max-w-md p-6 bg-surface-subtle rounded-lg border border-line">
            <h2 className="text-brand-700 font-semibold mb-2">The globe could not be displayed</h2>
            <p className="text-xs text-ink-soft mb-4">{loadError}</p>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="mb-3 px-3 py-1.5 rounded bg-brand-700 hover:bg-brand-800 text-xs font-medium text-white"
            >
              Reload globe
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
