/**
 * Zuhura Frontend - Scientific Terrain Intelligence Zustand Store
 * Holds reactive state for transect profiling, point morphometry, and analysis tools.
 */

import { create } from 'zustand';
import {
  Coordinate,
  TerrainProfileResult,
  PointAnalysisResult,
  fetchTerrainProfile,
} from '../lib/terrainApiClient';

interface TerrainAnalysisState {
  // Transect Profiler
  isTransectMode: boolean;
  transectStart: Coordinate | null;
  transectEnd: Coordinate | null;
  profileData: TerrainProfileResult | null;
  isLoadingProfile: boolean;
  profileError: string | null;
  hoveredSampleIndex: number | null;
  sampleCount: number;

  // Selected Point Analysis
  pointAnalysisData: PointAnalysisResult | null;
  isLoadingPoint: boolean;

  // Actions
  setIsTransectMode: (enabled: boolean) => void;
  setTransectStart: (coord: Coordinate | null) => void;
  setTransectEnd: (coord: Coordinate | null) => void;
  setSampleCount: (count: number) => void;
  setHoveredSampleIndex: (idx: number | null) => void;
  setPointAnalysisData: (data: PointAnalysisResult | null) => void;
  setIsLoadingPoint: (loading: boolean) => void;
  setProfileData: (data: TerrainProfileResult | null) => void;
  resetTransect: () => void;
  executeTransectQuery: () => Promise<void>;
}

export const useTerrainAnalysisStore = create<TerrainAnalysisState>((set, get) => ({
  isTransectMode: false,
  transectStart: { latitude: 18.25, longitude: 77.35 },
  transectEnd: { latitude: 18.50, longitude: 77.80 },
  profileData: null,
  isLoadingProfile: false,
  profileError: null,
  hoveredSampleIndex: null,
  sampleCount: 50,

  pointAnalysisData: null,
  isLoadingPoint: false,

  setIsTransectMode: (enabled) => set({ isTransectMode: enabled }),
  setTransectStart: (coord) => set({ transectStart: coord }),
  setTransectEnd: (coord) => set({ transectEnd: coord }),
  setSampleCount: (count) => set({ sampleCount: count }),
  setHoveredSampleIndex: (idx) => set({ hoveredSampleIndex: idx }),
  setPointAnalysisData: (data) => set({ pointAnalysisData: data }),
  setIsLoadingPoint: (loading) => set({ isLoadingPoint: loading }),
  setProfileData: (data) => set({ profileData: data }),

  resetTransect: () =>
    set({
      transectStart: null,
      transectEnd: null,
      profileData: null,
      profileError: null,
      hoveredSampleIndex: null,
    }),

  executeTransectQuery: async () => {
    const { transectStart, transectEnd, sampleCount } = get();
    if (!transectStart || !transectEnd) return;

    try {
      set({ isLoadingProfile: true, profileError: null });
      const data = await fetchTerrainProfile(transectStart, transectEnd, sampleCount, true);
      set({ profileData: data, isLoadingProfile: false });
    } catch (err: any) {
      set({
        isLoadingProfile: false,
        profileError: err.message || 'Transect extraction failed',
      });
    }
  },
}));
