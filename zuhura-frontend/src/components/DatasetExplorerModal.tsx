import React, { useState, useEffect } from 'react';
import {
  X,
  Search,
  Filter,
  Layers,
  Database,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { useGlobeStore } from '../store/globeStore';

interface TrekLayer {
  trek_id: string;
  label: string;
  title: string;
  category: string;
  product_type: string;
  mission: string;
  instrument: string;
  projection: string;
  bbox: string;
  wmts_template: string;
  capabilities_url: string;
  thumbnail_url?: string;
  description?: string;
  credit: string;
  access_type: string;
}

export const DatasetExplorerModal: React.FC = () => {
  const { isDatasetExplorerOpen, setIsDatasetExplorerOpen } = useGlobeStore();

  const [category, setCategory] = useState<string>('all');
  const [mission, setMission] = useState<string>('all');
  const [instrument, setInstrument] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [page, setPage] = useState<number>(1);
  const [pageSize] = useState<number>(12);

  const [loading, setLoading] = useState<boolean>(false);
  const [trekLayers, setTrekLayers] = useState<TrekLayer[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [selectedLayer, setSelectedLayer] = useState<TrekLayer | null>(null);

  const CATEGORIES = [
    { id: 'all', label: 'All Categories' },
    { id: 'imagery', label: 'Imagery / Optical' },
    { id: 'topography', label: 'Topography / Elevation' },
    { id: 'terrain', label: 'Terrain / Roughness' },
    { id: 'mineral', label: 'Mineralogy / Spectroscopy' },
    { id: 'thermalinertia', label: 'Thermal Inertia' },
  ];

  const MISSIONS = [
    { id: 'all', label: 'All Missions' },
    { id: 'Mars Reconnaissance Orbiter', label: 'Mars Reconnaissance Orbiter (MRO)' },
    { id: 'Mars Global Surveyor', label: 'Mars Global Surveyor (MGS)' },
    { id: 'MEX', label: 'Mars Express (MEX / ESA)' },
    { id: 'Mars Odyssey', label: 'Mars Odyssey (MO)' },
    { id: 'Viking', label: 'Viking Orbiters' },
  ];

  const fetchTrekLayers = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      });
      if (category !== 'all') params.append('category', category);
      if (mission !== 'all') params.append('mission', mission);
      if (instrument !== 'all') params.append('instrument', instrument);
      if (searchQuery.trim()) params.append('query', searchQuery.trim());

      const res = await fetch(`/api/v1/catalog/trek?${params.toString()}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setTrekLayers(data.layers || []);
      setTotalCount(data.total || 0);
      setTotalPages(data.total_pages || 1);
    } catch (err) {
      console.error('Failed to load Mars Trek catalog:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isDatasetExplorerOpen) {
      fetchTrekLayers();
    }
  }, [isDatasetExplorerOpen, category, mission, instrument, page]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchTrekLayers();
  };

  if (!isDatasetExplorerOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-brand-950/60 animate-fadeIn">
      <div className="relative w-full max-w-6xl h-[88vh] bg-white border border-line rounded-xl shadow-2xl flex flex-col overflow-hidden text-ink font-sans">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 bg-surface-subtle border-b border-line">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-brand-50 border border-brand-200 flex items-center justify-center text-brand-600">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-base font-bold text-ink">
                  Datasets
                </h2>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-brand-50 text-brand-600 border border-brand-200">
                  NASA Mars Trek • USGS Astrogeology • PDS
                </span>
              </div>
              <p className="text-xs text-ink-muted">
                Search, filter, and stream authentic planetary imagery, topography, mineralogy, and geological map layers
              </p>
            </div>
          </div>
          <button
            onClick={() => setIsDatasetExplorerOpen(false)}
            className="p-1.5 rounded-lg text-ink-muted hover:text-ink hover:bg-surface-muted transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Filter Bar */}
        <div className="px-6 py-3 bg-surface-subtle border-b border-line flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center space-x-2">
            <Filter className="w-3.5 h-3.5 text-ink-muted" />
            
            {/* Category */}
            <select
              value={category}
              onChange={(e) => { setCategory(e.target.value); setPage(1); }}
              className="bg-surface-subtle border border-line rounded-lg px-2.5 py-1.5 text-xs text-ink focus:outline-none focus:border-brand-600"
            >
              {CATEGORIES.map((c) => (
                <option key={c.id} value={c.id} className="bg-white">
                  {c.label}
                </option>
              ))}
            </select>

            {/* Mission */}
            <select
              value={mission}
              onChange={(e) => { setMission(e.target.value); setPage(1); }}
              className="bg-surface-subtle border border-line rounded-lg px-2.5 py-1.5 text-xs text-ink focus:outline-none focus:border-brand-600"
            >
              {MISSIONS.map((m) => (
                <option key={m.id} value={m.id} className="bg-white">
                  {m.label}
                </option>
              ))}
            </select>
          </div>

          {/* Search Box */}
          <form onSubmit={handleSearchSubmit} className="flex items-center space-x-2 flex-1 max-w-md">
            <div className="relative flex-1">
              <input
                type="text"
                placeholder="Search layer title, instrument, or ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-surface-subtle border border-line rounded-lg pl-8 pr-3 py-1.5 text-xs text-ink focus:outline-none focus:border-brand-600"
              />
              <Search className="w-3.5 h-3.5 text-ink-muted absolute left-2.5 top-2.5" />
            </div>
            <button
              type="submit"
              className="px-3 py-1.5 rounded-lg bg-brand-700 hover:bg-brand-700 text-white font-mono text-xs transition-colors"
            >
              Search
            </button>
          </form>

          <div className="text-[11px] font-mono text-ink-muted">
            Catalog: <span className="text-brand-600 font-bold">{totalCount}</span> scientific layers
          </div>
        </div>

        {/* Layer Cards Grid */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="h-full flex flex-col items-center justify-center space-y-3 text-ink-muted">
              <div className="w-8 h-8 border-2 border-brand-600 border-t-transparent rounded-full animate-spin" />
              <p className="text-xs font-mono">Querying Mars Trek Layer Registry...</p>
            </div>
          ) : trekLayers.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center space-y-2 text-ink-muted">
              <Layers className="w-10 h-10 stroke-[1.5]" />
              <p className="text-sm">No layers match the current criteria.</p>
              <button
                onClick={() => { setCategory('all'); setMission('all'); setInstrument('all'); setSearchQuery(''); setPage(1); }}
                className="text-xs text-brand-600 underline"
              >
                Reset filters
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {trekLayers.map((layer) => (
                <div
                  key={layer.trek_id || layer.label}
                  className="p-4 rounded-xl bg-surface-subtle border border-line hover:border-brand-600 transition-all flex flex-col justify-between group shadow-sm"
                >
                  <div className="space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-brand-50 text-brand-600 border border-brand-200">
                        {layer.category}
                      </span>
                      <span className="text-[10px] font-mono text-ink-muted truncate max-w-[150px]">
                        {layer.mission}
                      </span>
                    </div>

                    <h3 className="text-xs font-bold text-ink leading-snug group-hover:text-brand-600 transition-colors line-clamp-2">
                      {layer.title}
                    </h3>

                    <div className="space-y-1 font-mono text-[10px] text-ink-muted">
                      <div>
                        Label: <span className="text-ink-soft">{layer.label}</span>
                      </div>
                      {layer.instrument && (
                        <div>
                          Instrument: <span className="text-ink-soft">{layer.instrument}</span>
                        </div>
                      )}
                      {layer.projection && (
                        <div className="truncate">
                          Projection: <span className="text-ink-soft">{layer.projection}</span>
                        </div>
                      )}
                    </div>

                    {layer.description && (
                      <p className="text-ink-muted text-[11px] line-clamp-2 leading-relaxed">
                        {layer.description}
                      </p>
                    )}
                  </div>

                  <div className="mt-4 pt-3 border-t border-line flex items-center justify-between text-xs">
                    <a
                      href={layer.capabilities_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[10px] text-ink-muted hover:text-ink flex items-center space-x-1 font-mono transition-colors"
                      title="View OGC WMTS Capabilities XML"
                    >
                      <span>WMTS XML</span>
                      <ExternalLink className="w-2.5 h-2.5" />
                    </a>

                    <button
                      onClick={() => setSelectedLayer(layer)}
                      className="px-2.5 py-1 rounded-md bg-surface-muted hover:bg-surface-muted text-ink text-[10px] font-mono transition-colors"
                    >
                      Inspect Metadata
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Pagination Bar */}
        <div className="px-6 py-3 bg-surface-subtle border-t border-line flex items-center justify-between text-xs">
          <div className="text-ink-muted text-[11px] font-mono">
            Page <span className="text-ink font-bold">{page}</span> of {totalPages}
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page <= 1}
              className="px-3 py-1.5 rounded-lg bg-surface-muted hover:bg-surface-muted disabled:opacity-40 disabled:cursor-not-allowed flex items-center space-x-1 text-ink-soft font-mono text-xs transition-colors"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
              <span>Previous</span>
            </button>
            <button
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page >= totalPages}
              className="px-3 py-1.5 rounded-lg bg-surface-muted hover:bg-surface-muted disabled:opacity-40 disabled:cursor-not-allowed flex items-center space-x-1 text-ink-soft font-mono text-xs transition-colors"
            >
              <span>Next</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Detailed Metadata Inspector Drawer / Popup */}
        {selectedLayer && (
          <div className="absolute inset-0 z-50 bg-brand-950/60 flex items-center justify-center p-6 animate-fadeIn">
            <div className="relative w-full max-w-2xl bg-white border border-line rounded-xl p-6 space-y-4 shadow-2xl text-xs">
              <div className="flex items-center justify-between border-b border-line pb-3">
                <div>
                  <span className="text-[10px] text-brand-600 font-bold">
                    OGC WMTS Scientific Product
                  </span>
                  <h3 className="text-base font-bold text-ink mt-0.5">
                    {selectedLayer.title}
                  </h3>
                </div>
                <button
                  onClick={() => setSelectedLayer(null)}
                  className="p-1 rounded-lg text-ink-muted hover:text-ink hover:bg-surface-muted"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="space-y-2 font-mono text-[11px] bg-surface-subtle p-4 rounded-lg border border-line">
                <div className="flex justify-between">
                  <span className="text-ink-muted">Layer Label:</span>
                  <span className="text-ink">{selectedLayer.label}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-ink-muted">Category / Type:</span>
                  <span className="text-brand-600 font-bold">{selectedLayer.category} ({selectedLayer.product_type})</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-ink-muted">Mission:</span>
                  <span className="text-ink">{selectedLayer.mission}</span>
                </div>
                {selectedLayer.instrument && (
                  <div className="flex justify-between">
                    <span className="text-ink-muted">Instrument:</span>
                    <span className="text-ink">{selectedLayer.instrument}</span>
                  </div>
                )}
                {selectedLayer.bbox && (
                  <div className="flex justify-between">
                    <span className="text-ink-muted">Bounding Box:</span>
                    <span className="text-ink">{selectedLayer.bbox}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-ink-muted">Projection CRS:</span>
                  <span className="text-ink">{selectedLayer.projection}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-ink-muted">Service Protocol:</span>
                  <span className="text-success">OGC RESTful WMTS</span>
                </div>
              </div>

              {selectedLayer.description && (
                <div>
                  <h4 className="text-[11px] font-bold text-ink-soft mb-1">
                    Dataset Description
                  </h4>
                  <p className="text-ink-soft text-[11px] leading-relaxed bg-surface-muted p-3 rounded-lg border border-line">
                    {selectedLayer.description}
                  </p>
                </div>
              )}

              <div className="pt-2 flex items-center justify-between">
                <a
                  href={selectedLayer.wmts_template.replace('{z}/0/0.jpg', '0/0/0.jpg')}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-brand-600 hover:text-ink text-[11px] font-mono flex items-center space-x-1"
                >
                  <span>Direct Tile Endpoint</span>
                  <ExternalLink className="w-3 h-3" />
                </a>

                <button
                  onClick={() => setSelectedLayer(null)}
                  className="px-4 py-2 rounded-lg bg-brand-700 hover:bg-brand-700 text-white font-mono text-xs font-semibold"
                >
                  Done
                </button>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
};
