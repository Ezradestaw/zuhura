import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import {
  X,
  Maximize2,
  Minimize2,
  RotateCw,
  Eye,
  Sliders,
  Sparkles,
  Layers,
  Info,
} from 'lucide-react';
import { useGlobeStore } from '../store/globeStore';

interface LayerInfo {
  id: string;
  name: string;
  depth: string;
  thickness: string;
  density: string;
  vp: string;
  vs: string;
  state: string;
  composition: string;
  color: string;
  citation: string;
}

const INTERIOR_LAYERS_SPEC: LayerInfo[] = [
  {
    id: 'crust',
    name: 'Martian Crust (Upper / Middle / Lower)',
    depth: '0 – 45 km',
    thickness: '45 km (avg)',
    density: '2,600 – 3,100 kg/m³',
    vp: '2.8 – 6.2 km/s',
    vs: '1.6 – 3.6 km/s',
    state: 'Brittle to ductile solid',
    composition: 'Porous basaltic regolith, fractured lava flows, and dense mafic granulite.',
    color: '#c85a32',
    citation: 'Knapmeyer-Endrun et al., Science 2021',
  },
  {
    id: 'lithosphere',
    name: 'Lithospheric Mantle',
    depth: '45 – 500 km',
    thickness: '455 km',
    density: '3,450 kg/m³',
    vp: '7.9 km/s',
    vs: '4.4 km/s',
    state: 'Rigid solid',
    composition: 'Depleted peridotite, olivine-rich crystalline mantle, thermal boundary layer.',
    color: '#606c38',
    citation: 'Khan et al., Science 2021',
  },
  {
    id: 'mantle',
    name: 'Upper & Lower Convective Mantle',
    depth: '500 – 1,570 km',
    thickness: '1,070 km',
    density: '3,700 – 4,100 kg/m³',
    vp: '8.6 – 9.8 km/s',
    vs: '4.8 – 5.4 km/s',
    state: 'Viscous solid (convecting)',
    composition: 'Wadsleyite, ringwoodite, and high-pressure silicate bridgmanite.',
    color: '#b08968',
    citation: 'Stähler et al., Science 2021',
  },
  {
    id: 'slag',
    name: 'Basal Molten Silicate Slag Layer (CMB)',
    depth: '1,570 – 1,720 km',
    thickness: '~150 km',
    density: '4,400 kg/m³',
    vp: '7.2 km/s (depressed)',
    vs: '2.9 km/s (attenuated)',
    state: 'Molten to partially molten silicate',
    composition: 'Basal magma ocean remnant enriched in iron and heat-producing elements (Th, U).',
    color: '#ffb703',
    citation: 'Samuel et al., Nature 2023',
  },
  {
    id: 'core',
    name: 'Liquid Metallic Outer Core',
    depth: '1,720 – 3,396 km',
    thickness: 'Radius 1,570 ± 30 km',
    density: '6,100 – 7,100 kg/m³',
    vp: '5.1 km/s',
    vs: '0.0 km/s (Liquid Core S-Shadow)',
    state: 'Liquid metallic alloy',
    composition: 'Liquid Fe-Ni with 15–18 wt% light elements (S, C, O, H).',
    color: '#e63946',
    citation: 'Stähler et al., Science 2021; Khan et al. 2023',
  },
];

/**
 * Creates a procedural 2D canvas texture for the outer Martian surface shell.
 */
