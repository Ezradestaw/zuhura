import React, { useState, useEffect } from 'react';
import {
  X,
  Camera,
  Search,
  Filter,
  Download,
  Info,
  ChevronLeft,
  ChevronRight,
  Maximize2,
} from 'lucide-react';
import { useGlobeStore } from '../store/globeStore';

interface RawImageItem {
  image_id: string;
  sol: number;
  camera_code: string;
  camera_name: string;
  instrument: string;
  date_taken_utc?: string;
  date_taken_mars?: string;
  caption: string;
  title: string;
  original_url: string;
  local_path?: string;
  thumbnail_path?: string;
  size_bytes: number;
  credit: string;
  license: string;
}

export const RoverRawImagesModal: React.FC = () => {
  const { isRoverRawImagesOpen, setIsRoverRawImagesOpen } = useGlobeStore();

  const [rover, setRover] = useState<'perseverance' | 'curiosity'>('perseverance');
  const [selectedCamera, setSelectedCamera] = useState<string>('all');
  const [selectedSol, setSelectedSol] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [page, setPage] = useState<number>(1);
  const [limit] = useState<number>(12);

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [images, setImages] = useState<RawImageItem[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [totalPages, setTotalPages] = useState<number>(1);

  const [selectedImage, setSelectedImage] = useState<RawImageItem | null>(null);

  const CAMERAS = [
    { id: 'all', label: 'All Instruments' },
    { id: 'mastcam_z', label: 'Mastcam-Z (Multispectral Zoom)' },
    { id: 'navcam', label: 'Navcam (Engineering Stereo)' },
    { id: 'hazcam', label: 'Hazcam (Hazard Avoidance)' },
    { id: 'supercam', label: 'SuperCam (Remote Micro-Imager)' },
    { id: 'sherloc', label: 'SHERLOC WATSON (Microscopic)' },
    { id: 'pixl', label: 'PIXL (Lithochemistry Context)' },
  ];

  const fetchImages = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        rover,
        page: page.toString(),
        limit: limit.toString(),
      });
      if (selectedCamera !== 'all') params.append('camera', selectedCamera);
      if (selectedSol.trim()) params.append('sol', selectedSol.trim());
      if (searchTerm.trim()) params.append('search', searchTerm.trim());

      const res = await fetch(`/api/v1/rover/raw-images?${params.toString()}`);
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const data = await res.json();
      setImages(data.items || []);
      setTotalCount(data.total || 0);
      setTotalPages(data.total_pages || 1);
    } catch (err: any) {
      console.error('Failed to load rover raw images:', err);
      setError('Unable to load rover images. Please check connection.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isRoverRawImagesOpen) {
      fetchImages();
    }
  }, [isRoverRawImagesOpen, rover, selectedCamera, page]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchImages();
  };

  if (!isRoverRawImagesOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-brand-950/60 animate-fadeIn">
      <div className="relative w-full max-w-6xl h-[88vh] bg-white border border-line rounded-xl shadow-2xl flex flex-col overflow-hidden text-ink font-sans">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 bg-surface-subtle border-b border-line">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-brand-50 border border-brand-200 flex items-center justify-center text-brand-600">
              <Camera className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-base font-bold text-ink">
                  Rover images
                </h2>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-success-soft text-success border border-success-line">
                  NASA / JPL EDR
                </span>
              </div>
              <p className="text-xs text-ink-muted">
                Raw images from the Perseverance and Curiosity cameras, with their metadata.
              </p>
            </div>
          </div>
          <button
            onClick={() => {
              setIsRoverRawImagesOpen(false);
              setSelectedImage(null);
            }}
            className="p-1.5 rounded-lg text-ink-muted hover:text-ink hover:bg-surface-muted transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Filter Toolbar */}
        <div className="px-6 py-3 bg-surface-subtle border-b border-line flex flex-wrap items-center justify-between gap-3 text-xs">
          {/* Rover Selector */}
          <div className="flex items-center space-x-2 bg-surface-subtle p-1 rounded-lg border border-line">
            <button
              onClick={() => { setRover('perseverance'); setPage(1); }}
              className={`px-3 py-1 rounded-md font-mono text-xs transition-all ${
                rover === 'perseverance'
                  ? 'bg-brand-700 text-white shadow-sm'
                  : 'text-ink-muted hover:text-ink'
              }`}
            >
              Perseverance (M20)
            </button>
            <button
              onClick={() => { setRover('curiosity'); setPage(1); }}
              className={`px-3 py-1 rounded-md font-mono text-xs transition-all ${
                rover === 'curiosity'
                  ? 'bg-brand-700 text-white shadow-sm'
                  : 'text-ink-muted hover:text-ink'
              }`}
            >
              Curiosity (MSL)
            </button>
          </div>

          {/* Camera Category Dropdown */}
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-ink-muted" />
            <select
              value={selectedCamera}
              onChange={(e) => { setSelectedCamera(e.target.value); setPage(1); }}
              className="bg-surface-subtle border border-line rounded-lg px-3 py-1.5 text-xs text-ink focus:outline-none focus:border-brand-600"
            >
              {CAMERAS.map((c) => (
                <option key={c.id} value={c.id} className="bg-white">
                  {c.label}
                </option>
              ))}
            </select>
          </div>

          {/* Search & Sol Input */}
          <form onSubmit={handleSearchSubmit} className="flex items-center space-x-2 flex-1 max-w-md">
            <input
              type="number"
              placeholder="Sol (e.g. 2024)"
              value={selectedSol}
              onChange={(e) => setSelectedSol(e.target.value)}
              className="w-24 bg-surface-subtle border border-line rounded-lg px-2.5 py-1.5 text-xs text-ink font-mono focus:outline-none focus:border-brand-600"
            />
            <div className="relative flex-1">
              <input
                type="text"
                placeholder="Search caption, title, or ID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-surface-subtle border border-line rounded-lg pl-8 pr-3 py-1.5 text-xs text-ink focus:outline-none focus:border-brand-600"
              />
              <Search className="w-3.5 h-3.5 text-ink-muted absolute left-2.5 top-2.5" />
            </div>
            <button
              type="submit"
              className="px-3 py-1.5 rounded-lg bg-brand-700 hover:bg-brand-700 text-white font-mono text-xs transition-colors"
            >
              Filter
            </button>
          </form>

          {/* Telemetry Count */}
          <div className="text-[11px] font-mono text-ink-muted">
            Found <span className="text-brand-600 font-bold">{totalCount}</span> images
          </div>
        </div>

        {/* Main Content Area */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="h-full flex flex-col items-center justify-center space-y-3 text-ink-muted">
              <div className="w-8 h-8 border-2 border-brand-600 border-t-transparent rounded-full animate-spin" />
              <p className="text-xs font-mono">Querying NASA Raw Images Archive...</p>
            </div>
          ) : error ? (
            <div className="h-full flex flex-col items-center justify-center space-y-2 text-danger">
              <Info className="w-8 h-8" />
              <p className="text-sm font-medium">{error}</p>
              <button
                onClick={fetchImages}
                className="px-3 py-1 rounded bg-surface-muted hover:bg-surface-muted text-xs text-ink"
              >
                Retry
              </button>
            </div>
          ) : images.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center space-y-2 text-ink-muted">
              <Camera className="w-10 h-10 stroke-[1.5]" />
              <p className="text-sm">No raw images found matching your filter criteria.</p>
              <button
                onClick={() => { setSelectedCamera('all'); setSelectedSol(''); setSearchTerm(''); setPage(1); }}
                className="text-xs text-brand-600 underline"
              >
                Reset filters
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3.5">
              {images.map((img) => (
                <div
                  key={img.image_id}
                  onClick={() => setSelectedImage(img)}
                  className="group relative bg-surface-subtle border border-line hover:border-brand-600 rounded-lg overflow-hidden cursor-pointer transition-all duration-200 hover:shadow-lg flex flex-col"
                >
                  <div className="aspect-square bg-surface-subtle overflow-hidden relative">
                    <img
                      src={img.original_url}
                      alt={img.title || img.camera_name}
                      loading="lazy"
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                    <div className="absolute top-1.5 left-1.5 px-1.5 py-0.5 rounded bg-brand-950/75 text-[9px] font-mono text-white font-semibold">
                      Sol {img.sol}
                    </div>
                    <div className="absolute top-1.5 right-1.5 px-1.5 py-0.5 rounded bg-brand-700 text-[9px] font-mono text-white">
                      {img.camera_code}
                    </div>
                  </div>
                  <div className="p-2 flex-1 flex flex-col justify-between text-[10px]">
                    <div className="font-medium text-ink truncate" title={img.camera_name}>
                      {img.camera_name}
                    </div>
                    <div className="text-ink-muted font-mono text-[9px] mt-1 flex justify-between items-center">
                      <span>{(img.size_bytes / (1024 * 1024)).toFixed(2)} MB</span>
                      <Maximize2 className="w-3 h-3 text-ink-muted group-hover:text-brand-600" />
                    </div>
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

        {/* Detailed Lightbox Modal */}
        {selectedImage && (
          <div className="absolute inset-0 z-50 bg-brand-950/60 flex flex-col md:flex-row overflow-hidden animate-fadeIn">
            {/* Image Preview Canvas */}
            <div className="flex-1 flex items-center justify-center p-6 bg-space relative overflow-hidden">
              <img
                src={selectedImage.original_url}
                alt={selectedImage.title}
                className="max-w-full max-h-[80vh] object-contain rounded shadow-2xl"
              />
              <button
                onClick={() => setSelectedImage(null)}
                className="absolute top-4 right-4 p-2 rounded-full bg-surface-muted hover:bg-surface-muted text-ink transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Scientific Provenance & Metadata Sidebar */}
            <div className="w-full md:w-96 bg-white border-l border-line p-6 flex flex-col justify-between overflow-y-auto font-sans text-xs">
              <div className="space-y-4">
                <div>
                  <span className="text-[10px] text-brand-600 font-bold">
                    NASA Planetary Observation
                  </span>
                  <h3 className="text-base font-bold text-ink mt-0.5">
                    {selectedImage.camera_name}
                  </h3>
                  <div className="text-ink-muted font-mono text-[11px] mt-1">
                    Image ID: <span className="text-ink">{selectedImage.image_id}</span>
                  </div>
                </div>

                <div className="space-y-2 border-t border-b border-line py-3 font-mono text-[11px]">
                  <div className="flex justify-between">
                    <span className="text-ink-muted">Mission Sol:</span>
                    <span className="text-brand-600 font-bold">{selectedImage.sol}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-ink-muted">Camera Code:</span>
                    <span className="text-ink">{selectedImage.camera_code}</span>
                  </div>
                  {selectedImage.date_taken_utc && (
                    <div className="flex justify-between">
                      <span className="text-ink-muted">UTC Acquisition:</span>
                      <span className="text-ink">{selectedImage.date_taken_utc.replace('T', ' ').slice(0, 19)}</span>
                    </div>
                  )}
                  {selectedImage.date_taken_mars && (
                    <div className="flex justify-between">
                      <span className="text-ink-muted">Martian Solar Time:</span>
                      <span className="text-ink">{selectedImage.date_taken_mars}</span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span className="text-ink-muted">Uncompressed Size:</span>
                    <span className="text-ink">{(selectedImage.size_bytes / (1024 * 1024)).toFixed(2)} MB</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-ink-muted">Data status:</span>
                    <span className="text-success font-bold">OBSERVED (Raw EDR)</span>
                  </div>
                </div>

                {selectedImage.caption && (
                  <div>
                    <h4 className="text-[11px] font-bold text-ink-soft mb-1">
                      Observation Caption
                    </h4>
                    <p className="text-ink-soft leading-relaxed text-[11px] bg-surface-subtle p-3 rounded-lg border border-line">
                      {selectedImage.caption}
                    </p>
                  </div>
                )}

                <div>
                  <h4 className="text-[11px] font-bold text-ink-soft mb-1">
                    Provenance & Attribution
                  </h4>
                  <p className="text-ink-muted text-[10px] leading-normal">
                    Credit: {selectedImage.credit}. Released under public domain NASA open data policy.
                  </p>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-4 border-t border-line flex items-center space-x-2">
                <a
                  href={selectedImage.original_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-1 py-2 px-3 rounded-lg bg-brand-700 hover:bg-brand-700 text-white font-mono text-xs font-semibold flex items-center justify-center space-x-1.5 transition-colors"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download Full Res</span>
                </a>
                <button
                  onClick={() => setSelectedImage(null)}
                  className="py-2 px-3 rounded-lg bg-surface-muted hover:bg-surface-muted text-ink font-mono text-xs transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
};
