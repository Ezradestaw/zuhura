import { describe, it, expect, beforeEach } from 'vitest';
import { INITIAL_BOOKMARKS, readPersistedWorkspaceRaw, useWorkspaceStore } from '../src/store/workspaceStore';

describe('Researcher Scientific Workspace Store', () => {
  beforeEach(() => {
    useWorkspaceStore.setState({
      isWorkspaceOpen: false,
      bookmarks: INITIAL_BOOKMARKS,
      annotations: [],
      measurementsHistory: [],
      measurementToolActive: 'none',
      measurementPoints: [],
      activeStudyId: 'study_jezero_astrobiology',
      activeTab: 'studies',
    });
  });

  it('initializes with authoritative Martian research bookmarks', () => {
    const state = useWorkspaceStore.getState();
    expect(state.bookmarks.length).toBeGreaterThanOrEqual(3);
    const names = state.bookmarks.map((b) => b.name);
    expect(names.some((n) => n.includes('Jezero'))).toBe(true);
    expect(names.some((n) => n.includes('Gale'))).toBe(true);
    expect(names.some((n) => n.includes('Olympus'))).toBe(true);
  });

  it('adds and removes research bookmarks with coordinates and elevation', () => {
    const store = useWorkspaceStore.getState();
    const initialCount = store.bookmarks.length;

    store.addBookmark({
      name: 'Valles Marineris Chasma Wall',
      lat: -4.0,
      lon: 284.5,
      elevation_m: -3200,
      geological_context: 'Massive tectonic rift canyon outcrop',
      tags: ['Canyon', 'Tectonics'],
    });

    const updated = useWorkspaceStore.getState();
    expect(updated.bookmarks.length).toBe(initialCount + 1);
    const added = updated.bookmarks.find((b) => b.name === 'Valles Marineris Chasma Wall');
    expect(added).toBeDefined();
    expect(added?.lat).toBe(-4.0);
    expect(added?.elevation_m).toBe(-3200);

    // Remove bookmark
    if (added) {
      store.removeBookmark(added.id);
      expect(useWorkspaceStore.getState().bookmarks.length).toBe(initialCount);
    }
  });

  it('manages geological facies field annotations with epistemic certainty', async () => {
    const store = useWorkspaceStore.getState();
    store.addAnnotation({
      title: 'Kodiak Butte Bedset Boundary',
      notes: 'Cross-stratified deltaic foreset sandstone dipping south-southwest.',
      lat: 18.42,
      lon: 77.48,
      elevation_m: -2530,
      geologic_era: 'Noachian',
      epistemic_classification: 'OBSERVED',
    });

    const state = useWorkspaceStore.getState();
    expect(state.annotations.length).toBe(1);
    expect(state.annotations[0].geologic_era).toBe('Noachian');
    expect(state.annotations[0].epistemic_classification).toBe('OBSERVED');

    await new Promise((resolve) => setTimeout(resolve, 0));
    const persisted = readPersistedWorkspaceRaw();
    expect(persisted).toBeTruthy();
    expect(persisted).toContain('Kodiak Butte Bedset Boundary');
    expect(persisted).toContain('Jezero Crater Western Delta');
  });

  it('tracks geodesic measurement tools and history', () => {
    const store = useWorkspaceStore.getState();
    store.setMeasurementToolActive('ruler');
    expect(useWorkspaceStore.getState().measurementToolActive).toBe('ruler');

    store.addMeasurementPoint({ lat: 18.44, lon: 77.45, elevation_m: -2500 });
    store.addMeasurementPoint({ lat: 18.48, lon: 77.50, elevation_m: -2480 });

    expect(useWorkspaceStore.getState().measurementPoints.length).toBe(2);

    store.saveMeasurement({
      mode: 'distance',
      points: useWorkspaceStore.getState().measurementPoints,
      result_value: 5.2,
      elevation_delta_m: 20,
    });

    expect(useWorkspaceStore.getState().measurementsHistory.length).toBe(1);
    expect(useWorkspaceStore.getState().measurementsHistory[0].result_value).toBe(5.2);
  });
});