function createMarsSurfaceTexture(): THREE.CanvasTexture {
  const canvas = document.createElement('canvas');
  canvas.width = 1024;
  canvas.height = 512;
  const ctx = canvas.getContext('2d')!;

  // Base Martian reddish-ochre gradient
  const grad = ctx.createLinearGradient(0, 0, 0, 512);
  grad.addColorStop(0, '#f0f4f8'); // North polar ice cap
  grad.addColorStop(0.12, '#9a4726');
  grad.addColorStop(0.35, '#c85a32'); // Northern Lowlands
  grad.addColorStop(0.65, '#a43e1d'); // Southern Highlands
  grad.addColorStop(0.88, '#822e14');
  grad.addColorStop(1.0, '#f0f4f8'); // South polar ice cap
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, 1024, 512);

  // Dark albedo features (Syrtis Major, Acidalia, Sinus Sabaeus)
  ctx.fillStyle = 'rgba(45, 24, 16, 0.45)';
  ctx.beginPath();
  ctx.ellipse(450, 240, 90, 60, 0.4, 0, Math.PI * 2);
  ctx.fill();

  ctx.beginPath();
  ctx.ellipse(320, 180, 120, 50, -0.2, 0, Math.PI * 2);
  ctx.fill();

  ctx.beginPath();
  ctx.ellipse(750, 310, 140, 70, 0.1, 0, Math.PI * 2);
  ctx.fill();

  // White polar caps
  ctx.fillStyle = '#ffffff';
  ctx.beginPath();
  ctx.ellipse(512, 18, 160, 22, 0, 0, Math.PI * 2);
  ctx.fill();

  ctx.beginPath();
  ctx.ellipse(512, 496, 140, 20, 0, 0, Math.PI * 2);
  ctx.fill();

  // Fine crater noise
  ctx.fillStyle = 'rgba(20, 10, 5, 0.15)';
  for (let i = 0; i < 400; i++) {
    const rx = Math.random() * 1024;
    const ry = 40 + Math.random() * 432;
    const rad = 2 + Math.random() * 6;
    ctx.beginPath();
    ctx.arc(rx, ry, rad, 0, Math.PI * 2);
    ctx.fill();
  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.ClampToEdgeWrapping;
  return texture;
}

