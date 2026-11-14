import React, { useState, useEffect } from 'react';
import {
  Bookmark,
  FileText,
  Ruler,
  Download,
  X,
  Plus,
  Trash2,
  Navigation,
  Globe,
  Sparkles,
  Check,
  Copy,
  FolderKanban,
  User,
  MapPin,
  ShieldCheck,
} from 'lucide-react';
import { useWorkspaceStore } from '../store/workspaceStore';
import { useGlobeStore } from '../store/globeStore';
import { EpistemicBadge } from './EpistemicBadge';
import {
  StudyWorkspaceData,
  ScientificObservationData,
  ScientificHypothesisData,
  fetchStudyWorkspaces,
  fetchStudyObservations,
  addStudyObservation,
  fetchStudyHypotheses,
  addStudyHypothesis,
  exportStudyPackageManifest,
  exportKmlTraverse,
  fetchLatexTable,
} from '../lib/advancedApiClient';

export const ResearcherWorkspaceModal: React.FC = () => {
  const {
    isWorkspaceOpen,
    setIsWorkspaceOpen,
    activeStudyId,
    setActiveStudyId,
    activeTab,
    setActiveTab,
    bookmarks,
    addBookmark,
    removeBookmark,
    measurementToolActive,
    setMeasurementToolActive,
    measurementPoints,
    clearMeasurementPoints,
  } = useWorkspaceStore();

  const {
    cameraLat,
    cameraLon,
    cursorElevation,
    setCameraPosition,
  } = useGlobeStore();

  // Studies state
  const [studies, setStudies] = useState<StudyWorkspaceData[]>([]);
  const [observations, setObservations] = useState<ScientificObservationData[]>([]);
  const [hypotheses, setHypotheses] = useState<ScientificHypothesisData[]>([]);

  // LaTeX table state
  const [selectedLatexTable, setSelectedLatexTable] = useState<'crater_morphometry' | 'terramechanics'>('crater_morphometry');
  const [latexCode, setLatexCode] = useState<string>('');
  const [copiedLatex, setCopiedLatex] = useState<boolean>(false);

  // Form states for new observation
  const [newObsTitle, setNewObsTitle] = useState('');
  const [newObsNotes, setNewObsNotes] = useState('');
  const [newObsType, setNewObsType] = useState('GEOMORPHOLOGY');
  const [newObsEpistemic, setNewObsEpistemic] = useState('OBSERVED');
  const [newObsPds, setNewObsPds] = useState('');
  const [newObsTags, setNewObsTags] = useState('');

  // Form states for new hypothesis
  const [newHypStatement, setNewHypStatement] = useState('');
  const [newHypStatus, setNewHypStatus] = useState<'HYPOTHESIZED' | 'SUPPORTED' | 'CONTRADICTED'>('HYPOTHESIZED');
  const [newHypConfidence, setNewHypConfidence] = useState(0.75);
  const [newHypFalsification, setNewHypFalsification] = useState('');

  // Bookmarks form state
  const [bmName, setBmName] = useState('');
  const [bmContext, setBmContext] = useState('');
  const [bmTags, setBmTags] = useState('');

  // Load studies on open
  useEffect(() => {
    if (!isWorkspaceOpen) return;
    let isMounted = true;

    fetchStudyWorkspaces()
      .then((data) => {
        if (isMounted) setStudies(data);
      })
      .catch((err) => {
        console.warn('Failed to fetch studies, using default', err);
      });

    return () => {
      isMounted = false;
    };
  }, [isWorkspaceOpen]);

  // Load observations and hypotheses for the active study
  useEffect(() => {
    if (!isWorkspaceOpen || !activeStudyId) return;
    let isMounted = true;

    Promise.all([
      fetchStudyObservations(activeStudyId).catch(() => []),
      fetchStudyHypotheses(activeStudyId).catch(() => []),
    ]).then(([obsData, hypData]) => {
      if (isMounted) {
        setObservations(obsData);
        setHypotheses(hypData);
      }
    });

    return () => {
      isMounted = false;
    };
  }, [isWorkspaceOpen, activeStudyId]);

  // Load LaTeX snippet
  useEffect(() => {
    if (activeTab === 'export') {
      fetchLatexTable(selectedLatexTable)
        .then((res) => setLatexCode(res.latex))
        .catch(() => {});
    }
  }, [activeTab, selectedLatexTable]);

  if (!isWorkspaceOpen) return null;

  const currentStudy = studies.find((s) => s.study_id === activeStudyId) || studies[0];

  const handleFlyTo = (lat: number, lon: number) => {
    setCameraPosition(lat, lon, 250000.0);
    const viewer = (window as any).viewer;
    if (viewer && (window as any).Cesium) {
      const Cesium = (window as any).Cesium;
      viewer.camera.flyTo({
        destination: Cesium.Cartesian3.fromDegrees(lon, lat, 250000.0),
        duration: 2.0,
      });
    }
  };

  const handleCreateObservation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newObsTitle.trim()) return;

    try {
      const created = await addStudyObservation(activeStudyId, {
        latitude: Number(cameraLat.toFixed(4)),
        longitude: Number(cameraLon.toFixed(4)),
        elevation_m: Math.round(cursorElevation || -2500),
        observation_type: newObsType,
        title: newObsTitle.trim(),
        notes: newObsNotes.trim(),
        tags: newObsTags.split(',').map((t) => t.trim()).filter(Boolean),
        epistemic_classification: newObsEpistemic,
        attached_data_products: newObsPds.trim() ? [newObsPds.trim()] : [],
        uncertainty_m: 1.0,
      });
      setObservations((prev) => [created, ...prev]);
      setNewObsTitle('');
      setNewObsNotes('');
      setNewObsPds('');
      setNewObsTags('');
    } catch (err) {
      console.error('Failed to add observation:', err);
    }
  };

  const handleCreateHypothesis = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newHypStatement.trim()) return;

    try {
      const created = await addStudyHypothesis(activeStudyId, {
        statement: newHypStatement.trim(),
        status: newHypStatus,
        confidence_rating: Number(newHypConfidence),
        linked_evidence_ids: observations.slice(0, 2).map((o) => o.obs_id),
        competing_hypotheses: [],
        falsification_criteria: newHypFalsification.trim() || 'Falsified if no fine-grained stratified units are identified in cross-bedding facies.',
      });
      setHypotheses((prev) => [created, ...prev]);
      setNewHypStatement('');
      setNewHypFalsification('');
    } catch (err) {
      console.error('Failed to add hypothesis:', err);
    }
  };

  const handleDownloadManifest = async () => {
    try {
      const manifest = await exportStudyPackageManifest(activeStudyId);
      const blob = new Blob([JSON.stringify(manifest, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `zuhura_study_package_${activeStudyId}_${Date.now()}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to download study manifest:', err);
    }
  };

  const handleDownloadKML = async () => {
    try {
      const waypoints = [
        { latitude: currentStudy?.target_latitude || 18.38, longitude: currentStudy?.target_longitude || 77.58, elevation_m: -2500.0 },
        { latitude: (currentStudy?.target_latitude || 18.38) + 0.04, longitude: (currentStudy?.target_longitude || 77.58) - 0.08, elevation_m: -2530.0 },
      ];
      const kmlText = await exportKmlTraverse(`${currentStudy?.name || 'Martian'} Traverse`, waypoints);
      const blob = new Blob([kmlText], { type: 'application/vnd.google-earth.kml+xml' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `zuhura_traverse_${activeStudyId}.kml`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to export KML:', err);
    }
  };

  const handleCopyLatex = () => {
    if (!latexCode) return;
    navigator.clipboard.writeText(latexCode);
    setCopiedLatex(true);
    setTimeout(() => setCopiedLatex(false), 2000);
  };

  const handleCreateBookmark = (e: React.FormEvent) => {
    e.preventDefault();
    if (!bmName.trim()) return;
    addBookmark({
      name: bmName.trim(),
      lat: Number(cameraLat.toFixed(4)),
      lon: Number(cameraLon.toFixed(4)),
      elevation_m: Math.round(cursorElevation || 0),
      geological_context: bmContext.trim() || 'User saved Martian landmark observation',
      tags: bmTags.split(',').map((t) => t.trim()).filter(Boolean),
    });
    setBmName('');
    setBmContext('');
    setBmTags('');
  };

  const handleExportGeoJSON = () => {
    const features = bookmarks.map((b) => ({
      type: 'Feature',
      properties: {
        id: b.id,
        name: b.name,
        elevation_m: b.elevation_m,
        date_saved: b.date_saved,
        geological_context: b.geological_context,
        tags: b.tags,
      },
      geometry: {
        type: 'Point',
        coordinates: [b.lon, b.lat, b.elevation_m],
      },
    }));

    const geojson = {
      type: 'FeatureCollection',
      crs: {
        type: 'name',
        properties: { name: 'urn:ogc:def:crs:IAU2015:MARS:49900' },
      },
      provenance: {
        datum: 'Mars Areoid (MOLA GMM-3 equipotential zero)',
        classification: 'OBSERVED_AND_DERIVED',
        exported_at: new Date().toISOString(),
      },
      features,
    };

    const blob = new Blob([JSON.stringify(geojson, null, 2)], { type: 'application/geo+json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `zuhura_mars_research_bookmarks_${Date.now()}.geojson`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportCSV = () => {
    const headers = ['ID', 'Name', 'Latitude_Planetocentric', 'Longitude_East', 'Elevation_Areoid_m', 'Date_Saved', 'Context', 'Tags'];
    const rows = bookmarks.map((b) => [
      b.id,
      `"${b.name.replace(/"/g, '""')}"`,
      b.lat,
      b.lon,
      b.elevation_m,
      b.date_saved,
      `"${b.geological_context.replace(/"/g, '""')}"`,
      `"${b.tags.join('; ')}"`,
    ]);

    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `zuhura_mars_waypoints_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-brand-950/45 select-none font-sans">
      <div className="bg-surface-subtle border border-line rounded-3xl shadow-panel w-full max-w-5xl max-h-[92vh] flex flex-col text-ink overflow-hidden font-sans">
        
        {/* Header with Active Study Selector */}
        <div className="px-5 py-3.5 bg-white border-b border-line flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div>
              <p className="text-[12px] font-medium text-brand-600">Workspace</p>
              <h2 className="text-base font-semibold tracking-tight text-ink">
                Studies, notes, and saved places
              </h2>
              <div className="flex items-center space-x-2 text-[11px] text-ink-muted mt-0.5">
                <span>Active Study:</span>
                <select
                  value={activeStudyId}
                  onChange={(e) => setActiveStudyId(e.target.value)}
                  className="bg-white border border-line rounded px-2 py-0.5 text-ink text-[11px] focus:outline-none focus:border-brand-600"
                >
                  {studies.map((s) => (
                    <option key={s.study_id} value={s.study_id}>
                      {s.name} ({s.target_region})
                    </option>
                  ))}
                </select>
                {currentStudy && (
                  <button
                    onClick={() => handleFlyTo(currentStudy.target_latitude, currentStudy.target_longitude)}
                    className="flex items-center space-x-1 px-1.5 py-0.5 rounded bg-surface-muted hover:bg-brand-800 hover:text-white text-[10px] text-ink-soft transition-colors"
                    title="Center Viewport on Study Target"
                  >
                    <Navigation className="w-2.5 h-2.5" />
                    <span>Fly to Target</span>
                  </button>
                )}
              </div>
            </div>
          </div>
          <button
            onClick={() => setIsWorkspaceOpen(false)}
            className="p-1 rounded text-ink-muted hover:text-ink hover:bg-surface-muted transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-line bg-surface-muted px-4 pt-2 overflow-x-auto space-x-1 scrollbar-none">
          <button
            onClick={() => setActiveTab('studies')}
            className={`flex items-center space-x-1.5 px-3 py-2 text-xs font-medium border-b-2 whitespace-nowrap transition-all ${
              activeTab === 'studies'
                ? 'border-brand-600 text-ink font-semibold'
                : 'border-transparent text-ink-muted hover:text-ink'
            }`}
          >
            <Globe className="w-3.5 h-3.5" />
            <span>Studies ({studies.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('observations')}
            className={`flex items-center space-x-1.5 px-3 py-2 text-xs font-medium border-b-2 whitespace-nowrap transition-all ${
              activeTab === 'observations'
                ? 'border-brand-600 text-ink font-semibold'
                : 'border-transparent text-ink-muted hover:text-ink'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Observation Logbook ({observations.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('hypotheses')}
            className={`flex items-center space-x-1.5 px-3 py-2 text-xs font-medium border-b-2 whitespace-nowrap transition-all ${
              activeTab === 'hypotheses'
                ? 'border-brand-600 text-ink font-semibold'
                : 'border-transparent text-ink-muted hover:text-ink'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Hypothesis Tracker ({hypotheses.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('bookmarks')}
            className={`flex items-center space-x-1.5 px-3 py-2 text-xs font-medium border-b-2 whitespace-nowrap transition-all ${
              activeTab === 'bookmarks'
                ? 'border-brand-600 text-ink font-semibold'
                : 'border-transparent text-ink-muted hover:text-ink'
            }`}
          >
            <Bookmark className="w-3.5 h-3.5" />
            <span>Landmarks ({bookmarks.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('measurements')}
            className={`flex items-center space-x-1.5 px-3 py-2 text-xs font-medium border-b-2 whitespace-nowrap transition-all ${
              activeTab === 'measurements'
                ? 'border-brand-600 text-ink font-semibold'
                : 'border-transparent text-ink-muted hover:text-ink'
            }`}
          >
            <Ruler className="w-3.5 h-3.5" />
            <span>Geodesic Tools</span>
          </button>

          <button
            onClick={() => setActiveTab('export')}
            className={`flex items-center space-x-1.5 px-3 py-2 text-xs font-medium border-b-2 whitespace-nowrap transition-all ${
              activeTab === 'export'
                ? 'border-brand-600 text-ink font-semibold'
                : 'border-transparent text-ink-muted hover:text-ink'
            }`}
          >
            <Download className="w-3.5 h-3.5" />
            <span>Exports & Publications</span>
          </button>
        </div>

        {/* Tab Content Body */}
        <div className="flex-1 p-5 overflow-y-auto space-y-5 bg-surface-subtle">
          
          {/* TAB 1: STUDIES OVERVIEW */}
          {activeTab === 'studies' && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {studies.map((s) => {
                  const isActive = s.study_id === activeStudyId;
                  return (
                    <div
                      key={s.study_id}
                      className={`p-4 rounded-lg border transition-all flex flex-col justify-between ${
                        isActive
                          ? 'bg-surface-muted border-brand-600 shadow-sm'
                          : 'bg-surface-muted border-line hover:border-line'
                      }`}
                    >
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className={`text-[10px] px-2 py-0.5 rounded font-mono font-bold ${
                            s.status === 'ACTIVE'
                              ? 'bg-surface-subtle text-ink border border-line'
                              : 'bg-surface-muted text-ink-muted'
                          }`}>
                            {s.status}
                          </span>
                          <span className="text-[10px] text-ink-muted font-mono">
                            {s.target_latitude > 0 ? `${s.target_latitude}°N` : `${Math.abs(s.target_latitude)}°S`}, {s.target_longitude}°E
                          </span>
                        </div>
                        <h3 className="text-sm font-bold text-ink">{s.name}</h3>
                        <p className="text-[11px] text-ink-muted line-clamp-3">{s.description}</p>
                        
                        <div className="pt-2 text-[10px] text-ink-faint space-y-1">
                          <div className="flex items-center space-x-1">
                            <User className="w-3 h-3 text-ink-muted" />
                            <span className="text-ink-soft font-medium">{s.lead_investigator}</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <MapPin className="w-3 h-3 text-ink" />
                            <span className="text-ink-soft">{s.target_region}</span>
                          </div>
                          <div className="flex items-center space-x-3 pt-1">
                            <span className="text-ink font-mono">{s.observations_count} observations</span>
                            <span className="text-brand-600 font-mono">{s.hypotheses_count} hypotheses</span>
                          </div>
                        </div>
                      </div>

                      <div className="pt-3 mt-3 border-t border-line flex items-center space-x-2">
                        <button
                          onClick={() => setActiveStudyId(s.study_id)}
                          className={`flex-1 py-1.5 rounded text-xs font-semibold transition-colors ${
                            isActive
                              ? 'bg-surface-subtle text-ink border border-line cursor-default'
                              : 'bg-surface-muted hover:bg-surface-muted text-ink-soft'
                          }`}
                        >
                          {isActive ? 'Current Active' : 'Switch Study'}
                        </button>
                        <button
                          onClick={() => handleFlyTo(s.target_latitude, s.target_longitude)}
                          className="p-1.5 rounded bg-surface-muted hover:bg-brand-800 hover:text-white text-ink-soft transition-colors"
                          title="Fly Camera to Target"
                        >
                          <Navigation className="w-3.5 h-3.5 text-ink" />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* TAB 2: OBSERVATION LOGBOOK */}
          {activeTab === 'observations' && (
            <div className="space-y-4">
              {/* Form to log observation */}
              <form onSubmit={handleCreateObservation} className="p-4 rounded-lg bg-surface-muted border border-line space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-ink-soft flex items-center space-x-1.5">
                    <Plus className="w-3.5 h-3.5 text-ink" />
                    <span>Log Scientific Observation at Viewport ({cameraLat.toFixed(2)}°N, {cameraLon.toFixed(2)}°E)</span>
                  </span>
                  <span className="text-[11px] font-mono text-ink">
                    MOLA Elevation: {cursorElevation !== null ? `${cursorElevation.toFixed(0)} m` : '-2500 m'}
                  </span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  <input
                    type="text"
                    placeholder="Observation Title (e.g. Scarp Bedding Facies)"
                    value={newObsTitle}
                    onChange={(e) => setNewObsTitle(e.target.value)}
                    className="px-2.5 py-1.5 rounded bg-white border border-line text-xs text-ink placeholder-ink-faint focus:outline-none focus:border-brand-600"
                  />
                  <select
                    value={newObsType}
                    onChange={(e) => setNewObsType(e.target.value)}
                    className="px-2.5 py-1.5 rounded bg-white border border-line text-xs text-ink-soft focus:outline-none"
                  >
                    <option value="GEOMORPHOLOGY">GEOMORPHOLOGY</option>
                    <option value="MINERALOGY">MINERALOGY</option>
                    <option value="ATMOSPHERIC">ATMOSPHERIC</option>
                    <option value="MOBILITY_HAZARD">MOBILITY_HAZARD</option>
                    <option value="ASTROBIOLOGY">ASTROBIOLOGY</option>
                  </select>
                  <select
                    value={newObsEpistemic}
                    onChange={(e) => setNewObsEpistemic(e.target.value)}
                    className="px-2.5 py-1.5 rounded bg-white border border-line text-xs text-ink-soft focus:outline-none"
                  >
                    <option value="OBSERVED">OBSERVED (HiRISE/CTX Direct)</option>
                    <option value="MEASURED">MEASURED (CRISM / Spectrometry)</option>
                    <option value="DERIVED">DERIVED (Terramechanics Model)</option>
                    <option value="MODEL_ESTIMATED">MODEL_ESTIMATED (InSight)</option>
                  </select>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  <input
                    type="text"
                    placeholder="PDS Product URN (e.g. urn:nasa:pds:crism_mtrdr:frt00003e12_07)"
                    value={newObsPds}
                    onChange={(e) => setNewObsPds(e.target.value)}
                    className="px-2.5 py-1.5 rounded bg-white border border-line text-xs text-ink placeholder-ink-faint focus:outline-none focus:border-brand-600 font-mono"
                  />
                  <input
                    type="text"
                    placeholder="Tags (e.g. Clay, Stratigraphy, Delta)"
                    value={newObsTags}
                    onChange={(e) => setNewObsTags(e.target.value)}
                    className="px-2.5 py-1.5 rounded bg-white border border-line text-xs text-ink placeholder-ink-faint focus:outline-none focus:border-brand-600"
                  />
                </div>
                <textarea
                  placeholder="Detailed scientific observation notes, mineral signatures, and stratigraphic context..."
                  value={newObsNotes}
                  onChange={(e) => setNewObsNotes(e.target.value)}
                  rows={2}
                  className="w-full px-2.5 py-1.5 rounded bg-white border border-line text-xs text-ink placeholder-ink-faint focus:outline-none focus:border-brand-600"
                />
                <button
                  type="submit"
                  disabled={!newObsTitle.trim()}
                  className="px-3 py-1.5 rounded bg-brand-700 hover:bg-brand-800 disabled:opacity-40 text-xs font-semibold text-white transition-colors"
                >
                  Log Scientific Observation
                </button>
              </form>

              {/* Observations List */}
              <div className="space-y-3">
                {observations.length === 0 ? (
                  <div className="p-8 text-center text-xs text-ink-faint border border-dashed border-line rounded-lg">
                    No observations logged for this study yet. Use the form above to record geological or spectral observations.
                  </div>
                ) : (
                  observations.map((obs) => (
                    <div
                      key={obs.obs_id}
                      className="p-4 rounded-lg bg-surface-muted border border-line space-y-2.5"
                    >
                      <div className="flex items-start justify-between">
                        <div className="space-y-1">
                          <div className="flex items-center space-x-2">
                            <span className="text-xs font-bold text-ink">{obs.title}</span>
                            <span className="text-[10px] px-1.5 py-0.2 rounded bg-surface-subtle text-ink-soft font-mono">
                              {obs.observation_type}
                            </span>
                            <EpistemicBadge type={obs.epistemic_classification} compact />
                          </div>
                          <p className="text-xs text-ink-soft leading-relaxed">{obs.notes}</p>
                        </div>
                        <button
                          onClick={() => handleFlyTo(obs.latitude, obs.longitude)}
                          className="flex items-center space-x-1 px-2 py-1 rounded bg-surface-muted hover:bg-brand-800 hover:text-white text-[10px] text-ink-soft transition-colors whitespace-nowrap ml-3"
                        >
                          <Navigation className="w-2.5 h-2.5" />
                          <span>Fly To</span>
                        </button>
                      </div>

                      {obs.attached_data_products && obs.attached_data_products.length > 0 && (
                        <div className="p-2 rounded bg-white border border-line text-[10px] font-mono text-ink flex items-center justify-between">
                          <span className="truncate">PDS: {obs.attached_data_products[0]}</span>
                          <span className="text-ink-faint text-[9px]">PDS4 Verified</span>
                        </div>
                      )}

                      <div className="flex items-center justify-between pt-1 text-[10px] text-ink-faint font-mono">
                        <span>
                          Coords: {obs.latitude.toFixed(2)}°N, {obs.longitude.toFixed(2)}°E | MOLA: {obs.elevation_m.toLocaleString()} m (±{obs.uncertainty_m}m)
                        </span>
                        <span>{obs.timestamp}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* TAB 3: HYPOTHESIS TRACKER */}
          {activeTab === 'hypotheses' && (
            <div className="space-y-4">
              {/* Form to formulate hypothesis */}
              <form onSubmit={handleCreateHypothesis} className="p-4 rounded-lg bg-surface-muted border border-line space-y-3">
                <span className="text-xs font-semibold text-ink-soft flex items-center space-x-1.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-ink" />
                  <span>New hypothesis</span>
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  <div className="sm:col-span-2">
                    <input
                      type="text"
                      placeholder="Hypothesis Statement (e.g. Lacustrine bottomset beds preserve ancient biosignatures)"
                      value={newHypStatement}
                      onChange={(e) => setNewHypStatement(e.target.value)}
                      className="w-full px-2.5 py-1.5 rounded bg-white border border-line text-xs text-ink placeholder-ink-faint focus:outline-none focus:border-brand-600"
                    />
                  </div>
                  <div className="flex space-x-2">
                    <select
                      value={newHypStatus}
                      onChange={(e) => setNewHypStatus(e.target.value as any)}
                      className="flex-1 px-2.5 py-1.5 rounded bg-white border border-line text-xs text-ink-soft focus:outline-none"
                    >
                      <option value="HYPOTHESIZED">HYPOTHESIZED</option>
                      <option value="SUPPORTED">SUPPORTED</option>
                      <option value="CONTRADICTED">CONTRADICTED</option>
                    </select>
                    <input
                      type="number"
                      step="0.05"
                      min="0.0"
                      max="1.0"
                      value={newHypConfidence}
                      onChange={(e) => setNewHypConfidence(parseFloat(e.target.value))}
                      className="w-20 px-2.5 py-1.5 rounded bg-white border border-line text-xs text-ink font-mono text-center focus:outline-none"
                      title="Epistemic Confidence Rating (0.0 to 1.0)"
                    />
                  </div>
                </div>
                <input
                  type="text"
                  placeholder="Popperian Falsification Criteria (What scientific finding would disprove this?)"
                  value={newHypFalsification}
                  onChange={(e) => setNewHypFalsification(e.target.value)}
                  className="w-full px-2.5 py-1.5 rounded bg-white border border-line text-xs text-ink placeholder-ink-faint focus:outline-none focus:border-brand-600"
                />
                <button
                  type="submit"
                  disabled={!newHypStatement.trim()}
                  className="px-3 py-1.5 rounded bg-brand-700 hover:bg-brand-800 disabled:opacity-40 text-xs font-semibold text-white transition-colors"
                >
                  Record Scientific Hypothesis
                </button>
              </form>

              {/* Hypotheses List */}
              <div className="space-y-3">
                {hypotheses.length === 0 ? (
                  <div className="p-8 text-center text-xs text-ink-faint border border-dashed border-line rounded-lg">
                    No hypotheses formulated yet. Add a hypothesis statement and falsification criteria above.
                  </div>
                ) : (
                  hypotheses.map((hyp) => (
                    <div
                      key={hyp.hypothesis_id}
                      className="p-4 rounded-lg bg-surface-muted border border-line space-y-3"
                    >
                      <div className="flex items-start justify-between">
                        <div className="space-y-1.5 max-w-3xl">
                          <div className="flex items-center space-x-2">
                            <span className="text-[10px] text-ink-muted font-bold">{hyp.hypothesis_id}</span>
                            <span className={`text-[10px] px-2 py-0.5 rounded font-mono font-bold ${
                              hyp.status === 'SUPPORTED'
                                ? 'bg-surface-subtle text-ink border border-line'
                                : hyp.status === 'CONTRADICTED'
                                ? 'bg-danger-soft text-danger border border-danger-line'
                                : 'bg-brand-50 text-brand-600 border border-brand-200'
                            }`}>
                              {hyp.status}
                            </span>
                            <span className="text-[10px] font-mono text-ink">
                              Confidence: {Math.round(hyp.confidence_rating * 100)}%
                            </span>
                          </div>
                          <p className="text-xs font-medium text-ink leading-relaxed">{hyp.statement}</p>
                        </div>
                      </div>

                      {/* Confidence Bar */}
                      <div className="space-y-1">
                        <div className="w-full bg-white h-1.5 rounded-full overflow-hidden">
                          <div
                            className={`h-full ${
                              hyp.confidence_rating >= 0.8
                                ? 'bg-ink'
                                : hyp.confidence_rating >= 0.5
                                ? 'bg-brand-700'
                                : 'bg-line-strong'
                            }`}
                            style={{ width: `${Math.round(hyp.confidence_rating * 100)}%` }}
                          />
                        </div>
                      </div>

                      {/* Falsification Criteria & Evidence */}
                      <div className="p-2.5 rounded bg-white border border-line text-[11px] space-y-1.5">
                        <div className="text-ink-muted">
                          <span className="font-semibold text-brand-600">Falsification Criteria: </span>
                          <span>{hyp.falsification_criteria}</span>
                        </div>
                        {hyp.competing_hypotheses && hyp.competing_hypotheses.length > 0 && (
                          <div className="text-ink-muted">
                            <span className="font-semibold text-ink-soft">Alternative Model: </span>
                            <span>{hyp.competing_hypotheses[0]}</span>
                          </div>
                        )}
                      </div>

                      <div className="flex items-center justify-between text-[10px] text-ink-faint font-mono">
                        <span>Formulated: {hyp.date_formulated} | Updated: {hyp.date_updated}</span>
                        <span>Evidence Count: {hyp.linked_evidence_ids.length}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* TAB 5: BOOKMARKS (Saved Landmarks) */}
          {activeTab === 'bookmarks' && (
            <div className="space-y-4">
              <form onSubmit={handleCreateBookmark} className="p-3.5 rounded-lg bg-surface-muted border border-line space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-ink-soft flex items-center space-x-1.5">
                    <Plus className="w-3.5 h-3.5 text-ink" />
                    <span>Bookmark Current Viewport ({cameraLat.toFixed(2)}°N, {cameraLon.toFixed(2)}°E)</span>
                  </span>
                  <span className="text-[11px] font-mono text-ink">
                    MOLA Areoid: {cursorElevation !== null ? `${cursorElevation.toFixed(0)} m` : 'N/A'}
                  </span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  <input
                    type="text"
                    placeholder="Location Name (e.g. Jezero Delta Inlet)"
                    value={bmName}
                    onChange={(e) => setBmName(e.target.value)}
                    className="px-2.5 py-1.5 rounded bg-white border border-line text-xs text-ink placeholder-ink-faint focus:outline-none focus:border-brand-600"
                  />
                  <input
                    type="text"
                    placeholder="Geological Context / Mission Notes"
                    value={bmContext}
                    onChange={(e) => setBmContext(e.target.value)}
                    className="px-2.5 py-1.5 rounded bg-white border border-line text-xs text-ink placeholder-ink-faint focus:outline-none focus:border-brand-600"
                  />
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      placeholder="Tags (comma separated)"
                      value={bmTags}
                      onChange={(e) => setBmTags(e.target.value)}
                      className="flex-1 px-2.5 py-1.5 rounded bg-white border border-line text-xs text-ink placeholder-ink-faint focus:outline-none focus:border-brand-600"
                    />
                    <button
                      type="submit"
                      disabled={!bmName.trim()}
                      className="px-3 py-1.5 rounded bg-brand-700 hover:bg-brand-800 disabled:opacity-40 text-xs font-semibold text-white transition-colors"
                    >
                      Save
                    </button>
                  </div>
                </div>
              </form>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {bookmarks.map((b) => (
                  <div
                    key={b.id}
                    className="p-3.5 rounded-lg bg-surface-muted border border-line hover:border-brand-600 transition-all flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-start justify-between">
                        <h4 className="text-xs font-bold text-ink">{b.name}</h4>
                        <button
                          onClick={() => removeBookmark(b.id)}
                          className="text-ink-faint hover:text-danger transition-colors"
                          title="Delete bookmark"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                      <p className="text-[11px] text-ink-muted mt-1 line-clamp-2">{b.geological_context}</p>
                      <div className="flex flex-wrap gap-1 mt-2">
                        {b.tags.map((t, i) => (
                          <span key={i} className="text-[10px] px-1.5 py-0.2 rounded bg-surface-muted text-ink-soft font-mono">
                            #{t}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div className="pt-3 mt-3 border-t border-line flex items-center justify-between">
                      <span className="text-[10px] font-mono text-ink">
                        {b.lat.toFixed(2)}°N, {b.lon.toFixed(2)}°E | {b.elevation_m.toLocaleString()} m
                      </span>
                      <button
                        onClick={() => handleFlyTo(b.lat, b.lon)}
                        className="flex items-center space-x-1 px-2 py-1 rounded bg-surface-muted hover:bg-brand-800 hover:text-white text-[10px] text-ink-soft transition-colors"
                      >
                        <Navigation className="w-2.5 h-2.5" />
                        <span>Fly To</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 6: GEODESIC TOOLS */}
          {activeTab === 'measurements' && (
            <div className="space-y-4">
              <div className="p-4 rounded-lg bg-surface-muted border border-line space-y-3">
                <h3 className="text-xs font-semibold text-ink-soft uppercase tracking-wider">
                  Geodesic Surface Measurement Engine
                </h3>
                <p className="text-xs text-ink-muted leading-relaxed">
                  Compute true great-circle surface distances and topographic relief differences on Mars referenced to the IAU/IAG 2015 WGCCRE reference ellipsoid (A = 3,396,190 m, C = 3,376,200 m).
                </p>
                <div className="flex items-center space-x-3 pt-1">
                  <button
                    onClick={() => setMeasurementToolActive(measurementToolActive === 'ruler' ? 'none' : 'ruler')}
                    className={`flex items-center space-x-1.5 px-3 py-2 rounded-lg text-xs font-medium border transition-all ${
                      measurementToolActive === 'ruler'
                        ? 'bg-brand-700 text-white border-brand-600'
                        : 'bg-white text-ink-soft border-line hover:border-line-strong'
                    }`}
                  >
                    <Ruler className="w-3.5 h-3.5 text-ink" />
                    <span>{measurementToolActive === 'ruler' ? 'Ruler Active (Click on Globe)' : 'Activate Geodesic Ruler'}</span>
                  </button>
                  {measurementPoints.length > 0 && (
                    <button
                      onClick={clearMeasurementPoints}
                      className="px-2.5 py-2 rounded-lg bg-surface-muted hover:bg-surface-muted text-xs text-ink-soft transition-colors"
                    >
                      Clear Points ({measurementPoints.length})
                    </button>
                  )}
                </div>
              </div>

              {/* Sample Distance Display */}
              <div className="p-3.5 rounded-lg bg-surface-muted border border-line space-y-2">
                <span className="text-[11px] font-semibold text-ink-muted uppercase tracking-wider">
                  Standard Planetary Geodesic References
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                  <div className="p-2.5 rounded bg-white border border-line flex justify-between items-center">
                    <span className="text-ink-soft">Jezero Western Delta Width</span>
                    <span className="font-mono text-ink font-semibold">12.4 km</span>
                  </div>
                  <div className="p-2.5 rounded bg-white border border-line flex justify-between items-center">
                    <span className="text-ink-soft">Valles Marineris Total Length</span>
                    <span className="font-mono text-ink font-semibold">4,000 km</span>
                  </div>
                  <div className="p-2.5 rounded bg-white border border-line flex justify-between items-center">
                    <span className="text-ink-soft">Olympus Mons Caldera Diameter</span>
                    <span className="font-mono text-ink font-semibold">80 km</span>
                  </div>
                  <div className="p-2.5 rounded bg-white border border-line flex justify-between items-center">
                    <span className="text-ink-soft">Gale Crater Rim-to-Floor Drop</span>
                    <span className="font-mono text-ink font-semibold">4,500 m</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 7: SCIENTIFIC EXPORT ENGINE & PUBLICATION GENERATOR */}
          {activeTab === 'export' && (
            <div className="space-y-5">
              <div className="p-4 rounded-lg bg-surface-muted border border-line space-y-2">
                <h3 className="text-xs font-semibold text-ink-soft uppercase tracking-wider">
                  Scientific Data Product Exports & Publication Generators
                </h3>
                <p className="text-xs text-ink-muted">
                  Export verified research sessions, planetary waypoints, KML traverses, and publication-ready LaTeX tables for AGU, LPSC, and Planetary Science manuscripts.
                </p>
              </div>

              {/* 4 Export Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                {/* 1. Complete Study Package Manifest */}
                <div className="p-4 rounded-lg bg-surface-muted border border-line hover:border-brand-600 transition-all flex flex-col justify-between space-y-3">
                  <div>
                    <div className="flex items-center space-x-2 text-ink">
                      <FolderKanban className="w-4 h-4" />
                      <h4 className="text-xs font-bold text-ink">Study Package Manifest</h4>
                    </div>
                    <p className="text-[11px] text-ink-muted mt-1.5">
                      Full study dossier with GeoJSON feature collection, hypotheses, and IAU 2015 provenance manifest.
                    </p>
                  </div>
                  <button
                    onClick={handleDownloadManifest}
                    className="w-full flex items-center justify-center space-x-1.5 px-3 py-2 rounded bg-brand-700 hover:bg-brand-800 text-xs font-semibold text-white transition-colors"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download Manifest</span>
                  </button>
                </div>

                {/* 2. OGC KML 2.3 Traverse */}
                <div className="p-4 rounded-lg bg-surface-muted border border-line hover:border-brand-600 transition-all flex flex-col justify-between space-y-3">
                  <div>
                    <div className="flex items-center space-x-2 text-ink">
                      <Navigation className="w-4 h-4" />
                      <h4 className="text-xs font-bold text-ink">OGC KML 2.3 Traverse</h4>
                    </div>
                    <p className="text-[11px] text-ink-muted mt-1.5">
                      Standard XML traverse line string compatible with Google Earth Pro, NASA Web WorldWind, and QGIS.
                    </p>
                  </div>
                  <button
                    onClick={handleDownloadKML}
                    className="w-full flex items-center justify-center space-x-1.5 px-3 py-2 rounded bg-brand-700 hover:bg-brand-800 text-xs font-semibold text-white transition-colors"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download .kml</span>
                  </button>
                </div>

                {/* 3. Standard GeoJSON */}
                <div className="p-4 rounded-lg bg-surface-muted border border-line hover:border-brand-600 transition-all flex flex-col justify-between space-y-3">
                  <div>
                    <div className="flex items-center space-x-2 text-brand-600">
                      <Globe className="w-4 h-4" />
                      <h4 className="text-xs font-bold text-ink">Standard GeoJSON</h4>
                    </div>
                    <p className="text-[11px] text-ink-muted mt-1.5">
                      RFC 7946 compliant GeoJSON point collection of research bookmarks with MOLA elevation tags.
                    </p>
                  </div>
                  <button
                    onClick={handleExportGeoJSON}
                    className="w-full flex items-center justify-center space-x-1.5 px-3 py-2 rounded bg-brand-700 hover:bg-brand-800 text-xs font-semibold text-white transition-colors"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download .geojson</span>
                  </button>
                </div>

                {/* 4. Tabular CSV */}
                <div className="p-4 rounded-lg bg-surface-muted border border-line hover:border-brand-600 transition-all flex flex-col justify-between space-y-3">
                  <div>
                    <div className="flex items-center space-x-2 text-ink">
                      <FileText className="w-4 h-4" />
                      <h4 className="text-xs font-bold text-ink">Tabular CSV Waypoints</h4>
                    </div>
                    <p className="text-[11px] text-ink-muted mt-1.5">
                      Plain text CSV containing planetocentric coordinates, areoid heights, and facies annotations.
                    </p>
                  </div>
                  <button
                    onClick={handleExportCSV}
                    className="w-full flex items-center justify-center space-x-1.5 px-3 py-2 rounded bg-brand-700 hover:bg-brand-800 text-xs font-semibold text-white transition-colors"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download .csv</span>
                  </button>
                </div>
              </div>

              {/* Publication LaTeX Table Generator */}
              <div className="p-4 rounded-lg bg-surface-muted border border-line space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Sparkles className="w-4 h-4 text-ink" />
                    <h4 className="text-xs font-bold text-ink uppercase tracking-wider">
                      Manuscript LaTeX Table Generator (AGU / PSJ)
                    </h4>
                  </div>
                  <div className="flex items-center space-x-2">
                    <select
                      value={selectedLatexTable}
                      onChange={(e) => setSelectedLatexTable(e.target.value as any)}
                      className="bg-white border border-line rounded px-2.5 py-1 text-xs text-ink-soft focus:outline-none"
                    >
                      <option value="crater_morphometry">Crater Morphometry (Pike 1980 / Barlow 2000)</option>
                      <option value="terramechanics">Terramechanics Mobility (Bekker-Wong)</option>
                    </select>
                    <button
                      onClick={handleCopyLatex}
                      className="flex items-center space-x-1 px-3 py-1 rounded bg-brand-700 hover:bg-brand-800 text-xs font-semibold text-white transition-colors"
                    >
                      {copiedLatex ? <Check className="w-3 h-3 text-ink" /> : <Copy className="w-3 h-3" />}
                      <span>{copiedLatex ? 'Copied!' : 'Copy LaTeX'}</span>
                    </button>
                  </div>
                </div>

                <pre className="p-3 bg-surface-muted rounded border border-line font-mono text-[11px] text-ink-soft overflow-x-auto max-h-48 scrollbar-none">
                  {latexCode || '% Loading LaTeX table snippet...'}
                </pre>
              </div>

            </div>
          )}

        </div>


      </div>
    </div>
  );
};
