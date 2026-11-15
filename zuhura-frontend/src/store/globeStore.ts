import { create } from 'zustand';

export interface PlanetaryFeature {
  id: string;
  name: string;
  type: string;
  latitude: number;
  longitude: number;
  diameter_km: number;
  elevation_m: number;
  description: string;
}

export interface RoutePoint {
  lat: number;
  lon: number;
  name: string;
  elevation_m: number;
}

interface GlobeState {
  cameraLat: number;
  cameraLon: number;
  cameraAlt: number;
  cursorLat: number | null;
  cursorLon: number | null;
  cursorElevation: number | null;
  selectedFeature: PlanetaryFeature | null;
  selectedTerrain: string;
  enableLighting: boolean;
  solarAzimuth: number;
  solarElevation: number;
  // Advanced Planetary Feature Modes
  isRoutePlannerOpen: boolean;
  isPinpointOpen: boolean;
  isRegionDiscoveryOpen: boolean;
  isVisualIntelligenceOpen: boolean;
  isPlaceNamesVisible: boolean;
  isRoverRawImagesOpen: boolean;
  isMountSharpModalOpen: boolean;
  isDatasetExplorerOpen: boolean;
  selectedMountSharpUnit: string | null;
  // EVA planner
  isAresHudOpen: boolean;
  isVisorPovActive: boolean;
  activeEvaTargetId: string | null;
  activeNavigationRoute: any | null;
  activeDiscoveredRegions: any[];
  // Traverse planner: start/destination picked on the globe
  routePickTarget: 'start' | 'end' | null;
  departurePoint: RoutePoint | null;
  arrivalPoint: RoutePoint | null;
  // Camera orientation
  cameraHeading: number;
  cameraPitch: number;
  cameraRoll: number;
  // Surface Walk (First-person ground exploration)
  isSurfaceWalkActive: boolean;
  surfaceWalkSpeed: number;
  // Split-Screen Swipe Comparison
  isSplitScreenActive: boolean;
  splitPosition: number;
  splitLeftLayerId: string;
  splitRightLayerId: string;
  // Tile Loading Progress & Health
  tilesLoadingCount: number;
  isTileLoadError: boolean;
  // Help
  isMissionBriefingOpen: boolean;
  isLayerPanelCollapsed: boolean;
  setCameraPosition: (lat: number, lon: number, alt: number) => void;
  setCameraOrientation: (heading: number, pitch: number, roll: number) => void;
  setCursorPosition: (lat: number | null, lon: number | null, elevation: number | null) => void;
  setSelectedFeature: (feature: PlanetaryFeature | null) => void;
  setSelectedTerrain: (terrain: string) => void;
  setEnableLighting: (enabled: boolean) => void;
  setSolarLighting: (azimuth: number, elevation: number) => void;
  setIsRoutePlannerOpen: (open: boolean) => void;
  setIsPinpointOpen: (open: boolean) => void;
  setIsRegionDiscoveryOpen: (open: boolean) => void;
  setIsVisualIntelligenceOpen: (open: boolean) => void;
  setIsPlaceNamesVisible: (visible: boolean) => void;
  setIsRoverRawImagesOpen: (open: boolean) => void;
  setIsMountSharpModalOpen: (open: boolean) => void;
  setIsDatasetExplorerOpen: (open: boolean) => void;
  setSelectedMountSharpUnit: (unit: string | null) => void;
  setIsAresHudOpen: (open: boolean) => void;
  setIsVisorPovActive: (active: boolean) => void;
  setActiveEvaTargetId: (targetId: string | null) => void;
  setActiveNavigationRoute: (route: any | null) => void;
  setActiveDiscoveredRegions: (regions: any[]) => void;
  setRoutePickTarget: (target: 'start' | 'end' | null) => void;
  setDeparturePoint: (point: RoutePoint | null) => void;
  setArrivalPoint: (point: RoutePoint | null) => void;
  setIsSurfaceWalkActive: (active: boolean) => void;
  setSurfaceWalkSpeed: (speed: number) => void;
  setIsSplitScreenActive: (active: boolean) => void;
  setSplitPosition: (pos: number) => void;
  setSplitLayers: (leftId: string, rightId: string) => void;
  setTilesLoadingMetrics: (count: number, hasError: boolean) => void;
  setIsMissionBriefingOpen: (open: boolean) => void;
  setIsLayerPanelCollapsed: (collapsed: boolean) => void;
}

