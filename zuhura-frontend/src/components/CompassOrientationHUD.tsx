import React from 'react';
import { RotateCcw, ArrowUp, ArrowDown } from 'lucide-react';
import { useGlobeStore } from '../store/globeStore';

export const CompassOrientationHUD: React.FC = () => {
  const {
    cameraHeading,
    cameraPitch,
    cameraRoll,
    cameraLat,
    cameraLon,
    cameraAlt,
    activeMainView,
    isRoutePlannerOpen,
    isRegionDiscoveryOpen,
  } = useGlobeStore();

  const handleResetNorth = () => {
    const viewer = (window as any).viewer;
    if (viewer && (window as any).Cesium) {
      const Cesium = (window as any).Cesium;
      const destination = Cesium.Cartesian3.fromDegrees(cameraLon, cameraLat, cameraAlt, viewer.scene.globe.ellipsoid);
      viewer.camera.flyTo({
        destination,
        orientation: {
          heading: Cesium.Math.toRadians(0.0), // True North
          pitch: Cesium.Math.toRadians(Math.max(-89.9, Math.min(-10.0, cameraPitch))),
          roll: 0.0,
        },
        duration: 1.2,
      });
    }
  };

  const handleTilt = (deltaDeg: number) => {
    const viewer = (window as any).viewer;
    if (viewer && (window as any).Cesium) {
      const Cesium = (window as any).Cesium;
      const targetPitch = Math.max(-89.9, Math.min(-5.0, cameraPitch + deltaDeg));
      viewer.camera.setView({
        orientation: {
          heading: Cesium.Math.toRadians(cameraHeading),
          pitch: Cesium.Math.toRadians(targetPitch),
          roll: Cesium.Math.toRadians(cameraRoll),
        },
      });
    }
  };

  if (activeMainView !== 'explorer' || isRoutePlannerOpen || isRegionDiscoveryOpen) return null;

  return (
    <div className="absolute top-16 right-4 z-10 flex flex-col items-center select-none font-mono">
      {/* Compass Dial */}
      <div className="relative group flex items-center justify-center">
        <button
          onClick={handleResetNorth}
          className="relative w-12 h-12 rounded-full bg-white border border-line-strong hover:border-brand-600 shadow-2xl flex items-center justify-center transition-all duration-200 group-hover:scale-105 "
          title={`Heading ${Math.round(cameraHeading)}°. Click to face north.`}
        >
          {/* North Tick */}
          <div className="absolute top-1 text-[8px] font-bold text-brand-600 tracking-tighter">N</div>
          {/* South Tick */}
          <div className="absolute bottom-1 text-[8px] font-bold text-ink-muted tracking-tighter">S</div>
          {/* East Tick */}
          <div className="absolute right-1 text-[8px] font-bold text-ink-muted tracking-tighter">E</div>
          {/* West Tick */}
          <div className="absolute left-1 text-[8px] font-bold text-ink-muted tracking-tighter">W</div>

          {/* Rotating Compass Needle */}
          <div
            className="w-7 h-7 flex items-center justify-center transition-transform duration-75 ease-out"
            style={{ transform: `rotate(${-cameraHeading}deg)` }}
          >
            <div className="w-0.5 h-6 rounded-full bg-gradient-to-b from-danger from-50% to-ink-muted to-50%" />
          </div>
        </button>

        {/* Hover Flyout Controls */}
        <div className="absolute -bottom-8 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex items-center space-x-1 bg-white px-2 py-0.5 rounded border border-line text-[9px] text-ink-soft">
          <button
            onClick={() => handleTilt(15)}
            className="hover:text-brand-600 transition-colors p-0.5"
            title="Tilt Up (+15°)"
          >
            <ArrowUp className="w-3 h-3" />
          </button>
          <span className="text-ink-muted">|</span>
          <button
            onClick={() => handleTilt(-15)}
            className="hover:text-brand-600 transition-colors p-0.5"
            title="Tilt Down (-15°)"
          >
            <ArrowDown className="w-3 h-3" />
          </button>
          <span className="text-ink-muted">|</span>
          <button
            onClick={handleResetNorth}
            className="hover:text-brand-600 transition-colors p-0.5"
            title="Reset North & Nadir"
          >
            <RotateCcw className="w-3 h-3" />
          </button>
        </div>
      </div>
    </div>
  );
};
