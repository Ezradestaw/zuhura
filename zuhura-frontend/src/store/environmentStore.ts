import { create } from 'zustand';
import {
  MartianSitePreset,
  MissionEnvironmentAssessmentData,
  fetchEnvironmentPresets,
  fetchMissionEnvironmentAssessment,
} from '../lib/advancedApiClient';

export type EnvironmentTab = 'overview' | 'atmosphere' | 'dust' | 'thermal' | 'power' | 'viability';

interface EnvironmentState {
  isEnvironmentModalOpen: boolean;
  setIsEnvironmentModalOpen: (open: boolean) => void;
  activeTab: EnvironmentTab;
  setActiveTab: (tab: EnvironmentTab) => void;

  // Planetary Parameters
  selectedLs: number;
  setSelectedLs: (ls: number) => void;
  targetName: string;
  targetLat: number;
  targetLon: number;
  targetElevation: number;
  thermalInertia: number;
  panelArea: number;
  globalDustMultiplier: number;

  setTargetLocation: (name: string, lat: number, lon: number, elev: number, ti?: number) => void;
  setThermalInertia: (ti: number) => void;
  setPanelArea: (area: number) => void;
  setGlobalDustMultiplier: (multiplier: number) => void;

  presets: MartianSitePreset[];
  setPresets: (presets: MartianSitePreset[]) => void;
  loadPresets: () => Promise<void>;
  applyPreset: (presetId: string) => void;

  assessment: MissionEnvironmentAssessmentData | null;
  setAssessment: (assessment: MissionEnvironmentAssessmentData | null) => void;
  runAssessment: () => Promise<void>;

  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  error: string | null;
  setError: (error: string | null) => void;
}

export const useEnvironmentStore = create<EnvironmentState>((set, get) => ({
  isEnvironmentModalOpen: false,
  setIsEnvironmentModalOpen: (open) => set({ isEnvironmentModalOpen: open }),
  activeTab: 'overview',
  setActiveTab: (tab) => set({ activeTab: tab }),

  selectedLs: 180.0, // Default to Southern Spring / Perihelion approach
  setSelectedLs: (ls) => {
    set({ selectedLs: (ls + 360) % 360 });
    // Trigger recalculation if already loaded
    if (get().assessment) {
      get().runAssessment();
    }
  },

  targetName: 'Jezero Crater (Perseverance Touchdown)',
  targetLat: 18.38,
  targetLon: 77.58,
  targetElevation: -2500.0,
  thermalInertia: 360.0,
  panelArea: 1.3,
  globalDustMultiplier: 1.0,

  setTargetLocation: (name, lat, lon, elev, ti = 320.0) => {
    set({
      targetName: name,
      targetLat: lat,
      targetLon: lon,
      targetElevation: elev,
      thermalInertia: ti,
    });
    get().runAssessment();
  },

  setThermalInertia: (ti) => {
    set({ thermalInertia: ti });
    if (get().assessment) {
      get().runAssessment();
    }
  },

  setPanelArea: (area) => {
    set({ panelArea: area });
    if (get().assessment) {
      get().runAssessment();
    }
  },

  setGlobalDustMultiplier: (multiplier) => {
    set({ globalDustMultiplier: multiplier });
    if (get().assessment) {
      get().runAssessment();
    }
  },

  presets: [],
  setPresets: (presets) => set({ presets }),

  loadPresets: async () => {
    try {
      const res = await fetchEnvironmentPresets();
      if (res.status === 'success') {
        set({ presets: res.presets });
      }
    } catch (err: any) {
      console.warn('Could not load environmental presets:', err);
    }
  },

  applyPreset: (presetId) => {
    const preset = get().presets.find((p) => p.id === presetId);
    if (!preset) return;
    set({
      targetName: preset.name,
      targetLat: preset.latitude,
      targetLon: preset.longitude,
      targetElevation: preset.elevation_m,
      thermalInertia: preset.thermal_inertia_tiu,
    });
    get().runAssessment();
  },

  assessment: null,
  setAssessment: (assessment) => set({ assessment }),

  runAssessment: async () => {
    set({ isLoading: true, error: null });
    const s = get();
    try {
      const res = await fetchMissionEnvironmentAssessment({
        target_name: s.targetName,
        latitude: s.targetLat,
        longitude: s.targetLon,
        elevation_m: s.targetElevation,
        ls_deg: s.selectedLs,
        thermal_inertia_tiu: s.thermalInertia,
        panel_area_m2: s.panelArea,
      });
      if (res.status === 'success') {
        set({ assessment: res.assessment, isLoading: false });
      } else {
        set({ error: 'Assessment calculation returned non-success status', isLoading: false });
      }
    } catch (err: any) {
      set({ error: err.message || 'Failed to calculate environmental assessment', isLoading: false });
    }
  },

  isLoading: false,
  setIsLoading: (loading) => set({ isLoading: loading }),
  error: null,
  setError: (error) => set({ error }),
}));
