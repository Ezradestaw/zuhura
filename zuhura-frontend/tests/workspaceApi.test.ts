import { describe, it, expect, vi, beforeEach } from 'vitest';
import { INITIAL_BOOKMARKS, useWorkspaceStore } from '../src/store/workspaceStore';
import {
  fetchStudyWorkspaces,
  fetchStudyObservations,
  addStudyObservation,
  fetchStudyHypotheses,
  addStudyHypothesis,
  fetchStudyActivity,
  exportStudyPackageManifest,
  exportKmlTraverse,
  fetchLatexTable,
} from '../src/lib/advancedApiClient';

describe('Workspace API client', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    useWorkspaceStore.setState({
      bookmarks: INITIAL_BOOKMARKS,
      annotations: [],
      measurementsHistory: [],
      activeStudyId: 'study_jezero_astrobiology',
      activeTab: 'studies',
      measurementToolActive: 'none',
      measurementPoints: [],
    });
  });

  describe('Workspace Store Operations', () => {
    it('initializes with default active study and tabs', () => {
      const state = useWorkspaceStore.getState();
      expect(state.activeStudyId).toBe('study_jezero_astrobiology');
      expect(state.activeTab).toBe('studies');
      expect(state.bookmarks.length).toBeGreaterThanOrEqual(3);
      expect(state.measurementToolActive).toBe('none');
    });

    it('updates active study and tab correctly', () => {
      const store = useWorkspaceStore.getState();
      store.setActiveStudyId('study_olympus_lavatubes');
      store.setActiveTab('hypotheses');

      const updated = useWorkspaceStore.getState();
      expect(updated.activeStudyId).toBe('study_olympus_lavatubes');
      expect(updated.activeTab).toBe('hypotheses');
    });

    it('adds and removes research bookmarks with IAU 2015 coordinates', () => {
      const store = useWorkspaceStore.getState();
      const initialCount = store.bookmarks.length;

      store.addBookmark({
        name: 'Mawrth Vallis Clays',
        lat: 23.99,
        lon: 341.04,
        elevation_m: -2240,
        geological_context: 'Phyllosilicate-rich stratigraphy',
        tags: ['Clay', 'Mawrth', 'Noachian'],
      });

      const updated = useWorkspaceStore.getState();
      expect(updated.bookmarks.length).toBe(initialCount + 1);
      const added = updated.bookmarks.find((b) => b.name === 'Mawrth Vallis Clays');
      expect(added).toBeDefined();
      expect(added?.lat).toBe(23.99);

      if (added) {
        store.removeBookmark(added.id);
        const afterDelete = useWorkspaceStore.getState();
        expect(afterDelete.bookmarks.length).toBe(initialCount);
      }
    });

    it('toggles geodesic measurement tools and handles points', () => {
      const store = useWorkspaceStore.getState();
      store.setMeasurementToolActive('ruler');
      expect(useWorkspaceStore.getState().measurementToolActive).toBe('ruler');

      store.addMeasurementPoint({ lat: 18.38, lon: 77.58, elevation_m: -2500 });
      store.addMeasurementPoint({ lat: 18.42, lon: 77.48, elevation_m: -2530 });
      expect(useWorkspaceStore.getState().measurementPoints.length).toBe(2);

      store.clearMeasurementPoints();
      expect(useWorkspaceStore.getState().measurementPoints.length).toBe(0);

      store.setMeasurementToolActive('none');
      expect(useWorkspaceStore.getState().measurementToolActive).toBe('none');
    });
  });

  describe('Scientific Workspace API Client', () => {
    it('fetches collaborative study workspaces', async () => {
      const mockStudies = [
        {
          study_id: 'study_jezero_astrobiology',
          name: 'Jezero Delta Astrobiology & Biosignature Survey',
          description: 'Investigation of deltaic bottomset beds',
          lead_investigator: 'Dr. Elena Vance / Mars 2020 Science Team',
          target_region: 'Jezero Crater, Nili Fossae',
          target_latitude: 18.38,
          target_longitude: 77.58,
          active_layers: ['viking_mdim21', 'ctx_global'],
          date_created: '2026-10-15',
          date_modified: '2026-11-13',
          status: 'ACTIVE',
          observations_count: 4,
          hypotheses_count: 2,
        },
      ];

      vi.spyOn(global, 'fetch').mockResolvedValueOnce({
        ok: true,
        json: async () => mockStudies,
      } as Response);

      const studies = await fetchStudyWorkspaces();
      expect(studies.length).toBe(1);
      expect(studies[0].study_id).toBe('study_jezero_astrobiology');
      expect(studies[0].status).toBe('ACTIVE');
      expect(studies[0].target_latitude).toBe(18.38);
    });

    it('fetches and creates scientific observations with PDS references', async () => {
      const mockObs = {
        obs_id: 'obs_101',
        study_id: 'study_jezero_astrobiology',
        timestamp: '2026-11-13 14:00 UTC',
        latitude: 18.44,
        longitude: 77.45,
        elevation_m: -2530.0,
        observation_type: 'MINERALOGY',
        title: 'Smectite Clay Peak at Belva Scarp',
        notes: '2.3 micron CRISM absorption verified.',
        tags: ['CRISM', 'Smectite', 'Belva'],
        epistemic_classification: 'MEASURED',
        attached_data_products: ['urn:nasa:pds:crism_mtrdr:frt00003e12_07'],
        uncertainty_m: 0.8,
      };

      vi.spyOn(global, 'fetch').mockResolvedValueOnce({
        ok: true,
        json: async () => [mockObs],
      } as Response);

      const list = await fetchStudyObservations('study_jezero_astrobiology');
      expect(list.length).toBe(1);
      expect(list[0].epistemic_classification).toBe('MEASURED');

      vi.spyOn(global, 'fetch').mockResolvedValueOnce({
        ok: true,
        json: async () => mockObs,
      } as Response);

      const created = await addStudyObservation('study_jezero_astrobiology', mockObs);
      expect(created.obs_id).toBe('obs_101');
      expect(created.observation_type).toBe('MINERALOGY');
    });

    it('fetches and creates scientific hypotheses with falsification criteria', async () => {
      const mockHyp = {
        hypothesis_id: 'hyp_201',
        study_id: 'study_jezero_astrobiology',
        statement: 'Bottomset mudstones preserve intact biosignatures',
        status: 'HYPOTHESIZED' as const,
        confidence_rating: 0.85,
        linked_evidence_ids: ['obs_101'],
        competing_hypotheses: ['Complete UV photolysis'],
        falsification_criteria: 'Zero Raman fluorescence in core',
        date_formulated: '2026-11-13',
        date_updated: '2026-11-13',
      };

      vi.spyOn(global, 'fetch').mockResolvedValueOnce({
        ok: true,
        json: async () => [mockHyp],
      } as Response);

      const hyps = await fetchStudyHypotheses('study_jezero_astrobiology');
      expect(hyps.length).toBe(1);
      expect(hyps[0].confidence_rating).toBe(0.85);
      expect(hyps[0].falsification_criteria).toContain('Raman fluorescence');

      vi.spyOn(global, 'fetch').mockResolvedValueOnce({
        ok: true,
        json: async () => mockHyp,
      } as Response);

      const added = await addStudyHypothesis('study_jezero_astrobiology', mockHyp);
      expect(added.hypothesis_id).toBe('hyp_201');
    });

    it('fetches team collaboration activity stream', async () => {
      const mockActivities = [
        {
          activity_id: 'act_001',
          study_id: 'study_jezero_astrobiology',
          author: 'Dr. Elena Vance',
          action_type: 'HYPOTHESIS_UPDATE',
          content: 'Updated Hypothesis HYP-001 to SUPPORTED status',
          timestamp: '2026-11-13 10:15 UTC',
        },
      ];

      vi.spyOn(global, 'fetch').mockResolvedValueOnce({
        ok: true,
        json: async () => mockActivities,
      } as Response);

      const activities = await fetchStudyActivity('study_jezero_astrobiology');
      expect(activities.length).toBe(1);
      expect(activities[0].action_type).toBe('HYPOTHESIS_UPDATE');
    });

    it('exports study package manifest and OGC KML 2.3 traverse', async () => {
      const mockManifest = {
        study_manifest: {
          study_id: 'study_jezero_astrobiology',
          title: 'Jezero Delta Astrobiology',
          description: 'Survey',
          lead_investigator: 'Dr. Vance',
          target_region: 'Jezero',
          target_coordinates: { lat: 18.38, lon: 77.58 },
          status: 'ACTIVE',
          export_date_utc: '2026-11-13 15:00:00 UTC',
          total_observations: 2,
          total_hypotheses: 1,
        },
        observations: [],
        hypotheses: [],
        geojson: { type: 'FeatureCollection', features: [] },
        scientific_provenance: { epistemic_classification: 'OBSERVED_AND_DERIVED' },
        citation: 'Dr. Vance (2026). Jezero Delta Astrobiology.',
      };

      vi.spyOn(global, 'fetch').mockResolvedValueOnce({
        ok: true,
        json: async () => mockManifest,
      } as Response);

      const manifest = await exportStudyPackageManifest('study_jezero_astrobiology');
      expect(manifest.study_manifest.study_id).toBe('study_jezero_astrobiology');
      expect(manifest.geojson.type).toBe('FeatureCollection');
      expect(manifest.citation).toContain('Dr. Vance');

      const mockKml =
        '<?xml version="1.0"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Traverse</name></Document></kml>';
      vi.spyOn(global, 'fetch').mockResolvedValueOnce({
        ok: true,
        text: async () => mockKml,
      } as Response);

      const kml = await exportKmlTraverse('Traverse', [{ latitude: 18.38, longitude: 77.58, elevation_m: -2500 }]);
      expect(kml).toContain('<kml xmlns=');
      expect(kml).toContain('<Document>');
    });

    it('generates AGU/PSJ publication-ready LaTeX tables', async () => {
      const mockLatexResponse = {
        table_type: 'crater_morphometry',
        latex: '\\begin{table}[htbp]\n\\centering\n\\caption{Morphometric Parameters}\n\\end{table}',
      };

      vi.spyOn(global, 'fetch').mockResolvedValueOnce({
        ok: true,
        json: async () => mockLatexResponse,
      } as Response);

      const res = await fetchLatexTable('crater_morphometry');
      expect(res.table_type).toBe('crater_morphometry');
      expect(res.latex).toContain('\\begin{table}');
      expect(res.latex).toContain('\\end{table}');
    });
  });
});