export const useGlobeStore = create<GlobeState>((set) => ({
  cameraLat: 18.44,
  cameraLon: 77.45,
  cameraAlt: 1200000.0,
  cursorLat: 18.44,
  cursorLon: 77.45,
  cursorElevation: -2560.0,
  selectedFeature: null,
  selectedTerrain: 'global',
  enableLighting: false,
  solarAzimuth: 315.0,
  solarElevation: 45.0,
  isRoutePlannerOpen: false,
  isPinpointOpen: false,
  isRegionDiscoveryOpen: false,
  isVisualIntelligenceOpen: false,
  isPlaceNamesVisible: true,
  isRoverRawImagesOpen: false,
  isMountSharpModalOpen: false,
  isDatasetExplorerOpen: false,
  selectedMountSharpUnit: null,
  isAresHudOpen: false,
  isVisorPovActive: false,
  activeEvaTargetId: null,
  activeNavigationRoute: null,
  activeDiscoveredRegions: [],
  routePickTarget: null,
  departurePoint: null,
  arrivalPoint: null,
  cameraHeading: 0.0,
  cameraPitch: -90.0,
  cameraRoll: 0.0,
  isSurfaceWalkActive: false,
  surfaceWalkSpeed: 2.5,
  isSplitScreenActive: false,
  splitPosition: 0.5,
  splitLeftLayerId: 'zuhura-viking-mdim21',
  splitRightLayerId: 'zuhura-ctx-jezero',
  tilesLoadingCount: 0,
  isTileLoadError: false,
  isMissionBriefingOpen: false,
  isLayerPanelCollapsed: true,
  setCameraPosition: (lat, lon, alt) => set({ cameraLat: lat, cameraLon: lon, cameraAlt: alt }),
  setCameraOrientation: (heading, pitch, roll) => set({ cameraHeading: heading, cameraPitch: pitch, cameraRoll: roll }),
  setCursorPosition: (lat, lon, elevation) => set({ cursorLat: lat, cursorLon: lon, cursorElevation: elevation }),
  setSelectedFeature: (feature) => set({ selectedFeature: feature }),
  setSelectedTerrain: (terrain) => set({ selectedTerrain: terrain }),
  setEnableLighting: (enabled) => set({ enableLighting: enabled }),
  setSolarLighting: (azimuth, elevation) => set({ solarAzimuth: azimuth, solarElevation: elevation }),
  setIsRoutePlannerOpen: (open) => set({ isRoutePlannerOpen: open }),
  setIsPinpointOpen: (open) => set({ isPinpointOpen: open }),
  setIsRegionDiscoveryOpen: (open) => set({ isRegionDiscoveryOpen: open }),
  setIsVisualIntelligenceOpen: (open) => set({ isVisualIntelligenceOpen: open }),
  setIsPlaceNamesVisible: (visible) => set({ isPlaceNamesVisible: visible }),
  setIsRoverRawImagesOpen: (open) => set({ isRoverRawImagesOpen: open }),
  setIsMountSharpModalOpen: (open) => set({ isMountSharpModalOpen: open }),
  setIsDatasetExplorerOpen: (open) => set({ isDatasetExplorerOpen: open }),
  setSelectedMountSharpUnit: (unit) => set({ selectedMountSharpUnit: unit }),
  setIsAresHudOpen: (open) => set({ isAresHudOpen: open }),
  setIsVisorPovActive: (active) => set({ isVisorPovActive: active }),
  setActiveEvaTargetId: (targetId) => set({ activeEvaTargetId: targetId }),
  setActiveNavigationRoute: (route) => set({ activeNavigationRoute: route }),
  setActiveDiscoveredRegions: (regions) => set({ activeDiscoveredRegions: regions }),
  setRoutePickTarget: (target) => set({ routePickTarget: target }),
  setDeparturePoint: (point) => set({ departurePoint: point }),
  setArrivalPoint: (point) => set({ arrivalPoint: point }),
  setIsSurfaceWalkActive: (active) => set({ isSurfaceWalkActive: active }),
  setSurfaceWalkSpeed: (speed) => set({ surfaceWalkSpeed: speed }),
  setIsSplitScreenActive: (active) => set({ isSplitScreenActive: active }),
  setSplitPosition: (pos) => set({ splitPosition: pos }),
  setSplitLayers: (leftId, rightId) => set({ splitLeftLayerId: leftId, splitRightLayerId: rightId }),
  setTilesLoadingMetrics: (count, hasError) => set({ tilesLoadingCount: count, isTileLoadError: hasError }),
  setIsMissionBriefingOpen: (open) => set({ isMissionBriefingOpen: open }),
  setIsLayerPanelCollapsed: (collapsed) => set({ isLayerPanelCollapsed: collapsed }),
}));
