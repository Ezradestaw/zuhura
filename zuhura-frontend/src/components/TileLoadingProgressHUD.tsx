import React from 'react';
import { AlertTriangle } from 'lucide-react';
import { useGlobeStore } from '../store/globeStore';

/** Thin loading bar while map tiles stream in, and a notice if tiles fail to load. */
export const TileLoadingProgressHUD: React.FC = () => {
  const { tilesLoadingCount, isTileLoadError } = useGlobeStore();


  return (
    <>
      {tilesLoadingCount > 0 && (
        <div className="pointer-events-none fixed left-0 right-0 top-14 z-40 h-0.5 overflow-hidden bg-brand-100">
          <div className="h-full w-1/3 animate-pulse bg-brand-500" />
        </div>
      )}

      {isTileLoadError && (
        <div className="absolute bottom-8 right-4 z-10 flex items-center gap-1.5 rounded border border-danger-line bg-danger-soft px-2.5 py-1.5 text-xs text-danger">
          <AlertTriangle className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
          Some map tiles could not be loaded.
        </div>
      )}
    </>
  );
};
