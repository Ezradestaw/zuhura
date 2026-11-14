import React, { useState, useEffect } from 'react';
import { Eye, X, RefreshCw, Scan, Sparkles, Activity, TrendingUp } from 'lucide-react';
import { useGlobeStore } from '../store/globeStore';
import {
  fetchDetectedFeatures,
  fetchCraterMorphology,
  fetchMultiSpectralAnalysis,
  fetchChangeDetection,
  fetchImageRegistration,
  fetchSuperResolution,
  DetectedPlanetaryFeatureData,
  CraterMorphologyProfileData,
  MultiSpectralAnalysisResultData,
  TemporalChangeDetectionResultData,
  ImageRegistrationResultData,
  SuperResolutionResultData,
} from '../lib/advancedApiClient';
import { EpistemicBadge } from './EpistemicBadge';

export const VisualIntelligenceModal: React.FC = () => {
  const { isVisualIntelligenceOpen, setIsVisualIntelligenceOpen, setCameraPosition } = useGlobeStore();

  const [activeTab, setActiveTab] = useState<'features' | 'multispectral' | 'changes' | 'registration'>('features');

  // Coordinates
  const [lat, setLat] = useState<number>(18.38);
  const [lon, setLon] = useState<number>(77.58);

  // States
  const [features, setFeatures] = useState<DetectedPlanetaryFeatureData[]>([]);
  const [selectedCrater, setSelectedCrater] = useState<CraterMorphologyProfileData | null>(null);
  const [craterDiameter, setCraterDiameter] = useState<number>(47.5);

  const [spectralResult, setSpectralResult] = useState<MultiSpectralAnalysisResultData | null>(null);
  const [changesResult, setChangesResult] = useState<TemporalChangeDetectionResultData | null>(null);
  const [registrationResult, setRegistrationResult] = useState<ImageRegistrationResultData | null>(null);
  const [superResResult, setSuperResResult] = useState<SuperResolutionResultData | null>(null);

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const ANCHOR_SITES = [
    { name: 'Jezero Crater Basin', lat: 18.38, lon: 77.58, diam: 47.5 },
    { name: 'Kodiak Butte Delta Front', lat: 18.42, lon: 77.48, diam: 3.2 },
    { name: 'Séítah TAR Dune Field', lat: 18.36, lon: 77.54, diam: 1.8 },
    { name: 'Gale Mt Sharp Sulfate Benches', lat: -4.68, lon: 137.38, diam: 154.0 },
    { name: 'Palikir Crater Equatorward RSL', lat: -41.6, lon: 202.3, diam: 15.6 },
    { name: 'Newton Crater Gullies', lat: -40.5, lon: 158.1, diam: 298.0 },
  ];

  const handleLoadData = async (targetLat: number, targetLon: number, diam: number = 25.0) => {
    try {
      setIsLoading(true);
      setErrorMsg(null);
      const [featData, craterData, specData, changeData, regData, srData] = await Promise.all([
        fetchDetectedFeatures(targetLat, targetLon, 150.0).catch(() => []),
        fetchCraterMorphology(targetLat, targetLon, diam).catch(() => null),
        fetchMultiSpectralAnalysis(targetLat, targetLon).catch(() => null),
        fetchChangeDetection(targetLat, targetLon).catch(() => null),
        fetchImageRegistration().catch(() => null),
        fetchSuperResolution(6.0, 2.0).catch(() => null),
      ]);

      setFeatures(featData);
      setSelectedCrater(craterData);
      setSpectralResult(specData);
      setChangesResult(changeData);
      setRegistrationResult(regData);
      setSuperResResult(srData);
    } catch (e: any) {
      setErrorMsg(e.message || 'Vision intelligence analysis failed');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isVisualIntelligenceOpen) {
      handleLoadData(lat, lon, craterDiameter);
    }
  }, [isVisualIntelligenceOpen]);

  if (!isVisualIntelligenceOpen) return null;

  const handleSelectAnchor = (a: (typeof ANCHOR_SITES)[0]) => {
    setLat(a.lat);
    setLon(a.lon);
    setCraterDiameter(a.diam);
    setCameraPosition(a.lat, a.lon, 450000);
    handleLoadData(a.lat, a.lon, a.diam);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-brand-950/60 select-none">
      <div className="relative w-full max-w-4xl max-h-[90vh] bg-white border border-line rounded shadow-2xl flex flex-col overflow-hidden font-sans text-ink">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3.5 bg-surface-subtle border-b border-line">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded bg-brand-50 border border-brand-200 flex items-center justify-center text-brand-600">
              <Scan className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-sm text-ink">Visual intelligence</span>
                <EpistemicBadge type="OBSERVED" compact />
                <EpistemicBadge type="DERIVED" compact />
              </div>
              <p className="text-[11px] text-ink-muted">
                Crater measurements, CRISM spectral indices and change detection for a selected site.
              </p>
            </div>
          </div>
          <button
            onClick={() => setIsVisualIntelligenceOpen(false)}
            className="p-1.5 text-ink-muted hover:text-ink rounded hover:bg-surface-muted transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Anchor Sites Quick-Jump */}
        <div className="px-5 py-2 bg-surface-subtle border-b border-line flex items-center gap-1.5 overflow-x-auto text-[11px] font-mono">
          <span className="text-ink-muted text-[10px] uppercase tracking-wider shrink-0 mr-1">Anchors:</span>
          {ANCHOR_SITES.map((a, idx) => (
            <button
              key={idx}
              onClick={() => handleSelectAnchor(a)}
              className={`px-2 py-0.5 rounded border whitespace-nowrap transition-colors ${
                Math.abs(lat - a.lat) < 0.05 && Math.abs(lon - a.lon) < 0.05
                  ? 'bg-brand-50 border-brand-600 text-brand-600 font-bold'
                  : 'bg-surface-subtle border-line text-ink-muted hover:text-ink'
              }`}
            >
              {a.name}
            </button>
          ))}
        </div>

        {/* Navigation Tabs */}
        <div className="flex border-b border-line bg-surface-subtle text-xs font-mono">
          <button
            onClick={() => setActiveTab('features')}
            className={`flex-1 py-2.5 px-4 text-center border-b-2 transition-colors ${
              activeTab === 'features'
                ? 'border-brand-600 text-brand-600 font-bold bg-surface-subtle'
                : 'border-transparent text-ink-muted hover:text-ink'
            }`}
          >
            Features & Crater Morphology
          </button>
          <button
            onClick={() => setActiveTab('multispectral')}
            className={`flex-1 py-2.5 px-4 text-center border-b-2 transition-colors ${
              activeTab === 'multispectral'
                ? 'border-warning text-warning font-bold bg-surface-subtle'
                : 'border-transparent text-ink-muted hover:text-ink'
            }`}
          >
            CRISM Spectra & Thermal Inertia
          </button>
          <button
            onClick={() => setActiveTab('changes')}
            className={`flex-1 py-2.5 px-4 text-center border-b-2 transition-colors ${
              activeTab === 'changes'
                ? 'border-danger text-danger font-bold bg-surface-subtle'
                : 'border-transparent text-ink-muted hover:text-ink'
            }`}
          >
            Temporal Change Detection
          </button>
          <button
            onClick={() => setActiveTab('registration')}
            className={`flex-1 py-2.5 px-4 text-center border-b-2 transition-colors ${
              activeTab === 'registration'
                ? 'border-success text-success font-bold bg-surface-subtle'
                : 'border-transparent text-ink-muted hover:text-ink'
            }`}
          >
            Image Registration & Super-Res
          </button>
        </div>

        {/* Tab Body */}
        <div className="p-5 overflow-y-auto flex-1 space-y-4 text-xs">
          {errorMsg && (
            <div className="p-3 rounded bg-danger-soft border border-danger-line text-danger">{errorMsg}</div>
          )}

          {isLoading ? (
            <div className="py-16 flex flex-col items-center justify-center space-y-2 text-ink-muted font-mono">
              <RefreshCw className="w-6 h-6 animate-spin text-brand-600" />
              <span>Analyzing orbital frames and extracting feature signatures...</span>
            </div>
          ) : (
            <>
              {/* TAB 1: FEATURES & CRATER MORPHOLOGY */}
              {activeTab === 'features' && (
                <div className="space-y-4">
                  {/* Crater Morphometry Banner */}
                  {selectedCrater && (
                    <div className="p-4 rounded-lg bg-surface-subtle border border-brand-200 space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <Eye className="w-4 h-4 text-brand-600" />
                          <span className="font-bold font-mono text-ink text-sm">
                            {selectedCrater.name || 'Target Crater Morphometry'}
                          </span>
                          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-brand-50 text-brand-600 border border-brand-600">
                            {selectedCrater.crater_class}
                          </span>
                          <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-surface-muted text-ink-soft">
                            {selectedCrater.degradation_state}
                          </span>
                        </div>
                        <span className="font-mono text-ink-muted text-[11px]">
                          Age: ~{selectedCrater.estimated_age_gyr} Gyr (Hartmann 2001)
                        </span>
                      </div>

                      {/* Morphometry Metrics Grid */}
                      <div className="grid grid-cols-4 gap-2 font-mono text-[11px]">
                        <div className="p-2.5 rounded bg-surface-subtle border border-line">
                          <span className="text-ink-muted block text-[10px]">Diameter (D)</span>
                          <span className="text-ink font-bold text-sm">{selectedCrater.diameter_km} km</span>
                        </div>
                        <div className="p-2.5 rounded bg-surface-subtle border border-line">
                          <span className="text-ink-muted block text-[10px]">APPARENT DEPTH (d)</span>
                          <span className="text-brand-600 font-bold text-sm">{selectedCrater.apparent_depth_m} m</span>
                        </div>
                        <div className="p-2.5 rounded bg-surface-subtle border border-line">
                          <span className="text-ink-muted block text-[10px]">d/D RATIO</span>
                          <span className="text-warning font-bold text-sm">
                            {selectedCrater.depth_to_diameter_ratio}
                          </span>
                        </div>
                        <div className="p-2.5 rounded bg-surface-subtle border border-line">
                          <span className="text-ink-muted block text-[10px]">Ejecta type</span>
                          <span
                            className="text-success font-bold text-xs truncate block"
                            title={selectedCrater.ejecta_blanket_type}
                          >
                            {selectedCrater.ejecta_blanket_type.replace(/_/g, ' ')}
                          </span>
                        </div>
                      </div>

                      <p className="text-ink-muted text-[11px] font-sans leading-relaxed">
                        {selectedCrater.scientific_notes}
                      </p>
                    </div>
                  )}

                  {/* Detected Features List */}
                  <div className="space-y-2">
                    <span className="text-ink-muted text-[11px] block">
                      Regional Detected Features ({features.length} Identified)
                    </span>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                      {features.map((f, idx) => (
                        <div
                          key={idx}
                          className="p-3 rounded bg-surface-subtle border border-line hover:border-brand-200 transition-colors space-y-1.5"
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-ink font-mono text-[11px]">{f.name || f.feature_id}</span>
                            <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-surface-muted text-brand-600 border border-brand-200">
                              {(f.confidence_score * 100).toFixed(0)}% Conf
                            </span>
                          </div>
                          <div className="flex items-center space-x-2 text-[10px] font-mono text-ink-muted">
                            <span className="uppercase text-warning">{f.feature_type.replace(/_/g, ' ')}</span>
                            <span>•</span>
                            <span>
                              {f.bounding_box.width_m}m × {f.bounding_box.height_m}m
                            </span>
                          </div>
                          <p className="text-[10px] text-ink-muted font-sans leading-snug">
                            {f.scientific_significance}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2: CRISM SPECTRA & THEMIS THERMAL INERTIA */}
              {activeTab === 'multispectral' && spectralResult && (
                <div className="space-y-4">
                  {/* Spectral Indices Card */}
                  <div className="p-4 rounded-lg bg-surface-subtle border border-warning-line space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Activity className="w-4 h-4 text-warning" />
                        <span className="font-bold font-mono text-ink text-sm">
                          CRISM Multi-Spectral Band Ratio Indices
                        </span>
                      </div>
                      <div className="flex items-center space-x-2 font-mono text-[11px]">
                        <span className="text-ink-muted">False-Color RGB:</span>
                        <div
                          className="w-5 h-5 rounded border border-line-strong shadow-inner"
                          style={{ backgroundColor: spectralResult.false_color_rgb.hex }}
                        />
                        <span className="text-ink font-bold">{spectralResult.false_color_rgb.hex}</span>
                      </div>
                    </div>

                    <div className="grid grid-cols-4 gap-2 font-mono text-[11px]">
                      <div className="p-2.5 rounded bg-surface-subtle border border-line">
                        <span className="text-ink-muted block text-[10px]">Fe³⁺ iron oxide</span>
                        <span className="text-danger font-bold text-sm">
                          {spectralResult.spectral_indices.iron_oxide_index}
                        </span>
                        <span className="text-[9px] text-ink-muted block">R860/R530 Ratio</span>
                      </div>
                      <div className="p-2.5 rounded bg-surface-subtle border border-line">
                        <span className="text-ink-muted block text-[10px]">Smectite clays</span>
                        <span className="text-success font-bold text-sm">
                          {spectralResult.spectral_indices.phyllosilicate_clay_index}
                        </span>
                        <span className="text-[9px] text-ink-muted block">D2300 Absorption</span>
                      </div>
                      <div className="p-2.5 rounded bg-surface-subtle border border-line">
                        <span className="text-ink-muted block text-[10px]">Olivine / mafic</span>
                        <span className="text-brand-600 font-bold text-sm">
                          {spectralResult.spectral_indices.olivine_mafic_index}
                        </span>
                        <span className="text-[9px] text-ink-muted block">1 - R1050 Ratio</span>
                      </div>
                      <div className="p-2.5 rounded bg-surface-subtle border border-line">
                        <span className="text-ink-muted block text-[10px]">Hydration (H₂O)</span>
                        <span className="text-brand-600 font-bold text-sm">
                          {spectralResult.spectral_indices.hydrated_mineral_index}
                        </span>
                        <span className="text-[9px] text-ink-muted block">D1900 Band Depth</span>
                      </div>
                    </div>

                    <div className="p-2 rounded bg-surface-subtle border border-line text-[11px]">
                      <span className="text-warning font-bold font-mono">Dominant Mineralogy: </span>
                      <span className="text-ink">{spectralResult.spectral_indices.mineral_description}</span>
                    </div>
                  </div>

                  {/* THEMIS Thermal Inertia Card */}
                  <div className="p-4 rounded-lg bg-surface-subtle border border-brand-200 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <TrendingUp className="w-4 h-4 text-brand-600" />
                        <span className="font-bold font-mono text-ink text-sm">
                          THEMIS Thermal Inertia & Grain Size Inversion
                        </span>
                      </div>
                      <span className="text-[10px] font-mono text-ink-muted">Presley & Christensen (1997)</span>
                    </div>

                    <div className="grid grid-cols-4 gap-2 font-mono text-[11px]">
                      <div className="p-2.5 rounded bg-surface-subtle border border-line">
                        <span className="text-ink-muted block text-[10px]">Thermal inertia</span>
                        <span className="text-ink font-bold text-sm">
                          {spectralResult.thermal_inertia.derived_thermal_inertia_tiu} tiu
                        </span>
                        <span className="text-[9px] text-ink-muted block">J m⁻² K⁻¹ s⁻¹/²</span>
                      </div>
                      <div className="p-2.5 rounded bg-surface-subtle border border-line">
                        <span className="text-ink-muted block text-[10px]">Grain size (d)</span>
                        <span className="text-brand-600 font-bold text-sm">
                          {spectralResult.thermal_inertia.estimated_grain_size_um} µm
                        </span>
                        <span className="text-[9px] text-ink-muted block">Effective Diameter</span>
                      </div>
                      <div className="p-2.5 rounded bg-surface-subtle border border-line">
                        <span className="text-ink-muted block text-[10px]">Daily range</span>
                        <span className="text-warning font-bold text-sm">
                          Δ{spectralResult.thermal_inertia.diurnal_temperature_amplitude_k} K
                        </span>
                        <span className="text-[9px] text-ink-muted block">
                          {spectralResult.thermal_inertia.nighttime_ir_temp_k}K →{' '}
                          {spectralResult.thermal_inertia.daytime_ir_temp_k}K
                        </span>
                      </div>
                      <div className="p-2.5 rounded bg-surface-subtle border border-line">
                        <span className="text-ink-muted block text-[10px]">Sediment class</span>
                        <span
                          className="text-success font-bold text-xs truncate block"
                          title={spectralResult.thermal_inertia.grain_size_classification}
                        >
                          {spectralResult.thermal_inertia.grain_size_classification.replace(/_/g, ' ')}
                        </span>
                        <span className="text-[9px] text-ink-muted block">Regolith Physical Facies</span>
                      </div>
                    </div>

                    <div className="p-2 rounded bg-surface-subtle border border-line text-[11px]">
                      <span className="text-brand-600 font-bold font-mono">Bearing Capacity: </span>
                      <span className="text-ink-soft">{spectralResult.thermal_inertia.bearing_capacity_rating}</span>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 3: TEMPORAL CHANGE DETECTION */}
              {activeTab === 'changes' && changesResult && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-[11px] font-mono text-ink-muted">
                    <span>
                      SURVEILLANCE EPOCHS: {changesResult.epoch_1_date} TO {changesResult.epoch_2_date}
                    </span>
                    <span className="text-danger font-bold">{changesResult.total_changes_detected} Dynamic Events</span>
                  </div>

                  <div className="space-y-2">
                    {changesResult.changes.map((c, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded bg-surface-subtle border border-line hover:border-danger-line transition-colors space-y-1.5"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <span className="font-bold text-ink font-mono text-[11px]">
                              {c.change_type.replace(/_/g, ' ')}
                            </span>
                            <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-danger-soft text-danger border border-danger-line">
                              Albedo{' '}
                              {c.relative_albedo_delta_pct > 0
                                ? `+${c.relative_albedo_delta_pct}`
                                : c.relative_albedo_delta_pct}
                              %
                            </span>
                          </div>
                          <span className="text-[10px] font-mono text-ink-muted">
                            Confidence: {(c.confidence_score * 100).toFixed(0)}%
                          </span>
                        </div>
                        <div className="text-[10px] font-mono text-ink-muted">
                          Coords: {c.location_latitude.toFixed(2)}°N, {c.location_longitude.toFixed(2)}°E • Observed
                          between {c.first_observed_epoch} and {c.second_observed_epoch}
                        </div>
                        <p className="text-[11px] text-ink-soft font-sans leading-relaxed">{c.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* TAB 4: IMAGE REGISTRATION & SUPER-RESOLUTION */}
              {activeTab === 'registration' && registrationResult && superResResult && (
                <div className="space-y-4">
                  {/* Sub-Pixel Registration Card */}
                  <div className="p-4 rounded-lg bg-surface-subtle border border-success-line space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Scan className="w-4 h-4 text-success" />
                        <span className="font-bold font-mono text-ink text-sm">
                          Orbital Frame Sub-Pixel Registration (CTX ↔ HiRISE)
                        </span>
                      </div>
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-success-soft text-success border border-success-line">
                        {registrationResult.registration_quality}
                      </span>
                    </div>

                    <div className="grid grid-cols-4 gap-2 font-mono text-[11px]">
                      <div className="p-2.5 rounded bg-surface-subtle border border-line">
                        <span className="text-ink-muted block text-[10px]">Residual RMSE</span>
                        <span className="text-success font-bold text-sm">
                          {registrationResult.subpixel_alignment_rmse_pixels} px
                        </span>
                        <span className="text-[9px] text-ink-muted block">Sub-Pixel Error</span>
                      </div>
                      <div className="p-2.5 rounded bg-surface-subtle border border-line">
                        <span className="text-ink-muted block text-[10px]">RANSAC inliers</span>
                        <span className="text-ink font-bold text-sm">
                          {registrationResult.inlier_matches_count} / {registrationResult.matched_keypoints_count}
                        </span>
                        <span className="text-[9px] text-ink-muted block">Consensus Matches</span>
                      </div>
                      <div className="p-2.5 rounded bg-surface-subtle border border-line">
                        <span className="text-ink-muted block text-[10px]">Inlier ratio</span>
                        <span className="text-brand-600 font-bold text-sm">
                          {(registrationResult.inlier_ratio * 100).toFixed(1)}%
                        </span>
                        <span className="text-[9px] text-ink-muted block">Geometric Consensus</span>
                      </div>
                      <div className="p-2.5 rounded bg-surface-subtle border border-line">
                        <span className="text-ink-muted block text-[10px]">Rotation</span>
                        <span className="text-warning font-bold text-sm">
                          {registrationResult.rotation_angle_degrees}°
                        </span>
                        <span className="text-[9px] text-ink-muted block">
                          Scale: {registrationResult.projective_scale_factor}x
                        </span>
                      </div>
                    </div>

                    {/* Homography Matrix View */}
                    <div className="p-2.5 rounded bg-surface-subtle font-mono text-[10px] space-y-1">
                      <span className="text-ink-muted uppercase text-[9px] block">
                        Projective Homography Matrix (H 3×3):
                      </span>
                      <div className="text-ink-soft">
                        {registrationResult.homography_matrix_3x3.map((row, rIdx) => (
                          <div key={rIdx} className="flex justify-between max-w-xs">
                            {row.map((val, cIdx) => (
                              <span key={cIdx}>{val.toFixed(4)}</span>
                            ))}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Super-Resolution Enhancement Card */}
                  <div className="p-4 rounded-lg bg-surface-subtle border border-brand-200 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Sparkles className="w-4 h-4 text-brand-600" />
                        <span className="font-bold font-mono text-ink text-sm">
                          Morphological Super-Resolution Enhancement
                        </span>
                      </div>
                      <span className="font-mono text-brand-600 text-[11px] font-bold">
                        {superResResult.original_resolution_m_per_px}m → {superResResult.enhanced_resolution_m_per_px}m
                        ({superResResult.enhancement_factor}x)
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-2 font-mono text-[11px]">
                      <div className="p-2 rounded bg-surface-subtle border border-line flex justify-between">
                        <span className="text-ink-muted">Peak SNR (PSNR):</span>
                        <span className="text-success font-bold">{superResResult.psnr_db} dB</span>
                      </div>
                      <div className="p-2 rounded bg-surface-subtle border border-line flex justify-between">
                        <span className="text-ink-muted">Structural Similarity (SSIM):</span>
                        <span className="text-brand-600 font-bold">{superResResult.ssim_score}</span>
                      </div>
                    </div>

                    <div className="space-y-1">
                      <span className="text-[10px] text-ink-muted">Subtle Features Revealed:</span>
                      <div className="flex flex-wrap gap-1.5">
                        {superResResult.features_revealed.map((f, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-0.5 rounded bg-surface-subtle border border-brand-600 text-[10px] text-brand-600"
                          >
                            {f}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};
