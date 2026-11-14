import { create } from 'zustand';

export interface ScientificLayer {
  id: string;
  name: string;
  category: 'topography' | 'imagery' | 'geology' | 'mineralogy' | 'missions';
  provider: string;
  resolution: string;
  visible: boolean;
  opacity: number;
  description: string;
  citation: string;
}

interface LayerState {
  layers: ScientificLayer[];
  toggleLayer: (id: string) => void;
  setOpacity: (id: string, opacity: number) => void;
}

const DEFAULT_LAYERS: ScientificLayer[] = [
  {
    id: 'zuhura-viking-mdim21',
    name: 'Viking MDIM 2.1 Natural Color Mosaic',
    category: 'imagery',
    provider: 'USGS Astrogeology / NASA PDS',
    resolution: '232 m/px (L0–10)',
    visible: true,
    opacity: 1.0,
    description:
      'Orthorectified global true-color optical mosaic from Viking Orbiters 1 & 2. Authoritative natural Mars surface basemap.',
    citation: 'Archinal et al. (2003), USGS Open-File',
  },
  {
    id: 'zuhura-ctx-jezero',
    name: 'MRO CTX Western Delta Mosaic',
    category: 'imagery',
    provider: 'MSSS / NASA PDS',
    resolution: '5.55 m/px (L9–15)',
    visible: true,
    opacity: 1.0,
    description: 'Context Camera calibrated radiance mosaic draped over Western Jezero delta fan and crater floor.',
    citation: 'Malin et al. (2007), JGR Planets',
  },
  {
    id: 'zuhura-hirise-jezero',
    name: 'MRO HiRISE Perseverance Touchdown',
    category: 'imagery',
    provider: 'UArizona / NASA PDS / HiRISE',
    resolution: '0.50 m/px (L13–18)',
    visible: true,
    opacity: 1.0,
    description: 'Sub-meter targeted observation footprint over Octavia E. Butler touchdown ellipse and delta scarp.',
    citation: 'McEwen et al. (2007), JGR Planets',
  },
  {
    id: 'zuhura-mola-global-v3-cog',
    name: 'MOLA Topographic Colormap (Elevation)',
    category: 'topography',
    provider: 'NASA GSFC / MOLA Science Team',
    resolution: '463 m/px (L0–7)',
    visible: false,
    opacity: 0.75,
    description:
      'Cloud-Optimized GeoTIFF streaming with dynamic scientific color ramp and zero-elevation datum preservation. Toggle to overlay topography.',
    citation: 'Smith et al. (2001) / Zuhura Stage 3 & 6',
  },
  {
    id: 'zuhura-mola-megdr-128',
    name: 'MOLA Topography & Hillshade',
    category: 'topography',
    provider: 'NASA PDS Geosciences',
    resolution: '463 m/px',
    visible: false,
    opacity: 0.8,
    description: 'Mars Orbiter Laser Altimeter global gridded terrain elevation model referenced to GMM-3 areoid.',
    citation: 'Smith et al. (2001), JGR Planets',
  },
  {
    id: 'zuhura-themis-ir-jezero',
    name: 'THEMIS Daytime IR (Jezero Crater)',
    category: 'mineralogy',
    provider: 'ASU / NASA PDS',
    resolution: '100 m/px',
    visible: false,
    opacity: 0.8,
    description:
      'Thermal Emission Imaging System calibrated infrared mosaic (Band 9, 12.57 um) measuring surface thermophysical properties.',
    citation: 'Christensen et al. (2004), Space Science Reviews',
  },
  {
    id: 'zuhura-usgs-sim3292',
    name: 'USGS Global Geologic Map (SIM 3292)',
    category: 'geology',
    provider: 'USGS Astrogeology',
    resolution: '1,000 m/px',
    visible: false,
    opacity: 0.6,
    description: 'Global 1:20M-scale stratigraphic unit boundaries and geological contacts.',
    citation: 'Tanaka et al. (2014), USGS SIM 3292',
  },
  {
    id: 'zuhura-landing-sites',
    name: 'Mars Missions & Landing Sites',
    category: 'missions',
    provider: 'NASA / ESA / CNSA',
    resolution: 'In-situ',
    visible: true,
    opacity: 1.0,
    description: 'Traverses, landing ellipses, and surface exploration sites.',
    citation: 'Planetary Data System Analyst Notebook',
  },
  {
    id: 'zuhura-mola-hrsc-blend',
    name: 'MGS MOLA & MEX HRSC Blended Color Hillshade',
    category: 'topography',
    provider: 'NASA / ESA / DLR / Solar System Treks',
    resolution: '200 m/px (L0–9)',
    visible: false,
    opacity: 0.85,
    description:
      'High-resolution blend of MOLA laser altimetry and Mars Express High Resolution Stereo Camera topographic relief.',
    citation: 'NASA Mars Trek / DLR HRSC Team',
  },
  {
    id: 'zuhura-themis-day-ir',
    name: 'THEMIS-IR Daytime Global Thermal Mosaic',
    category: 'imagery',
    provider: 'ASU / NASA PDS / Mars Odyssey',
    resolution: '100 m/px (L0–9)',
    visible: false,
    opacity: 0.8,
    description:
      'Controlled thermal infrared radiance mosaic measuring Martian thermophysical inertia and surface bedrock exposure.',
    citation: 'Christensen et al. (2004), Space Science Reviews',
  },
  {
    id: 'zuhura-tes-clinopyroxene',
    name: 'MGS TES Clinopyroxene (High-Ca Pyroxene)',
    category: 'mineralogy',
    provider: 'ASU / NASA GSFC TES Team',
    resolution: '3,000 m/px',
    visible: false,
    opacity: 0.75,
    description:
      'Thermal Emission Spectrometer global abundance mapping of calcium-rich clinopyroxene in basaltic terrains.',
    citation: 'Bandfield et al. (2000), Science / Mars Trek',
  },
  {
    id: 'zuhura-mount-sharp-route',
    name: 'Curiosity Mount Sharp Exploration Route',
    category: 'missions',
    provider: 'NASA / JPL-Caltech / MRO / MSL',
    resolution: 'Sub-meter (PIA23179)',
    visible: true,
    opacity: 1.0,
    description:
      'Curiosity traverse and proposed ascent route up Mount Sharp (Aeolis Mons) through Vera Rubin Ridge and Glen Torridon clays.',
    citation: 'NASA Science / JPL Photojournal PIA23179',
  },
];

export const useLayerStore = create<LayerState>((set) => ({
  layers: DEFAULT_LAYERS,
  toggleLayer: (id) =>
    set((state) => ({
      layers: state.layers.map((l) => (l.id === id ? { ...l, visible: !l.visible } : l)),
    })),
  setOpacity: (id, opacity) =>
    set((state) => ({
      layers: state.layers.map((l) => (l.id === id ? { ...l, opacity: Math.max(0, Math.min(1, opacity)) } : l)),
    })),
}));
