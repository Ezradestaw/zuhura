import { create } from 'zustand';

interface ProvenanceState {
  isProvenanceModalOpen: boolean;
  selectedDatasetId: string | null;
  activeTab: 'datasets' | 'models' | 'classifications';
  setIsProvenanceModalOpen: (open: boolean) => void;
  setSelectedDatasetId: (id: string | null) => void;
  setActiveTab: (tab: 'datasets' | 'models' | 'classifications') => void;
  openProvenanceModal: (datasetId?: string) => void;
}

export const useProvenanceStore = create<ProvenanceState>((set) => ({
  isProvenanceModalOpen: false,
  selectedDatasetId: null,
  activeTab: 'datasets',
  setIsProvenanceModalOpen: (open) => set({ isProvenanceModalOpen: open }),
  setSelectedDatasetId: (id) => set({ selectedDatasetId: id }),
  setActiveTab: (tab) => set({ activeTab: tab }),
  openProvenanceModal: (datasetId) =>
    set({
      isProvenanceModalOpen: true,
      selectedDatasetId: datasetId || 'MOLA',
      activeTab: datasetId?.includes('MODEL') ? 'models' : 'datasets',
    }),
}));