export const XRayMars3DModal: React.FC = () => {
  const { isXRayMarsOpen, setIsXRayMarsOpen } = useGlobeStore();
  const mountRef = useRef<HTMLDivElement>(null);

  const [selectedLayer, setSelectedLayer] = useState<LayerInfo>(INTERIOR_LAYERS_SPEC[4]); // Core by default
  const [cutawayAngle, setCutawayAngle] = useState<number>(90); // 90° default quadrant cut
  const [autoRotate, setAutoRotate] = useState<boolean>(true);
  const [showSeismicRays, setShowSeismicRays] = useState<boolean>(true);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);

  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const layerMeshesRef = useRef<THREE.Mesh[]>([]);
  const seismicGroupRef = useRef<THREE.Group | null>(null);
  const animFrameIdRef = useRef<number>(0);

  useEffect(() => {
    if (!isXRayMarsOpen || !mountRef.current) return;

    const width = mountRef.current.clientWidth;
    const height = mountRef.current.clientHeight;

    // 1. Three.js Scene Setup
    const scene = new THREE.Scene();
    sceneRef.current = scene;
    scene.background = new THREE.Color(0x07080b);

    // Subtle star particles in background
    const starGeo = new THREE.BufferGeometry();
    const starCount = 600;
    const starPositions = new Float32Array(starCount * 3);
    for (let i = 0; i < starCount * 3; i += 3) {
      starPositions[i] = (Math.random() - 0.5) * 80;
      starPositions[i + 1] = (Math.random() - 0.5) * 80;
      starPositions[i + 2] = (Math.random() - 0.5) * 80;
    }
    starGeo.setAttribute('position', new THREE.BufferAttribute(starPositions, 3));
    const starMat = new THREE.PointsMaterial({ color: 0x8892b0, size: 0.15, transparent: true, opacity: 0.7 });
    scene.add(new THREE.Points(starGeo, starMat));

    // 2. Camera Setup
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(2.8, 1.8, 3.8);
    cameraRef.current = camera;

    // 3. WebGL Renderer with Antialiasing
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.localClippingEnabled = true;
    rendererRef.current = renderer;
    mountRef.current.appendChild(renderer.domElement);

    // 4. OrbitControls for 3D Navigation
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.minDistance = 1.4;
    controls.maxDistance = 12.0;
    controlsRef.current = controls;

    // 5. Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.65);
    scene.add(ambientLight);

    const sunLight = new THREE.DirectionalLight(0xffecd2, 1.2);
    sunLight.position.set(5, 4, 3);
    scene.add(sunLight);

    const backRimLight = new THREE.DirectionalLight(0x4cc9f0, 0.4);
    backRimLight.position.set(-4, -2, -3);
    scene.add(backRimLight);

    // Core point light for radiant heat
    const coreLight = new THREE.PointLight(0xff9e00, 1.5, 6);
    scene.add(coreLight);

    // 6. Mars Surface Texture
    const marsSurfaceTex = createMarsSurfaceTexture();

    // 7. Concentric Cutaway Spheres
    // Layer radii (scale normalized to R_surface = 2.0)
    const layerDefs = [
      { id: 'core', radius: 0.92, color: 0xe63946, roughness: 0.2, metalness: 0.7, emissive: 0x661100, emissiveIntensity: 0.45 },
      { id: 'slag', radius: 1.05, color: 0xffb703, roughness: 0.4, metalness: 0.3, emissive: 0x442200, emissiveIntensity: 0.35 },
      { id: 'mantle', radius: 1.55, color: 0xb08968, roughness: 0.6, metalness: 0.1, emissive: 0x110500, emissiveIntensity: 0.1 },
      { id: 'lithosphere', radius: 1.88, color: 0x606c38, roughness: 0.5, metalness: 0.1, emissive: 0x051105, emissiveIntensity: 0.1 },
      { id: 'crust', radius: 2.0, color: 0xc85a32, roughness: 0.8, metalness: 0.05, map: marsSurfaceTex },
    ];

    const meshes: THREE.Mesh[] = [];
    const radCut = (cutawayAngle * Math.PI) / 180;

    layerDefs.forEach((def, index) => {
      // Sphere with cutaway wedge
      const phiLength = Math.PI * 2 - radCut;
      const geom = new THREE.SphereGeometry(def.radius, 64, 32, radCut, phiLength);

      let mat: THREE.Material;
      if (def.map) {
        mat = new THREE.MeshStandardMaterial({
          map: def.map,
          roughness: def.roughness,
          metalness: def.metalness,
          side: THREE.DoubleSide,
        });
      } else {
        mat = new THREE.MeshStandardMaterial({
          color: def.color,
          roughness: def.roughness,
          metalness: def.metalness,
          emissive: def.emissive || 0x000000,
          emissiveIntensity: def.emissiveIntensity || 0,
          side: THREE.DoubleSide,
        });
      }

      const mesh = new THREE.Mesh(geom, mat);
      mesh.userData = { layerId: def.id, index: index, baseRadius: def.radius };
      scene.add(mesh);
      meshes.push(mesh);
    });
    layerMeshesRef.current = meshes;

    // 8. 3D Seismic Ray Paths
    const seismicGroup = new THREE.Group();
    seismicGroupRef.current = seismicGroup;

    // Epicenter marker at Cerberus Fossae (~10°N, 150°E)
    const epicenter = new THREE.Vector3(1.2, 0.4, 1.5).normalize().multiplyScalar(2.02);
    const epiMesh = new THREE.Mesh(
      new THREE.SphereGeometry(0.04, 16, 16),
      new THREE.MeshBasicMaterial({ color: 0xff0044 })
    );
    epiMesh.position.copy(epicenter);
    seismicGroup.add(epiMesh);

    // Generate 8 curved P and S wave ray paths through the interior
    for (let k = 0; k < 8; k++) {
      const angle = (k / 8) * Math.PI * 1.5 + 0.3;
      const target = new THREE.Vector3(
        Math.cos(angle) * 2.0,
        (Math.random() - 0.5) * 0.8,
        Math.sin(angle) * 2.0
      );

      // Deep inflection point near CMB
      const midDepth = 0.95 + (k / 8) * 0.6;
      const midPoint = epicenter.clone().lerp(target, 0.5).normalize().multiplyScalar(midDepth);

      const curve = new THREE.QuadraticBezierCurve3(epicenter, midPoint, target);
      const points = curve.getPoints(30);
      const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
      const isPwave = k % 2 === 0;
      const lineMat = new THREE.LineBasicMaterial({
        color: isPwave ? 0x00f0ff : 0xff9900,
        transparent: true,
        opacity: 0.75,
        linewidth: 2,
      });
      const rayLine = new THREE.Line(lineGeo, lineMat);
      seismicGroup.add(rayLine);
    }
    scene.add(seismicGroup);

    // 9. Raycasting for Interactive 3D Layer Picking
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    const handlePointerDown = (event: MouseEvent) => {
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObjects(layerMeshesRef.current);
      if (intersects.length > 0) {
        const hit = intersects[0].object;
        const layerId = hit.userData.layerId;
        const info = INTERIOR_LAYERS_SPEC.find((l) => l.id === layerId);
        if (info) setSelectedLayer(info);
      }
    };

    renderer.domElement.addEventListener('pointerdown', handlePointerDown);

    // 10. Animation Loop
    const animate = () => {
      animFrameIdRef.current = requestAnimationFrame(animate);

      if (autoRotate && controlsRef.current) {
        scene.rotation.y += 0.003;
      }

      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    // Resize Handler
    const handleResize = () => {
      if (!mountRef.current || !rendererRef.current || !cameraRef.current) return;
      const w = mountRef.current.clientWidth;
      const h = mountRef.current.clientHeight;
      cameraRef.current.aspect = w / h;
      cameraRef.current.updateProjectionMatrix();
      rendererRef.current.setSize(w, h);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (renderer.domElement) {
        renderer.domElement.removeEventListener('pointerdown', handlePointerDown);
      }
      cancelAnimationFrame(animFrameIdRef.current);
      renderer.dispose();
      if (mountRef.current && renderer.domElement) {
        mountRef.current.removeChild(renderer.domElement);
      }
    };
  }, [isXRayMarsOpen]);

  // Update cutaway angle dynamically on 3D meshes
  useEffect(() => {
    if (!sceneRef.current) return;
    const radCut = (cutawayAngle * Math.PI) / 180;
    const phiLength = Math.PI * 2 - radCut;

    layerMeshesRef.current.forEach((mesh) => {
      const baseR = mesh.userData.baseRadius;
      mesh.geometry.dispose();
      mesh.geometry = new THREE.SphereGeometry(baseR, 64, 32, radCut, phiLength);
    });
  }, [cutawayAngle]);

  // Toggle seismic waves
  useEffect(() => {
    if (seismicGroupRef.current) {
      seismicGroupRef.current.visible = showSeismicRays;
    }
  }, [showSeismicRays]);

  const handleResetCamera = () => {
    if (!cameraRef.current || !controlsRef.current || !sceneRef.current) return;
    cameraRef.current.position.set(2.8, 1.8, 3.8);
    controlsRef.current.target.set(0, 0, 0);
    sceneRef.current.rotation.set(0, 0, 0);
    controlsRef.current.update();
  };

  if (!isXRayMarsOpen) return null;

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center p-3 md:p-6 bg-brand-950/45 transition-all ${
        isFullscreen ? 'p-0' : ''
      }`}
    >
      <div
        className={`relative flex flex-col bg-surface-subtle border border-line rounded-2xl shadow-2xl overflow-hidden transition-all duration-200 ${
          isFullscreen ? 'w-full h-full rounded-none border-none' : 'w-full max-w-6xl h-[88vh]'
        }`}
      >
        {/* Top Header Bar */}
        <div className="flex items-center justify-between px-5 py-3.5 bg-white border-b border-line shrink-0 select-none">
          <div className="flex items-center space-x-3">
            <div>
              <p className="text-[12px] font-medium text-brand-600">X-ray</p>
              <h3 className="text-base font-semibold tracking-tight text-ink">
                Interior of Mars
              </h3>
              <p className="text-[13px] text-ink-muted">
                Drag to turn the planet, scroll to move inward, and choose a layer to read what it is.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleResetCamera}
              className="p-1.5 rounded-lg bg-surface-muted hover:bg-surface-muted text-ink-soft transition-colors"
              title="Reset 3D Viewpoint"
            >
              <RotateCw className="w-4 h-4" />
            </button>
            <button
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="p-1.5 rounded-lg bg-surface-muted hover:bg-surface-muted text-ink-soft transition-colors"
              title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
            >
              {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            </button>
            <button
              onClick={() => setIsXRayMarsOpen(false)}
              className="p-1.5 rounded-lg bg-surface-muted hover:bg-brand-50 text-ink-soft hover:text-brand-600 transition-colors"
              title="Close 3D X-Ray Model"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Central Workspace: 3D Canvas + Interactive Floating Controls + Side Telemetry */}
        <div className="relative flex-1 w-full h-full overflow-hidden flex flex-col md:flex-row">
          {/* 3D WebGL Canvas Viewport */}
          <div ref={mountRef} className="relative min-h-[220px] flex-1 w-full h-full cursor-grab active:cursor-grabbing">
            {/* 3D Viewport Controls HUD Overlay */}
            <div className="absolute top-4 left-4 z-20 flex flex-col space-y-2 p-3 rounded-xl bg-surface-muted border border-line shadow-xl text-xs font-mono select-none w-64">
              <div className="flex items-center justify-between pb-1.5 border-b border-line text-ink-soft font-bold">
                <span className="flex items-center space-x-1.5">
                  <Sliders className="w-3.5 h-3.5 text-brand-600" />
                  <span>Cutaway</span>
                </span>
              </div>

              {/* Cutaway Angle Slider */}
              <div className="space-y-1">
                <div className="flex justify-between text-[11px] text-ink-muted">
                  <span>Cutaway Slice:</span>
                  <span className="text-brand-600 font-bold">{cutawayAngle}°</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="180"
                  step="5"
                  value={cutawayAngle}
                  onChange={(e) => setCutawayAngle(Number(e.target.value))}
                  className="w-full accent-brand-600 cursor-pointer h-1.5 bg-surface-muted rounded-lg"
                />
              </div>

              {/* Toggle Buttons */}
              <div className="pt-1.5 flex items-center justify-between gap-2">
                <button
                  onClick={() => setAutoRotate(!autoRotate)}
                  className={`flex-1 py-1 px-2 rounded text-[10px] font-mono border transition-colors ${
                    autoRotate
                      ? 'bg-brand-50 text-brand-600 border-brand-200'
                      : 'bg-surface-muted text-ink-muted border-line'
                  }`}
                >
                  {autoRotate ? 'Auto-Orbit: ON' : 'Orbit: OFF'}
                </button>
                <button
                  onClick={() => setShowSeismicRays(!showSeismicRays)}
                  className={`flex-1 py-1 px-2 rounded text-[10px] font-mono border transition-colors ${
                    showSeismicRays
                      ? 'bg-surface-subtle text-ink border-line'
                      : 'bg-surface-muted text-ink-muted border-line'
                  }`}
                >
                  {showSeismicRays ? 'Seismic: ON' : 'Seismic: OFF'}
                </button>
              </div>
            </div>

            {/* Bottom 3D Navigation Guide Tip */}
            <div className="absolute bottom-4 left-4 z-20 flex items-center space-x-2 px-3 py-1.5 rounded-full bg-surface-muted border border-line text-[10px] font-mono text-ink-muted select-none pointer-events-none">
              <Eye className="w-3.5 h-3.5 text-ink" />
              <span>Left Click + Drag: Orbit in 3D | Scroll: Zoom to Core | Right Click: Pan</span>
            </div>
          </div>

          {/* Right Scientific Layer Telemetry Inspector Panel */}
          <div className="w-full md:w-80 lg:w-96 max-h-[48%] md:max-h-none bg-surface-subtle border-t md:border-t-0 md:border-l border-line p-5 flex flex-col justify-between shrink-0 overflow-y-auto font-sans select-none">
            <div className="space-y-4">
              {/* Header */}
              <div className="pb-3 border-b border-line">
                <div className="flex items-center space-x-2 text-[10px] text-brand-600">
                  <Layers className="w-3.5 h-3.5" />
                  <span>Selected layer</span>
                </div>
                <h4 className="text-base font-bold text-ink mt-1">{selectedLayer.name}</h4>
                <div className="mt-1 flex items-center space-x-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-surface-muted text-ink-soft">
                    Depth: {selectedLayer.depth}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-surface-subtle text-ink border border-line">
                    {selectedLayer.thickness}
                  </span>
                </div>
              </div>

              {/* Physical Parameters Grid */}
              <div className="grid grid-cols-2 gap-2.5 font-mono text-xs">
                <div className="p-2.5 rounded-lg bg-white border border-line">
                  <div className="text-[10px] text-ink-muted uppercase">Bulk Density (ρ)</div>
                  <div className="text-xs font-bold text-ink-soft mt-0.5">{selectedLayer.density}</div>
                </div>

                <div className="p-2.5 rounded-lg bg-white border border-line">
                  <div className="text-[10px] text-ink-muted uppercase">State of Matter</div>
                  <div className="text-xs font-bold text-brand-600 mt-0.5">{selectedLayer.state}</div>
                </div>

                <div className="p-2.5 rounded-lg bg-white border border-line">
                  <div className="text-[10px] text-ink uppercase">P-Wave Velocity (Vp)</div>
                  <div className="text-xs font-bold text-ink mt-0.5">{selectedLayer.vp}</div>
                </div>

                <div className="p-2.5 rounded-lg bg-white border border-line">
                  <div className="text-[10px] text-ink uppercase">S-Wave Velocity (Vs)</div>
                  <div className="text-xs font-bold text-ink mt-0.5">{selectedLayer.vs}</div>
                </div>
              </div>

              {/* Composition & Geochemical Interpretation */}
              <div className="space-y-1.5 p-3 rounded-lg bg-white border border-line">
                <div className="text-[10px] text-ink-muted flex items-center space-x-1">
                  <Sparkles className="w-3 h-3 text-brand-600" />
                  <span>Mineralogy & Geochemistry</span>
                </div>
                <p className="text-xs text-ink-soft leading-relaxed font-sans">{selectedLayer.composition}</p>
              </div>

              {/* Peer-Reviewed Ground Truth Citation */}
              <div className="p-2.5 rounded-lg bg-surface-subtle border border-line text-[11px] font-sans text-ink-muted flex items-start space-x-2">
                <Info className="w-3.5 h-3.5 text-ink shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold text-ink-soft">Reference:</span> {selectedLayer.citation}
                </div>
              </div>

              {/* Interactive Layer Selector Buttons */}
              <div className="space-y-1.5 pt-2">
                <div className="text-[10px] text-ink-muted">Quick Layer Selector:</div>
                <div className="flex flex-col space-y-1 font-mono text-[11px]">
                  {INTERIOR_LAYERS_SPEC.map((layer) => (
                    <button
                      key={layer.id}
                      onClick={() => setSelectedLayer(layer)}
                      className={`py-1.5 px-3 rounded-lg text-left transition-all border flex items-center justify-between ${
                        selectedLayer.id === layer.id
                          ? 'bg-brand-50 border-brand-600 text-brand-600 font-bold'
                          : 'bg-white border-line text-ink-muted hover:text-ink hover:border-line-strong'
                      }`}
                    >
                      <span>{layer.name.split(' (')[0]}</span>
                      <span className="text-[10px] text-ink-faint">{layer.depth}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="pt-3 border-t border-line text-[10px] font-mono text-ink-faint text-center">
              Zuhura Mars 3D Interior Engine • InSight SEIS Data Integration
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
