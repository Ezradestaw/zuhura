import React, { useState } from 'react';
import { Layers, Eye, EyeOff, Sliders, ChevronDown, ChevronRight, Info, Sun, Globe, TrendingUp } from 'lucide-react';
import { useLayerStore, ScientificLayer } from '../store/layerStore';
import { useGlobeStore } from '../store/globeStore';
import { useTerrainAnalysisStore } from '../store/terrainAnalysisStore';
import { useProvenanceStore } from '../store/provenanceStore';
import { EpistemicBadge } from './EpistemicBadge';

export const LayerPanel: React.FC = () => {
  const { layers, toggleLayer, setOpacity } = useLayerStore();
  const { openProvenanceModal } = useProvenanceStore();
  const {
    selectedTerrain,
    setSelectedTerrain,
    enableLighting,
    setEnableLighting,
    solarAzimuth,
    solarElevation,
    setSolarLighting,
    isLayerPanelCollapsed,
    setIsLayerPanelCollapsed,
  } = useGlobeStore();
  const { isTransectMode, setIsTransectMode, setTransectStart, setTransectEnd, executeTransectQuery } =
    useTerrainAnalysisStore();

  const [selectedInfo, setSelectedInfo] = useState<ScientificLayer | null>(null);


  const TERRAIN_OPTIONS = [
    { id: 'global', name: 'Global Mars (Multi-Res)' },
    { id: 'jezero', name: 'Jezero Crater (Perseverance)' },
    { id: 'gale', name: 'Gale Crater (Mount Sharp)' },
    { id: 'valles_marineris', name: 'Valles Marineris (Chasmata)' },
    { id: 'olympus_mons', name: 'Olympus Mons (+21.2 km Peak)' },
  ];

  const visibleCount = layers.filter((l) => l.visible).length;

  return (
    <div className="fixed top-16 left-20 z-20 w-80 bg-white border border-line rounded-lg shadow-2xl overflow-hidden font-sans select-none transition-all duration-200">
      {/* Header */}
      <div className="flex items-center justify-between px-3.5 py-2.5 bg-surface-subtle border-b border-line">
        <div className="flex items-center space-x-2">
          <Layers className="w-4 h-4 text-brand-600" />
          <span className="font-semibold text-xs text-ink">Layers</span>
          <span className="px-1.5 py-0.2 rounded bg-brand-50 border border-brand-200 text-brand-600 text-[10px] font-mono font-bold">
            {visibleCount}/{layers.length}
          </span>
        </div>
        <button
          onClick={() => setIsLayerPanelCollapsed(!isLayerPanelCollapsed)}
          className="text-ink-muted hover:text-ink p-0.5 rounded transition-colors"
          title={isLayerPanelCollapsed ? 'Expand Layer Panel' : 'Collapse Layer Panel'}
        >
          {isLayerPanelCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {!isLayerPanelCollapsed && (
        <div className="p-2.5 space-y-3 max-h-[calc(100vh-180px)] overflow-y-auto">
          {/* Scientific Imagery Layers List */}
          <div className="space-y-1.5">
            {layers.map((layer) => (
              <div
                key={layer.id}
                className={`p-2 rounded border transition-all ${
                  layer.visible ? 'bg-surface-subtle border-line shadow-sm' : 'bg-white border-line opacity-60'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2 flex-1 min-w-0">
                    <button
                      onClick={() => toggleLayer(layer.id)}
                      className={`p-1 rounded transition-colors ${
                        layer.visible ? 'text-brand-600 hover:text-brand-600' : 'text-ink-muted hover:text-ink-soft'
                      }`}
                    >
                      {layer.visible ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
                    </button>
                    <span className="text-xs font-medium text-ink truncate">{layer.name}</span>
                  </div>
                  <div className="flex items-center space-x-1.5">
                    <EpistemicBadge
                      type={
                        layer.category === 'imagery'
                          ? 'OBSERVED'
                          : layer.category === 'topography'
                            ? 'MEASURED'
                            : 'DERIVED'
                      }
                      datasetId={layer.id}
                      compact
                    />
                    <span className="px-1.5 py-0.5 rounded bg-surface-subtle border border-line text-[9px] text-ink-muted font-mono">
                      {layer.resolution}
                    </span>
                    <button
                      onClick={() => setSelectedInfo(selectedInfo?.id === layer.id ? null : layer)}
                      className="text-ink-muted hover:text-ink p-0.5"
                    >
                      <Info className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {/* Opacity Slider */}
                {layer.visible && (
                  <div className="mt-2 pt-2 border-t border-line flex items-center space-x-2">
                    <Sliders className="w-3 h-3 text-ink-muted shrink-0" />
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.05"
                      value={layer.opacity}
                      onChange={(e) => setOpacity(layer.id, parseFloat(e.target.value))}
                      className="w-full h-1 bg-surface-muted rounded appearance-none cursor-pointer accent-brand-600"
                    />
                    <span className="text-[10px] font-mono text-ink-muted w-8 text-right tabular-nums">
                      {Math.round(layer.opacity * 100)}%
                    </span>
                  </div>
                )}

                {/* Expanded Scientific Info */}
                {selectedInfo?.id === layer.id && (
                  <div className="mt-2 p-2 bg-white rounded border border-line text-[11px] text-ink-soft space-y-1">
                    <p className="leading-relaxed">{layer.description}</p>
                    <div className="pt-1 border-t border-line text-[10px] text-ink-muted">
                      <span className="font-semibold text-ink-soft">Provider:</span> {layer.provider}
                    </div>
                    <div className="text-[10px] text-ink-muted">
                      <span className="font-semibold text-ink-soft">Citation:</span> {layer.citation}
                    </div>
                    <button
                      onClick={() => openProvenanceModal(layer.id)}
                      className="mt-1 w-full py-1 px-2 rounded bg-brand-50 hover:bg-brand-50 border border-brand-200 text-brand-600 text-[10px] font-mono flex items-center justify-center space-x-1 transition-colors"
                    >
                      <span>Inspect Provenance & Uncertainty</span>
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Quantized-Mesh Terrain Models */}
          <div className="pt-2.5 border-t border-line">
            <div className="flex items-center space-x-1.5 mb-1.5 text-ink-soft text-xs font-semibold">
              <Globe className="w-3.5 h-3.5 text-brand-600" />
              <span>Mars Terrain Model</span>
            </div>
            <select
              value={selectedTerrain}
              onChange={(e) => setSelectedTerrain(e.target.value)}
              className="w-full bg-surface-subtle border border-line text-ink text-xs rounded p-1.5 font-mono focus:outline-none focus:border-brand-600"
            >
              {TERRAIN_OPTIONS.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
            <div className="mt-1 text-[10px] text-ink-muted font-mono">IAU 2015 Mars Ellipsoid & MOLA GMM-3 areoid</div>
          </div>

          {/* Dynamic Solar Illumination & Vertex Normals */}
          <div className="pt-2.5 border-t border-line">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-1.5 text-ink-soft text-xs font-semibold">
                <Sun className="w-3.5 h-3.5 text-warning" />
                <span>Solar Illumination</span>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={enableLighting}
                  onChange={(e) => setEnableLighting(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-7 h-4 bg-surface-muted peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-line-strong after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-line after:border after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-warning" />
              </label>
            </div>

            {enableLighting && (
              <div className="space-y-2 bg-surface-subtle p-2 rounded border border-line text-[11px] font-mono">
                <div>
                  <div className="flex justify-between text-[10px] text-ink-muted mb-1">
                    <span>Sun azimuth</span>
                    <span className="text-warning tabular-nums">{solarAzimuth.toFixed(0)}°</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="360"
                    step="5"
                    value={solarAzimuth}
                    onChange={(e) => setSolarLighting(parseFloat(e.target.value), solarElevation)}
                    className="w-full h-1 bg-surface-muted rounded appearance-none cursor-pointer accent-brand-600"
                  />
                </div>
                <div>
                  <div className="flex justify-between text-[10px] text-ink-muted mb-1">
                    <span>Sun elevation</span>
                    <span className="text-warning tabular-nums">{solarElevation.toFixed(0)}°</span>
                  </div>
                  <input
                    type="range"
                    min="5"
                    max="90"
                    step="5"
                    value={solarElevation}
                    onChange={(e) => setSolarLighting(solarAzimuth, parseFloat(e.target.value))}
                    className="w-full h-1 bg-surface-muted rounded appearance-none cursor-pointer accent-brand-600"
                  />
                </div>
              </div>
            )}
          </div>

          {/* Scientific Terrain Intelligence Tools */}
          <div className="pt-2.5 border-t border-line">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-1.5 text-ink-soft text-xs font-semibold">
                <TrendingUp className="w-3.5 h-3.5 text-brand-600" />
                <span>Geodesic Profiler</span>
              </div>
              <button
                onClick={() => {
                  setIsTransectMode(!isTransectMode);
                  if (!isTransectMode) {
                    executeTransectQuery();
                  }
                }}
                className={`px-2 py-0.5 rounded text-[10px] font-mono transition-colors ${
                  isTransectMode
                    ? 'bg-brand-700 text-white font-bold'
                    : 'bg-surface-muted text-ink-soft hover:bg-surface-muted'
                }`}
              >
                {isTransectMode ? 'PROFILER ACTIVE' : 'OPEN PROFILER'}
              </button>
            </div>

            {isTransectMode && (
              <div className="space-y-1.5 bg-surface-subtle p-2 rounded border border-line text-[10px] font-mono">
                <span className="text-ink-muted block text-[9px] uppercase">Presets</span>
                <div className="grid grid-cols-1 gap-1">
                  <button
                    onClick={() => {
                      setTransectStart({ latitude: 18.25, longitude: 77.35 });
                      setTransectEnd({ latitude: 18.5, longitude: 77.8 });
                      executeTransectQuery();
                    }}
                    className="text-left px-2 py-1 rounded bg-surface-subtle hover:bg-surface-muted text-ink truncate"
                  >
                    1. Jezero Western Delta &amp; Floor
                  </button>
                  <button
                    onClick={() => {
                      setTransectStart({ latitude: 18.65, longitude: 226.2 });
                      setTransectEnd({ latitude: 18.65, longitude: 228.0 });
                      executeTransectQuery();
                    }}
                    className="text-left px-2 py-1 rounded bg-surface-subtle hover:bg-surface-muted text-ink truncate"
                  >
                    2. Olympus Mons Caldera to Scarp
                  </button>
                  <button
                    onClick={() => {
                      setTransectStart({ latitude: -12.0, longitude: 297.0 });
                      setTransectEnd({ latitude: -14.0, longitude: 297.0 });
                      executeTransectQuery();
                    }}
                    className="text-left px-2 py-1 rounded bg-surface-subtle hover:bg-surface-muted text-ink truncate"
                  >
                    3. Valles Marineris Coprates Chasma
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
