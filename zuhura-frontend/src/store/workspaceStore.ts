import { create } from 'zustand';
import { createJSONStorage, persist, type StateStorage } from 'zustand/middleware';

export interface ResearchBookmark {
  id: string;
  name: string;
  lat: number;
  lon: number;
  elevation_m: number;
  date_saved: string;
  geological_context: string;
  tags: string[];
}

export interface GeologicalAnnotation {
  id: string;
  title: string;
  notes: string;
  lat: number;
  lon: number;
  elevation_m: number;
  geologic_era: string; // "Noachian", "Hesperian", "Amazonian"
  epistemic_classification: string;
  date_created: string;
}

export interface GeodesicMeasurement {
  id: string;
  mode: 'distance' | 'area';
  points: { lat: number; lon: number; elevation_m: number }[];
  result_value: number; // km or km^2
  elevation_delta_m: number;
  timestamp: string;
}

export type WorkspaceTabType =
  | 'studies'
  | 'observations'
  | 'hypotheses'
  | 'bookmarks'
  | 'annotations'
  | 'measurements'
  | 'export';

interface WorkspaceState {
  isWorkspaceOpen: boolean;
  activeStudyId: string;
  activeTab: WorkspaceTabType;
  measurementToolActive: 'none' | 'ruler' | 'area';
  measurementPoints: { lat: number; lon: number; elevation_m: number }[];
  bookmarks: ResearchBookmark[];
  annotations: GeologicalAnnotation[];
  measurementsHistory: GeodesicMeasurement[];
  setIsWorkspaceOpen: (open: boolean) => void;
  setActiveStudyId: (id: string) => void;
  setActiveTab: (tab: WorkspaceTabType) => void;
  setMeasurementToolActive: (tool: 'none' | 'ruler' | 'area') => void;
  addMeasurementPoint: (pt: { lat: number; lon: number; elevation_m: number }) => void;
  clearMeasurementPoints: () => void;
  addBookmark: (bookmark: Omit<ResearchBookmark, 'id' | 'date_saved'>) => void;
  removeBookmark: (id: string) => void;
  addAnnotation: (annotation: Omit<GeologicalAnnotation, 'id' | 'date_created'>) => void;
  removeAnnotation: (id: string) => void;
  saveMeasurement: (m: Omit<GeodesicMeasurement, 'id' | 'timestamp'>) => void;
}

export const WORKSPACE_STORAGE_KEY = 'zuhura-researcher-workspace';

const memoryStorage = new Map<string, string>();

function workspaceStateStorage(): StateStorage {
  if (typeof localStorage !== 'undefined') {
    return localStorage;
  }
  return {
    getItem: (name) => memoryStorage.get(name) ?? null,
    setItem: (name, value) => {
      memoryStorage.set(name, value);
    },
    removeItem: (name) => {
      memoryStorage.delete(name);
    },
  };
}

export function readPersistedWorkspaceRaw(): string | null {
  const stored = workspaceStateStorage().getItem(WORKSPACE_STORAGE_KEY);
  return typeof stored === 'string' ? stored : null;
}

// Initial seed bookmarks for prominent Martian landing and scientific sites
export const INITIAL_BOOKMARKS: ResearchBookmark[] = [
  {
    id: "bm-jezero-delta",
    name: "Jezero Crater Western Delta",
    lat: 18.44,
    lon: 77.45,
    elevation_m: -2530,
    date_saved: "2026-11-13",
    geological_context: "Mars 2020 Perseverance landing site; ancient lacustrine delta facies",
    tags: ["Perseverance", "Delta", "Sedimentary"]
  },
  {
    id: "bm-gale-mtsharp",
    name: "Gale Crater - Mount Sharp",
    lat: -4.68,
    lon: 137.38,
    elevation_m: -4120,
    date_saved: "2026-11-13",
    geological_context: "MSL Curiosity rover traverse; sulfate and smectite clay facies",
    tags: ["Curiosity", "Sulfate", "Clay"]
  },
  {
    id: "bm-olympus-mons",
    name: "Olympus Mons Central Caldera",
    lat: 18.65,
    lon: 226.20,
    elevation_m: 21287,
    date_saved: "2026-11-13",
    geological_context: "Solar system's tallest volcano; collapsed basaltic calderas",
    tags: ["Volcano", "Shield", "Caldera"]
  }
];

export const useWorkspaceStore = create<WorkspaceState>()(
  persist(
    (set) => ({
  isWorkspaceOpen: false,
  activeStudyId: 'study_jezero_astrobiology',
  activeTab: 'studies',
  measurementToolActive: 'none',
  measurementPoints: [],
  bookmarks: INITIAL_BOOKMARKS,
  annotations: [],
  measurementsHistory: [],
  setIsWorkspaceOpen: (open) => set({ isWorkspaceOpen: open }),
  setActiveStudyId: (id) => set({ activeStudyId: id }),
  setActiveTab: (tab) => set({ activeTab: tab }),
  setMeasurementToolActive: (tool) => set({
    measurementToolActive: tool,
    measurementPoints: []
  }),
  addMeasurementPoint: (pt) => set((state) => ({
    measurementPoints: [...state.measurementPoints, pt]
  })),
  clearMeasurementPoints: () => set({ measurementPoints: [] }),
  addBookmark: (bm) => set((state) => ({
    bookmarks: [
      ...state.bookmarks,
      {
        ...bm,
        id: `bm-${Date.now()}`,
        date_saved: new Date().toISOString().split('T')[0]
      }
    ]
  })),
  removeBookmark: (id) => set((state) => ({
    bookmarks: state.bookmarks.filter((b) => b.id !== id)
  })),
  addAnnotation: (ann) => set((state) => ({
    annotations: [
      ...state.annotations,
      {
        ...ann,
        id: `ann-${Date.now()}`,
        date_created: new Date().toISOString().split('T')[0]
      }
    ]
  })),
  removeAnnotation: (id) => set((state) => ({
    annotations: state.annotations.filter((a) => a.id !== id)
  })),
  saveMeasurement: (m) => set((state) => ({
    measurementsHistory: [
      ...state.measurementsHistory,
      {
        ...m,
        id: `meas-${Date.now()}`,
        timestamp: new Date().toISOString()
      }
    ]
  })),
    }),
    {
      name: WORKSPACE_STORAGE_KEY,
      storage: createJSONStorage(workspaceStateStorage),
      partialize: (state) => ({
        bookmarks: state.bookmarks,
        annotations: state.annotations,
        measurementsHistory: state.measurementsHistory,
      }),
    },
  ),
);
