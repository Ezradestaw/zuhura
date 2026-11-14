import React, { useEffect } from 'react';
import { Footprints, X, Zap } from 'lucide-react';
import { useGlobeStore } from '../store/globeStore';

export const SurfaceExplorationHUD: React.FC = () => {
  const {
    isSurfaceWalkActive,
    surfaceWalkSpeed,
    cameraLat,
    cameraLon,
    cursorElevation,
    setIsSurfaceWalkActive,
    setSurfaceWalkSpeed,
    setCameraPosition,
  } = useGlobeStore();

  useEffect(() => {
    if (!isSurfaceWalkActive) return;

    const viewer = (window as any).viewer;
    const Cesium = (window as any).Cesium;
    if (!viewer || !Cesium) return;

    // Lock camera into first-person surface perspective (~2m eye height above terrain)
    const groundElevation = cursorElevation || 0.0;
    const eyeAltitude = groundElevation + 2.0;

    const ellipsoid = viewer.scene.globe.ellipsoid;
    viewer.camera.flyTo({
      destination: Cesium.Cartesian3.fromDegrees(cameraLon, cameraLat, eyeAltitude, ellipsoid),
      orientation: {
        heading: viewer.camera.heading,
        pitch: Cesium.Math.toRadians(-5.0), // looking slightly forward towards horizon
        roll: 0.0,
      },
      duration: 1.5,
    });

    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't intercept if user is typing in an input
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') return;

      if (e.key === 'Escape') {
        setIsSurfaceWalkActive(false);
        return;
      }

      const moveStepMeters = (e.shiftKey ? surfaceWalkSpeed * 2.5 : surfaceWalkSpeed) * 2.0;
      const camera = viewer.camera;

      if (e.key === 'w' || e.key === 'W' || e.key === 'ArrowUp') {
        camera.moveForward(moveStepMeters);
        e.preventDefault();
      } else if (e.key === 's' || e.key === 'S' || e.key === 'ArrowDown') {
        camera.moveBackward(moveStepMeters);
        e.preventDefault();
      } else if (e.key === 'a' || e.key === 'A' || e.key === 'ArrowLeft') {
        camera.moveLeft(moveStepMeters);
        e.preventDefault();
      } else if (e.key === 'd' || e.key === 'D' || e.key === 'ArrowRight') {
        camera.moveRight(moveStepMeters);
        e.preventDefault();
      } else if (e.key === 'q' || e.key === 'Q') {
        camera.lookLeft(Cesium.Math.toRadians(3.0));
        e.preventDefault();
      } else if (e.key === 'e' || e.key === 'E') {
        camera.lookRight(Cesium.Math.toRadians(3.0));
        e.preventDefault();
      }

      // Update position in store
      const carto = ellipsoid.cartesianToCartographic(camera.position);
      if (carto) {
        const curLon = Cesium.Math.toDegrees(carto.longitude);
        const curLat = Cesium.Math.toDegrees(carto.latitude);
        setCameraPosition(curLat, curLon, carto.height);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isSurfaceWalkActive, surfaceWalkSpeed, cameraLat, cameraLon, cursorElevation]);

  if (!isSurfaceWalkActive) return null;

  return (
    <div className="absolute top-16 left-1/2 -translate-x-1/2 z-10 flex items-center space-x-3 px-4 py-2 rounded bg-white border border-brand-200 shadow-2xl text-xs font-mono select-none">
      <div className="flex items-center space-x-2 text-brand-600">
        <span className="w-2 h-2 rounded-full bg-brand-700 " />
        <Footprints className="w-4 h-4 text-brand-600" />
        <span className="text-ink font-bold tracking-wider">Surface walk:</span>
      </div>

      <div className="flex items-center space-x-2 text-ink-soft">
        <span className="text-ink-muted">POS:</span>
        <span className="text-ink tabular-nums">
          {cameraLat.toFixed(4)}°, {cameraLon.toFixed(4)}°
        </span>
        <span className="text-ink">|</span>
        <span className="text-ink-muted">Eye height:</span>
        <span className="text-brand-600 font-bold tabular-nums">+2.0 m</span>
        <span className="text-ink">|</span>
        <span className="text-ink-muted">SPEED:</span>
        <button
          onClick={() => setSurfaceWalkSpeed(surfaceWalkSpeed === 2.5 ? 5.0 : 2.5)}
          className="flex items-center space-x-1 px-1.5 py-0.5 rounded bg-surface-muted hover:bg-surface-muted text-warning transition-colors"
          title="Toggle Sprint Velocity"
        >
          <Zap className="w-3 h-3 text-warning" />
          <span>{surfaceWalkSpeed.toFixed(1)} m/s</span>
        </button>
      </div>

      <div className="pl-2 border-l border-line text-[10px] text-ink-muted">WASD to walk · Q/E turn · Shift sprint</div>

      {/* Exit Button */}
      <button
        onClick={() => {
          setIsSurfaceWalkActive(false);
          const viewer = (window as any).viewer;
          const Cesium = (window as any).Cesium;
          if (viewer && Cesium) {
            viewer.camera.flyTo({
              destination: Cesium.Cartesian3.fromDegrees(cameraLon, cameraLat, 50000.0),
              duration: 1.5,
            });
          }
        }}
        className="ml-2 pl-2 border-l border-line text-ink-muted hover:text-ink transition-colors"
        title="Exit Surface Walk Mode (ESC)"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
};
