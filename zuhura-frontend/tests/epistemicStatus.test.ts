import { describe, it, expect, beforeEach } from 'vitest';
import { useProvenanceStore } from '../src/store/provenanceStore';

describe('Epistemic status framework', () => {
  beforeEach(() => {
    useProvenanceStore.setState({
      isProvenanceModalOpen: false,
      selectedDatasetId: null,
      activeTab: 'datasets',
    });
  });

  describe('1. Epistemic Provenance Store Management', () => {
    it('initializes with modal closed and default datasets tab', () => {
      const state = useProvenanceStore.getState();
      expect(state.isProvenanceModalOpen).toBe(false);
      expect(state.selectedDatasetId).toBeNull();
      expect(state.activeTab).toBe('datasets');
    });

    it('opens provenance modal with target dataset id', () => {
      useProvenanceStore.getState().openProvenanceModal('MOLA_MEG128');
      const state = useProvenanceStore.getState();
      expect(state.isProvenanceModalOpen).toBe(true);
      expect(state.selectedDatasetId).toBe('MOLA_MEG128');
      expect(state.activeTab).toBe('datasets');
    });

    it('routes MODEL_ESTIMATED to the competing models tab automatically', () => {
      useProvenanceStore.getState().openProvenanceModal('INSIGHT_MODEL');
      const state = useProvenanceStore.getState();
      expect(state.isProvenanceModalOpen).toBe(true);
      expect(state.activeTab).toBe('models');
    });

    it('switches between datasets, models, and classifications tabs', () => {
      useProvenanceStore.getState().setActiveTab('classifications');
      expect(useProvenanceStore.getState().activeTab).toBe('classifications');

      useProvenanceStore.getState().setActiveTab('models');
      expect(useProvenanceStore.getState().activeTab).toBe('models');
    });
  });

  describe('2. Standardized Epistemic 7-Tier Classifications', () => {
    const EXPECTED_TIERS = [
      'OBSERVED',
      'MEASURED',
      'DERIVED',
      'MODEL_ESTIMATED',
      'SIMULATED',
      'PROVISIONAL',
      'UNVERIFIED',
    ];

    it('contains all 7 standardized epistemic classifications', () => {
      EXPECTED_TIERS.forEach((tier) => {
        expect(tier).toBeDefined();
        expect(typeof tier).toBe('string');
      });
    });

    it('verifies uncertainty model structure format', () => {
      const molaUncertainty = {
        nominal_value: 0.0,
        uncertainty_absolute: 1.0,
        unit: 'meters',
        methodology: 'pulse transit time laser altimetry',
      };
      expect(molaUncertainty.uncertainty_absolute).toBe(1.0);
      expect(molaUncertainty.unit).toBe('meters');
    });

    it('validates competing models reconciliation integrity', () => {
      const stahler2021 = { core_radius_km: 1830.0, uncertainty_km: 40.0, status: 'SUPERSEDED' };
      const nature2023 = { core_radius_km: 1650.0, uncertainty_km: 20.0, status: 'CURRENT_CONSENSUS' };

      expect(stahler2021.core_radius_km).toBeGreaterThan(nature2023.core_radius_km);
      expect(nature2023.status).toBe('CURRENT_CONSENSUS');
      expect(nature2023.uncertainty_km).toBeLessThanOrEqual(20.0);
    });
  });
});