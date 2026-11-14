import React, { useState, useEffect } from 'react';
import {
  X,
  Compass,
  Download,
  ExternalLink,
  Mountain,
} from 'lucide-react';
import { useGlobeStore } from '../store/globeStore';

interface GeologicalUnit {
  name: string;
  type: string;
  sol: number;
  elevation_m: number;
}

interface MountSharpData {
  dataset_id: string;
  title: string;
  target: string;
  mission: string;
  coordinates: {
    latitude_deg: number;
    longitude_deg: number;
    crs: string;
    elevation_range_m: number[];
  };
  geological_units: GeologicalUnit[];
  contributing_instruments: Array<{
    mission: string;
    instrument: string;
    institution: string;
    purpose: string;
  }>;
  credit: string;
  provenance: {
    source_url: string;
    photojournal_id: string;
  };
  download_links: {
    original_tiff: string;
    route_animation: string;
    full_jpg: string;
    annotated_fig1: string;
  };
}

export const MountSharpExplorationModal: React.FC = () => {
  const {
    isMountSharpModalOpen,
    setIsMountSharpModalOpen,
    setSelectedTerrain,
    setCameraPosition,
  } = useGlobeStore();

  const [activeTab, setActiveTab] = useState<'overview' | 'animation' | 'stratigraphy' | 'instruments'>('overview');
  const [data, setData] = useState<MountSharpData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    if (isMountSharpModalOpen) {
      setLoading(true);
      fetch('/api/v1/mount-sharp')
        .then((res) => res.json())
        .then((json) => {
          setData(json);
        })
        .catch((err) => console.error('Failed to load Mount Sharp data:', err))
        .finally(() => setLoading(false));
    }
  }, [isMountSharpModalOpen]);

  const handleFlyToMountSharp = () => {
    setSelectedTerrain('gale');
    setCameraPosition(-4.589, 137.441, 45000.0);
    setIsMountSharpModalOpen(false);
  };

  if (!isMountSharpModalOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-brand-950/60 animate-fadeIn">
      <div className="relative w-full max-w-5xl h-[86vh] bg-white border border-line rounded-xl shadow-2xl flex flex-col overflow-hidden text-ink font-sans">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 bg-surface-subtle border-b border-line">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-brand-50 border border-brand-200 flex items-center justify-center text-brand-600">
              <Mountain className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-base font-bold text-ink">
                  Curiosity's Proposed Path Up Mount Sharp
                </h2>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-brand-50 text-brand-600 border border-brand-200">
                  PIA23179 / MSL
                </span>
              </div>
              <p className="text-xs text-ink-muted">
                Gale Crater Aeolis Mons Exploration Route & Geological Units Synthesis (HiRISE • CRISM • CTX • HRSC)
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={handleFlyToMountSharp}
              className="px-3 py-1.5 rounded-lg bg-brand-700 hover:bg-brand-700 text-white font-mono text-xs font-semibold flex items-center space-x-1.5 transition-colors shadow-sm"
              title="Fly 3D Camera to Gale Crater & Mount Sharp"
            >
              <Compass className="w-3.5 h-3.5" />
              <span>Fly to Mount Sharp (3D)</span>
            </button>
            <button
              onClick={() => setIsMountSharpModalOpen(false)}
              className="p-1.5 rounded-lg text-ink-muted hover:text-ink hover:bg-surface-muted transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="px-6 py-2 bg-surface-subtle border-b border-line flex items-center space-x-2 text-xs">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-3 py-1.5 rounded-md font-mono transition-all ${
              activeTab === 'overview'
                ? 'bg-surface-muted text-ink font-semibold'
                : 'text-ink-muted hover:text-ink'
            }`}
          >
            Scientific Overview
          </button>
          <button
            onClick={() => setActiveTab('animation')}
            className={`px-3 py-1.5 rounded-md font-mono transition-all ${
              activeTab === 'animation'
                ? 'bg-surface-muted text-ink font-semibold'
                : 'text-ink-muted hover:text-ink'
            }`}
          >
            Rover Route Animation (GIF)
          </button>
          <button
            onClick={() => setActiveTab('stratigraphy')}
            className={`px-3 py-1.5 rounded-md font-mono transition-all ${
              activeTab === 'stratigraphy'
                ? 'bg-surface-muted text-ink font-semibold'
                : 'text-ink-muted hover:text-ink'
            }`}
          >
            Geological Stratigraphy Units
          </button>
          <button
            onClick={() => setActiveTab('instruments')}
            className={`px-3 py-1.5 rounded-md font-mono transition-all ${
              activeTab === 'instruments'
                ? 'bg-surface-muted text-ink font-semibold'
                : 'text-ink-muted hover:text-ink'
            }`}
          >
            Contributing Instruments
          </button>
        </div>

        {/* Body Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="h-full flex items-center justify-center text-ink-muted font-mono text-xs">
              Loading NASA PIA23179 Mount Sharp Assets...
            </div>
          ) : !data ? (
            <div className="h-full flex items-center justify-center text-danger font-mono text-xs">
              Unable to load Mount Sharp dataset.
            </div>
          ) : (
            <div>
              {/* TAB 1: OVERVIEW */}
              {activeTab === 'overview' && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="md:col-span-2 space-y-4">
                    <div className="relative rounded-xl overflow-hidden border border-line bg-surface-muted shadow-lg">
                      <img
                        src={data.download_links?.annotated_fig1 || data.download_links?.full_jpg}
                        alt="Curiosity Proposed Path up Mount Sharp"
                        className="w-full object-cover max-h-[50vh]"
                      />
                      <div className="absolute bottom-2 left-2 px-2.5 py-1 rounded bg-brand-950/75 text-[10px] font-mono text-white">
                        Figure 1: Annotated Proposed Path (Vera Rubin • Glen Torridon • Sulfate Unit)
                      </div>
                    </div>

                    <div className="bg-surface-subtle p-4 rounded-xl border border-line space-y-2 text-xs">
                      <h3 className="text-ink font-bold text-[11px]">
                        Mission summary
                      </h3>
                      <p className="text-ink-soft leading-relaxed">
                        This authoritative dataset illustrates the multi-year ascent route for NASA's Mars Science Laboratory (Curiosity) rover climbing Mount Sharp (Aeolis Mons) in Gale Crater. Rising 5.5 kilometers above the crater floor, Mount Sharp preserves a sedimentary record spanning billions of years of Martian climate evolution, from an ancient warm and wet lacustrine environment to today's hyper-arid desert.
                      </p>
                    </div>
                  </div>

                  {/* Sidebar Info & Downloads */}
                  <div className="space-y-4">
                    <div className="bg-surface-subtle p-4 rounded-xl border border-line space-y-3 font-mono text-xs">
                      <h4 className="text-[11px] font-bold text-brand-600 uppercase tracking-wider">
                        Geographic Parameters
                      </h4>
                      <div className="space-y-1.5 text-[11px]">
                        <div className="flex justify-between">
                          <span className="text-ink-muted">Target:</span>
                          <span className="text-ink font-semibold">Mount Sharp (Aeolis Mons)</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-ink-muted">Crater:</span>
                          <span className="text-ink font-semibold">Gale Crater (154 km Ø)</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-ink-muted">Coordinates:</span>
                          <span className="text-ink font-semibold">4.59° S, 137.44° E</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-ink-muted">Floor Elevation:</span>
                          <span className="text-ink font-semibold">-4,500 m Areoid</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-ink-muted">Peak Elevation:</span>
                          <span className="text-ink font-semibold">+5,500 m Areoid</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-ink-muted">Relief:</span>
                          <span className="text-brand-600 font-bold">~5.5 km Vertical</span>
                        </div>
                      </div>
                    </div>

                    {/* Official NASA Downloadable Files */}
                    <div className="bg-surface-subtle p-4 rounded-xl border border-line space-y-2.5 text-xs">
                      <h4 className="text-[11px] font-bold text-brand-600 flex items-center space-x-1.5">
                        <Download className="w-3.5 h-3.5" />
                        <span>Official NASA Downloads</span>
                      </h4>
                      <div className="space-y-1.5">
                        <a
                          href={data.download_links?.original_tiff}
                          className="w-full py-2 px-3 rounded-lg bg-brand-50 hover:bg-brand-100 border border-brand-200 text-ink font-mono text-[11px] flex items-center justify-between transition-colors"
                        >
                          <span>Original Master GeoTIFF</span>
                          <span className="text-brand-600 font-bold text-[10px]">13.7 MB</span>
                        </a>
                        <a
                          href={data.download_links?.route_animation}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="w-full py-2 px-3 rounded-lg bg-surface-muted hover:bg-surface-muted border border-line text-ink font-mono text-[11px] flex items-center justify-between transition-colors"
                        >
                          <span>Curiosity Route Animation</span>
                          <span className="text-ink-muted text-[10px]">3.0 MB GIF</span>
                        </a>
                        <a
                          href={data.download_links?.full_jpg}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="w-full py-2 px-3 rounded-lg bg-surface-muted hover:bg-surface-muted border border-line text-ink font-mono text-[11px] flex items-center justify-between transition-colors"
                        >
                          <span>Full Overview Image</span>
                          <span className="text-ink-muted text-[10px]">743 KB JPG</span>
                        </a>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2: ANIMATION */}
              {activeTab === 'animation' && (
                <div className="flex flex-col items-center justify-center space-y-4">
                  <div className="relative rounded-xl overflow-hidden border border-line bg-surface-muted shadow-2xl max-w-3xl">
                    <img
                      src={data.download_links?.route_animation}
                      alt="Curiosity Proposed Path up Mount Sharp Animation"
                      className="w-full object-contain max-h-[60vh]"
                    />
                  </div>
                  <p className="text-xs text-ink-muted font-mono text-center max-w-2xl">
                    NASA animation demonstrating Curiosity's traverse ascending from the clay-bearing unit into the sulfate-bearing unit and Gediz Vallis channel.
                  </p>
                </div>
              )}

              {/* TAB 3: STRATIGRAPHY */}
              {activeTab === 'stratigraphy' && (
                <div className="space-y-4">
                  <h3 className="text-xs text-ink-soft font-bold">
                    Mount Sharp Chronostratigraphic Units Traversed by Curiosity
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                    {data.geological_units.map((unit, idx) => (
                      <div
                        key={idx}
                        className="p-3.5 rounded-xl bg-surface-subtle border border-line hover:border-brand-200 transition-all flex flex-col justify-between"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-ink">{unit.name}</span>
                          <span className="px-2 py-0.5 rounded bg-surface-subtle text-brand-600 font-mono text-[10px] font-bold">
                            {unit.elevation_m} m
                          </span>
                        </div>
                        <div className="mt-2 flex items-center justify-between text-[11px] font-mono text-ink-muted">
                          <span className="capitalize">{unit.type.replace(/_/g, ' ')}</span>
                          <span className="text-ink-muted">Target Sol ~{unit.sol}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* TAB 4: INSTRUMENTS */}
              {activeTab === 'instruments' && (
                <div className="space-y-4">
                  <h3 className="text-xs text-ink-soft font-bold">
                    Missions & Orbital Remote-Sensing Instruments Synthesized
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {data.contributing_instruments.map((inst, idx) => (
                      <div
                        key={idx}
                        className="p-4 rounded-xl bg-surface-subtle border border-line space-y-2 text-xs"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-bold text-ink font-mono">
                            {inst.mission} • {inst.instrument}
                          </span>
                          <span className="text-[10px] font-mono text-brand-600 font-semibold">
                            {inst.institution}
                          </span>
                        </div>
                        <p className="text-ink-soft text-[11px] leading-relaxed">
                          {inst.purpose}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 bg-surface-subtle border-t border-line flex items-center justify-between text-xs text-ink-muted">
          <div className="text-[10px]">
            Attribution: {data?.credit || 'NASA / JPL-Caltech / ESA / MSSS / USGS'}
          </div>
          <a
            href={data?.provenance.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center space-x-1 text-brand-600 hover:text-ink transition-colors text-[11px]"
          >
            <span>NASA Science Source</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>

      </div>
    </div>
  );
};
