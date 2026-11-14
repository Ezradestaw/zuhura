import React, { useEffect, useRef } from 'react';
import { Columns, X, SlidersHorizontal } from 'lucide-react';
import { useGlobeStore } from '../store/globeStore';

interface LayerOption {
  id: string;
  name: string;
  res: string;
}

const AVAILABLE_SWIPE_LAYERS: LayerOption[] = [
  { id: 'zuhura-viking-mdim21', name: 'Viking MDIM 2.1 Natural Color', res: '232 m/px' },
  { id: 'zuhura-ctx-jezero', name: 'MRO CTX Context Mosaic', res: '5.55 m/px' },
  { id: 'zuhura-hirise-jezero', name: 'MRO HiRISE Targeted High-Res', res: '0.25 m/px' },
  { id: 'zuhura-mola-global-v3-cog', name: 'MOLA MEG128 Topography Colormap', res: '463 m/px' },
];

export const ImagerySplitSwipeHUD: React.FC = () => {
  const {
    isSplitScreenActive,
    splitPosition,
    splitLeftLayerId,
    splitRightLayerId,
    setIsSplitScreenActive,
    setSplitPosition,
    setSplitLayers,
  } = useGlobeStore();

  const isDraggingRef = useRef(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isSplitScreenActive) return;

    const viewer = (window as any).viewer;
    const Cesium = (window as any).Cesium;
    if (!viewer || !Cesium) return;

    // Set Cesium scene split position
    viewer.scene.imagerySplitPosition = splitPosition;

    // Apply SplitDirection to imagery layers
    const layers = viewer.imageryLayers;
    for (let i = 0; i < layers.length; i++) {
      const layer = layers.get(i);
      const layerId = (layer as any).zuhuraLayerId;
      if (layerId === splitLeftLayerId) {
        layer.splitDirection = Cesium.SplitDirection.LEFT;
        layer.show = true;
      } else if (layerId === splitRightLayerId) {
        layer.splitDirection = Cesium.SplitDirection.RIGHT;
        layer.show = true;
      } else {
        layer.splitDirection = Cesium.SplitDirection.NONE;
      }
    }
  }, [isSplitScreenActive, splitPosition, splitLeftLayerId, splitRightLayerId]);

  if (!isSplitScreenActive) return null;

  const handleMouseDown = () => {
    isDraggingRef.current = true;
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDraggingRef.current) return;
    const x = e.clientX;
    const w = window.innerWidth;
    const newPos = Math.max(0.08, Math.min(0.92, x / w));
    setSplitPosition(newPos);
  };

  const handleMouseUp = () => {
    isDraggingRef.current = false;
  };

  const handleClose = () => {
    setIsSplitScreenActive(false);
    const viewer = (window as any).viewer;
    const Cesium = (window as any).Cesium;
    if (viewer && Cesium) {
      const layers = viewer.imageryLayers;
      for (let i = 0; i < layers.length; i++) {
        layers.get(i).splitDirection = Cesium.SplitDirection.NONE;
      }
    }
  };

  const leftLayerName = AVAILABLE_SWIPE_LAYERS.find(l => l.id === splitLeftLayerId)?.name || 'Left Layer';
  const rightLayerName = AVAILABLE_SWIPE_LAYERS.find(l => l.id === splitRightLayerId)?.name || 'Right Layer';

  return (
    <div
      ref={containerRef}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      className="fixed inset-0 z-10 pointer-events-none select-none"
    >
      {/* Top Banner Control Panel */}
      <div className="absolute top-16 left-1/2 -translate-x-1/2 pointer-events-auto flex items-center space-x-3 px-4 py-2 rounded bg-white border border-line-strong shadow-2xl text-xs font-mono">
        <div className="flex items-center space-x-2 text-brand-600">
          <Columns className="w-4 h-4 text-brand-600" />
          <span className="text-ink font-bold tracking-wider">Compare layers:</span>
        </div>

        {/* Left Selector */}
        <select
          value={splitLeftLayerId}
          onChange={(e) => setSplitLayers(e.target.value, splitRightLayerId)}
          className="bg-surface-subtle border border-line rounded px-2 py-0.5 text-xs text-brand-600 font-mono focus:outline-none focus:border-brand-600"
        >
          {AVAILABLE_SWIPE_LAYERS.map(l => (
            <option key={`left-${l.id}`} value={l.id}>
              LEFT: {l.name} ({l.res})
            </option>
          ))}
        </select>

        <span className="text-ink">vs</span>

        {/* Right Selector */}
        <select
          value={splitRightLayerId}
          onChange={(e) => setSplitLayers(splitLeftLayerId, e.target.value)}
          className="bg-surface-subtle border border-line rounded px-2 py-0.5 text-xs text-warning font-mono focus:outline-none focus:border-warning"
        >
          {AVAILABLE_SWIPE_LAYERS.map(l => (
            <option key={`right-${l.id}`} value={l.id}>
              RIGHT: {l.name} ({l.res})
            </option>
          ))}
        </select>

        {/* Exit Button */}
        <button
          onClick={handleClose}
          className="ml-2 pl-2 border-l border-line text-ink-muted hover:text-ink transition-colors"
          title="Exit Split-Screen Swipe Mode"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Floating Draggable Vertical Divider Bar */}
      <div
        className="absolute top-0 bottom-0 pointer-events-auto cursor-ew-resize flex items-center justify-center"
        style={{ left: `${splitPosition * 100}%`, transform: 'translateX(-50%)' }}
        onMouseDown={handleMouseDown}
      >
        {/* Hairline Divider Line */}
        <div className="w-[2px] h-full bg-brand-700" />

        {/* Draggable Handle Puck */}
        <div className="absolute w-9 h-9 rounded-full bg-white border-2 border-brand-600 shadow-2xl flex items-center justify-center text-brand-600 hover:scale-110 transition-transform">
          <SlidersHorizontal className="w-4 h-4" />
        </div>

        {/* Left Side Label Indicator */}
        <div className="absolute right-6 px-2 py-1 rounded bg-white border border-brand-200 text-[10px] font-mono text-brand-600 pointer-events-none whitespace-nowrap shadow-lg">
          ◀ {leftLayerName}
        </div>

        {/* Right Side Label Indicator */}
        <div className="absolute left-6 px-2 py-1 rounded bg-white border border-warning-line text-[10px] font-mono text-warning pointer-events-none whitespace-nowrap shadow-lg">
          {rightLayerName} ▶
        </div>
      </div>
    </div>
  );
};