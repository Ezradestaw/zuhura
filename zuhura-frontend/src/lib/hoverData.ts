/**
 * Zuhura Mars - Instant Client-Side Planetary Gazetteer & Dynamic Hover Intelligence Engine
 * Auto-compiled from authoritative IAU nomenclature and regional geological mapping.
 */

export interface MarsFeatureItem {
  id: string;
  name: string;
  type: string;
  category: string;
  lat: number;
  lon: number;
  diameter_km: number;
  elevation_m: number;
  description: string;
  [key: string]: any;
}

export interface MarsRegionItem {
  id: string;
  name: string;
  type: string;
  center: [number, number];
  bounds: number[][];
  description: string;
  geology: string;
  [key: string]: any;
}

export interface HoverPlaceInfo {
  name: string;
  category: string;
  description: string;
  geologicalEra: string;
  elevation_m: number;
  distance_km?: number;
  isSpecificFeature: boolean;
}

export const MARS_HOVER_FEATURES: MarsFeatureItem[] = [
  {
    id: 'olympus-mons',
    name: 'Olympus Mons',
    type: 'Mons (Shield Volcano)',
    category: 'mons',
    lat: 18.65,
    lon: -133.8,
    diameter_km: 624.0,
    elevation_m: 21287,
    description:
      'The largest planetary shield volcano and mountain in the solar system, standing ~22 km above surrounding plains with a 80 km caldera.',
    origin_of_name: 'Mount Olympus, home of the gods in Greek mythology.',
    iau_approval_year: 1973,
  },
  {
    id: 'ascraeus-mons',
    name: 'Ascraeus Mons',
    type: 'Mons (Shield Volcano)',
    category: 'mons',
    lat: 11.92,
    lon: -104.08,
    diameter_km: 462.0,
    elevation_m: 18225,
    description: 'Northernmost of the three Tharsis Montes shield volcanoes, rising over 18 km above datum.',
    origin_of_name: 'Classical albedo feature named after Ascra, birthplace of Hesiod.',
    iau_approval_year: 1973,
  },
  {
    id: 'pavonis-mons',
    name: 'Pavonis Mons',
    type: 'Mons (Shield Volcano)',
    category: 'mons',
    lat: 0.8,
    lon: -112.96,
    diameter_km: 375.0,
    elevation_m: 14058,
    description: 'Central shield volcano of Tharsis Montes, situated right on the Martian equator.',
    origin_of_name: 'Named after the Peacock constellation (Pavo).',
    iau_approval_year: 1973,
  },
  {
    id: 'arsia-mons',
    name: 'Arsia Mons',
    type: 'Mons (Shield Volcano)',
    category: 'mons',
    lat: -8.4,
    lon: -121.11,
    diameter_km: 435.0,
    elevation_m: 17761,
    description: 'Southernmost Tharsis Montes volcano with a gigantic 110-km caldera and lava tubes.',
    origin_of_name: 'Named after the ancient Roman forest Arsia Silva.',
    iau_approval_year: 1973,
  },
  {
    id: 'elysium-mons',
    name: 'Elysium Mons',
    type: 'Mons (Shield Volcano)',
    category: 'mons',
    lat: 25.02,
    lon: 147.21,
    diameter_km: 410.0,
    elevation_m: 13900,
    description: 'Major shield volcano towering 13.9 km above the volcanic plains of Elysium Planitia.',
    origin_of_name: 'From Greek mythology Elysium, the island of the blessed.',
    iau_approval_year: 1973,
  },
  {
    id: 'alba-mons',
    name: 'Alba Mons (Alba Patera)',
    type: 'Mons (Low-profile Volcano)',
    category: 'mons',
    lat: 40.5,
    lon: -109.9,
    diameter_km: 1600.0,
    elevation_m: 6800,
    description: 'The largest volcano on Mars in terms of surface area and span, with extremely gentle flank slopes.',
    origin_of_name: "Albedo feature meaning 'white mountain'.",
    iau_approval_year: 1973,
  },
  {
    id: 'hecate-tholus',
    name: 'Hecates Tholus',
    type: 'Tholus (Small Dome)',
    category: 'tholus',
    lat: 32.12,
    lon: 150.24,
    diameter_km: 183.0,
    elevation_m: 5300,
    description:
      'Volcano in northern Elysium showing signs of explosive eruptions and glacial activity in its caldera.',
    origin_of_name: 'Named after Hecate, goddess of magic and crossroads.',
    iau_approval_year: 1973,
  },
  {
    id: 'albor-tholus',
    name: 'Albor Tholus',
    type: 'Tholus (Small Dome)',
    category: 'tholus',
    lat: 19.0,
    lon: 150.47,
    diameter_km: 160.0,
    elevation_m: 4500,
    description: 'Extinct volcano south of Elysium Mons with a dramatic 3 km deep summit caldera.',
    origin_of_name: 'Classical albedo feature.',
    iau_approval_year: 1973,
  },
  {
    id: 'uranius-mons',
    name: 'Uranius Mons',
    type: 'Mons (Volcano)',
    category: 'mons',
    lat: 26.9,
    lon: -92.8,
    diameter_km: 265.0,
    elevation_m: 4500,
    description: 'Older volcano north of Tharsis Montes, heavily impacted and eroded.',
    origin_of_name: 'Classical albedo feature named for Urania, muse of astronomy.',
    iau_approval_year: 1973,
  },
  {
    id: 'ceraunius-tholus',
    name: 'Ceraunius Tholus',
    type: 'Tholus (Small Volcano)',
    category: 'tholus',
    lat: 24.25,
    lon: -97.4,
    diameter_km: 130.0,
    elevation_m: 8500,
    description: 'Steep-sided volcano carved by deep radial gullies with a prominent summit crater.',
    origin_of_name: 'Named after Ceraunian Mountains in ancient Epirus.',
    iau_approval_year: 1973,
  },
  {
    id: 'biblis-tholus',
    name: 'Biblis Tholus',
    type: 'Tholus (Volcano Dome)',
    category: 'tholus',
    lat: 2.55,
    lon: -124.62,
    diameter_km: 170.0,
    elevation_m: 7100,
    description: 'Intermediate volcano west of Pavonis Mons with an elongated caldera.',
    origin_of_name: 'Biblis, classical albedo feature.',
    iau_approval_year: 1973,
  },
  {
    id: 'ulysses-tholus',
    name: 'Ulysses Tholus',
    type: 'Tholus (Volcano Dome)',
    category: 'tholus',
    lat: 2.97,
    lon: -121.55,
    diameter_km: 102.0,
    elevation_m: 5400,
    description: 'Volcanic dome immediately east of Biblis Tholus.',
    origin_of_name: 'Named after Homeric hero Ulysses.',
    iau_approval_year: 1973,
  },
  {
    id: 'jovis-tholus',
    name: 'Jovis Tholus',
    type: 'Tholus (Volcano Dome)',
    category: 'tholus',
    lat: 18.2,
    lon: -117.4,
    diameter_km: 58.0,
    elevation_m: 3000,
    description: 'Small caldera dome surrounded by vast Tharsis lava flows.',
    origin_of_name: 'Latin for Jupiter.',
    iau_approval_year: 1973,
  },
  {
    id: 'apollinaris-mons',
    name: 'Apollinaris Mons',
    type: 'Mons (Ancient Volcano)',
    category: 'mons',
    lat: -9.3,
    lon: 174.4,
    diameter_km: 296.0,
    elevation_m: 5000,
    description: 'Isolated shield volcano near Gusev Crater displaying pyroclastic deposits.',
    origin_of_name: 'Named after the spring Aquae Apollinares in Italy.',
    iau_approval_year: 1973,
  },
  {
    id: 'hadriacus-mons',
    name: 'Hadriacus Mons (Hadriaca Patera)',
    type: 'Patera / Mons',
    category: 'mons',
    lat: -31.29,
    lon: 91.86,
    diameter_km: 450.0,
    elevation_m: 1200,
    description: 'Ancient eroded volcano on the northeast rim of Hellas basin, source of Dao Vallis.',
    origin_of_name: 'Named after the Adriatic Sea.',
    iau_approval_year: 2007,
  },
  {
    id: 'tyrrhenus-mons',
    name: 'Tyrrhenus Mons (Tyrrhena Patera)',
    type: 'Patera / Mons',
    category: 'mons',
    lat: -21.36,
    lon: 106.53,
    diameter_km: 300.0,
    elevation_m: 3000,
    description: 'Eroded highland volcano east of Hellas Basin with radial gullies.',
    origin_of_name: 'Classical albedo feature named after Tyrrhenian Sea.',
    iau_approval_year: 2007,
  },
  {
    id: 'valles-marineris',
    name: 'Valles Marineris',
    type: 'Vallis (Grand Canyon System)',
    category: 'chasma',
    lat: -13.9,
    lon: -59.2,
    diameter_km: 4000.0,
    elevation_m: -7000,
    description:
      'The largest canyon system in the solar system, stretching over 4,000 km long, up to 200 km wide and 7 km deep.',
    origin_of_name: 'Named in honor of Mariner 9 orbiter team who discovered it in 1971-1972.',
    iau_approval_year: 1973,
  },
  {
    id: 'noctis-labyrinthus',
    name: 'Noctis Labyrinthus',
    type: 'Labyrinthus (Valley Maze)',
    category: 'chasma',
    lat: -6.36,
    lon: -101.19,
    diameter_km: 1140.0,
    elevation_m: 3000,
    description:
      "'The Labyrinth of Night' \u2014 an intricate network of deep, steep-walled intersecting grabens and valleys.",
    origin_of_name: 'Classical albedo feature.',
    iau_approval_year: 1973,
  },
  {
    id: 'melas-chasma',
    name: 'Melas Chasma',
    type: 'Chasma (Canyon Basin)',
    category: 'chasma',
    lat: -9.8,
    lon: -76.46,
    diameter_km: 547.0,
    elevation_m: -9000,
    description:
      'The widest central segment of Valles Marineris and its lowest point, sinking ~9 km below surrounding plains.',
    origin_of_name: 'Classical albedo feature.',
    iau_approval_year: 1973,
  },
  {
    id: 'candor-chasma',
    name: 'Candor Chasma',
    type: 'Chasma (Canyon)',
    category: 'chasma',
    lat: -6.53,
    lon: -75.78,
    diameter_km: 813.0,
    elevation_m: -7500,
    description:
      'Northern canyon of central Valles Marineris with dramatic layered sedimentary deposits and sulfate beds.',
    origin_of_name: 'Classical albedo feature meaning brightness.',
    iau_approval_year: 1973,
  },
  {
    id: 'ophir-chasma',
    name: 'Ophir Chasma',
    type: 'Chasma (Canyon)',
    category: 'chasma',
    lat: -4.0,
    lon: -72.5,
    diameter_km: 317.0,
    elevation_m: -7000,
    description:
      'Steep-walled northern arm of Valles Marineris filled with massive landslide debris and internal layered deposits.',
    origin_of_name: 'Biblical gold land of Ophir.',
    iau_approval_year: 1973,
  },
  {
    id: 'hebes-chasma',
    name: 'Hebes Chasma',
    type: 'Chasma (Closed Canyon Basin)',
    category: 'chasma',
    lat: 1.07,
    lon: -76.12,
    diameter_km: 317.0,
    elevation_m: -6000,
    description: 'A completely enclosed 8 km deep trough with a central flat-topped mesa (Hebes Mensa) rising 5 km.',
    origin_of_name: 'Named after Hebe, goddess of youth.',
    iau_approval_year: 1973,
  },
  {
    id: 'echus-chasma',
    name: 'Echus Chasma',
    type: 'Chasma (Canyon)',
    category: 'chasma',
    lat: 2.5,
    lon: -80.0,
    diameter_km: 391.0,
    elevation_m: -4000,
    description: 'Origin of the catastrophic outflow channel Kasei Valles, surrounded by 4 km sheer cliffs.',
    origin_of_name: 'Classical albedo feature Echo.',
    iau_approval_year: 1976,
  },
  {
    id: 'juventae-chasma',
    name: 'Juventae Chasma',
    type: 'Chasma (Canyon)',
    category: 'chasma',
    lat: -4.5,
    lon: -62.5,
    diameter_km: 320.0,
    elevation_m: -5000,
    description: 'Enclosed box canyon north of Valles Marineris, source of the Maja Valles outflow channel.',
    origin_of_name: 'Named after Juventas, fountain of youth.',
    iau_approval_year: 1973,
  },
  {
    id: 'ganges-chasma',
    name: 'Ganges Chasma',
    type: 'Chasma (Canyon)',
    category: 'chasma',
    lat: -7.9,
    lon: -48.1,
    diameter_km: 574.0,
    elevation_m: -6500,
    description: 'Eastern canyon branch connected to Capri Chasma with steep tiered walls.',
    origin_of_name: 'Named after the Ganges River.',
    iau_approval_year: 1973,
  },
  {
    id: 'capri-chasma',
    name: 'Capri Chasma',
    type: 'Chasma (Canyon)',
    category: 'chasma',
    lat: -8.27,
    lon: -42.12,
    diameter_km: 275.0,
    elevation_m: -4000,
    description: 'Eastern terminus of Valles Marineris opening out into chaotic terrain and outflow channels.',
    origin_of_name: 'Island of Capri in the Mediterranean.',
    iau_approval_year: 1973,
  },
  {
    id: 'eos-chasma',
    name: 'Eos Chasma',
    type: 'Chasma (Canyon)',
    category: 'chasma',
    lat: -12.15,
    lon: -39.17,
    diameter_km: 1306.0,
    elevation_m: -5000,
    description: 'Southern outflow channel gateway of Valles Marineris transitioning into chaotic terrain.',
    origin_of_name: 'Eos, Greek goddess of dawn.',
    iau_approval_year: 1973,
  },
  {
    id: 'ius-chasma',
    name: 'Ius Chasma',
    type: 'Chasma (Canyon)',
    category: 'chasma',
    lat: -7.29,
    lon: -84.39,
    diameter_km: 938.0,
    elevation_m: -6000,
    description: 'Western main trough of Valles Marineris with parallel fault-bounded canyons and scarp slumps.',
    origin_of_name: 'Classical albedo feature.',
    iau_approval_year: 1973,
  },
  {
    id: 'tithonium-chasma',
    name: 'Tithonium Chasma',
    type: 'Chasma (Canyon)',
    category: 'chasma',
    lat: -4.6,
    lon: -84.7,
    diameter_km: 803.0,
    elevation_m: -5500,
    description: 'Northern twin canyon of Ius Chasma in western Valles Marineris.',
    origin_of_name: 'Named after Tithonus, consort of Eos.',
    iau_approval_year: 1973,
  },
  {
    id: 'kasei-valles',
    name: 'Kasei Valles',
    type: 'Vallis (Outflow Channel)',
    category: 'vallis',
    lat: 24.6,
    lon: -65.0,
    diameter_km: 1780.0,
    elevation_m: -3000,
    description: 'Gigantic outflow channel carved by catastrophic floods discharging into Chryse Planitia.',
    origin_of_name: 'The word for Mars in Japanese (\u706b\u661f).',
    iau_approval_year: 1976,
  },
  {
    id: 'ares-vallis',
    name: 'Ares Vallis',
    type: 'Vallis (Outflow Channel)',
    category: 'vallis',
    lat: 10.3,
    lon: -25.8,
    diameter_km: 1700.0,
    elevation_m: -3500,
    description: 'Massive catastrophic flood channel where Mars Pathfinder and Sojourner landed in 1997.',
    origin_of_name: 'Ares, the Greek god of war.',
    iau_approval_year: 1979,
  },
  {
    id: 'tiu-vallis',
    name: 'Tiu Vallis',
    type: 'Vallis (Outflow Channel)',
    category: 'vallis',
    lat: 15.7,
    lon: -35.7,
    diameter_km: 1720.0,
    elevation_m: -3200,
    description: 'Major outflow channel originating in Aram Chaos and debouching into Chryse Planitia.',
    origin_of_name: 'Old English god of war (Tuesday).',
    iau_approval_year: 1979,
  },
  {
    id: 'simud-vallis',
    name: 'Simud Vallis',
    type: 'Vallis (Outflow Channel)',
    category: 'vallis',
    lat: 19.8,
    lon: -37.8,
    diameter_km: 945.0,
    elevation_m: -3400,
    description: 'Outflow channel emerging from Hydraotes Chaos showing streamlined teardrop islands.',
    origin_of_name: 'The word for Mars in Sumerian.',
    iau_approval_year: 1979,
  },
  {
    id: 'shalbatana-vallis',
    name: 'Shalbatana Vallis',
    type: 'Vallis (Valley)',
    category: 'vallis',
    lat: 7.8,
    lon: -42.1,
    diameter_km: 1029.0,
    elevation_m: -2800,
    description: 'Sinuous channel containing evidence of paleolakes and catastrophic flooding.',
    origin_of_name: 'The word for Mars in Akkadian.',
    iau_approval_year: 1979,
  },
  {
    id: 'maadim-vallis',
    name: "Ma'adim Vallis",
    type: 'Vallis (Canyon / Spillway)',
    category: 'vallis',
    lat: -21.6,
    lon: 177.3,
    diameter_km: 825.0,
    elevation_m: -1500,
    description: 'Enormous gorge that drained a massive highland paleolake into Gusev Crater where Spirit landed.',
    origin_of_name: 'The word for Mars in Hebrew (\u05de\u05d0\u05d3\u05d9\u05dd).',
    iau_approval_year: 1976,
  },
  {
    id: 'nirgal-vallis',
    name: 'Nirgal Vallis',
    type: 'Vallis (Tributary River Valley)',
    category: 'vallis',
    lat: -28.2,
    lon: -42.0,
    diameter_km: 496.0,
    elevation_m: -500,
    description: 'Classic amphitheater-headed branching valley system formed by groundwater sapping.',
    origin_of_name: 'The word for Mars in Babylonian.',
    iau_approval_year: 1973,
  },
  {
    id: 'nanedi-valles',
    name: 'Nanedi Valles',
    type: 'Vallis (Meandering Valley)',
    category: 'vallis',
    lat: 4.9,
    lon: -48.2,
    diameter_km: 508.0,
    elevation_m: -1000,
    description: 'Meandering canyon in Xanthe Terra with deeply incised inner channels.',
    origin_of_name: 'Word for Mars in Sesotho.',
    iau_approval_year: 1976,
  },
  {
    id: 'mawrth-vallis',
    name: 'Mawrth Vallis',
    type: 'Vallis (Ancient Valley)',
    category: 'vallis',
    lat: 23.99,
    lon: -18.96,
    diameter_km: 636.0,
    elevation_m: -2000,
    description: 'One of the oldest valleys on Mars, exposing thick phyllosilicate clay beds vital to astrobiology.',
    origin_of_name: 'The word for Mars in Welsh.',
    iau_approval_year: 1976,
  },
  {
    id: 'athabasca-valles',
    name: 'Athabasca Valles',
    type: 'Vallis (Young Flood Channel)',
    category: 'vallis',
    lat: 9.8,
    lon: 156.0,
    diameter_km: 285.0,
    elevation_m: -2500,
    description: 'Geologically young channel in Elysium carved by catastrophic water release from Cerberus Fossae.',
    origin_of_name: 'Athabasca River in Canada.',
    iau_approval_year: 1997,
  },
  {
    id: 'mangala-valles',
    name: 'Mangala Valles',
    type: 'Vallis (Outflow Channel)',
    category: 'vallis',
    lat: -11.5,
    lon: -151.0,
    diameter_km: 828.0,
    elevation_m: -1200,
    description: 'Outflow network originating at a graben in Memnonia Fossae.',
    origin_of_name: 'The word for Mars in Sanskrit (\u092e\u0919\u094d\u0917\u0932).',
    iau_approval_year: 1979,
  },
  {
    id: 'dao-vallis',
    name: 'Dao Vallis',
    type: 'Vallis (Channel)',
    category: 'vallis',
    lat: -38.7,
    lon: 87.9,
    diameter_km: 1200.0,
    elevation_m: -3500,
    description: 'Valley cutting into the northeast floor of Hellas basin from Hadriacus Mons.',
    origin_of_name: 'The word for star/Mars in Thai (\u0e14\u0e32\u0e27).',
    iau_approval_year: 1979,
  },
  {
    id: 'crater-jezero',
    name: 'Jezero Crater',
    type: 'Crater (Paleolake Basin)',
    category: 'crater',
    lat: 18.38,
    lon: 77.58,
    diameter_km: 49.0,
    elevation_m: -2500,
    description:
      'Ancient lake basin hosting a well-preserved river delta, touchdown site of NASA Perseverance rover in 2021.',
    origin_of_name: "Town of Jezero in Bosnia and Herzegovina; 'jezero' also means lake in Slavic languages.",
    iau_approval_year: 2007,
  },
  {
    id: 'crater-gale',
    name: 'Gale Crater',
    type: 'Crater (Central Peak Mound)',
    category: 'crater',
    lat: -5.37,
    lon: 137.44,
    diameter_km: 154.0,
    elevation_m: -4500,
    description:
      'Impact crater featuring the 5.5-km high Aeolis Mons (Mount Sharp) at its center, explored by NASA Curiosity rover since 2012.',
    origin_of_name: 'Walter Frederick Gale, Australian amateur astronomer.',
    iau_approval_year: 1991,
  },
  {
    id: 'crater-gusev',
    name: 'Gusev Crater',
    type: 'Crater (Ancient Lakebed)',
    category: 'crater',
    lat: -14.57,
    lon: 175.47,
    diameter_km: 166.0,
    elevation_m: -1900,
    description: "Impact crater drained into by Ma'adim Vallis, landing site of NASA Spirit rover (MER-A) in 2004.",
    origin_of_name: 'Matvei Gusev, Russian astronomer (1826-1866).',
    iau_approval_year: 1976,
  },
  {
    id: 'crater-korolev',
    name: 'Korolev Crater',
    type: 'Crater (Ice-Filled Basin)',
    category: 'crater',
    lat: 72.77,
    lon: 164.58,
    diameter_km: 81.4,
    elevation_m: -3900,
    description:
      'Spectacular northern polar crater containing a permanent 1.8-km thick water ice dome protected by a cold trap.',
    origin_of_name: 'Sergei Korolev, chief rocket designer of the Soviet space program.',
    iau_approval_year: 1973,
  },
  {
    id: 'crater-schiaparelli',
    name: 'Schiaparelli Crater',
    type: 'Crater (Impact Basin)',
    category: 'crater',
    lat: -2.7,
    lon: 16.7,
    diameter_km: 461.0,
    elevation_m: -1000,
    description: 'Vast impact basin in Sinus Sabaeus filled with fine-grained sedimentary layers.',
    origin_of_name: 'Giovanni Schiaparelli, Italian astronomer who mapped Martian canali.',
    iau_approval_year: 1973,
  },
  {
    id: 'crater-huygens',
    name: 'Huygens Crater',
    type: 'Crater (Ancient Basin)',
    category: 'crater',
    lat: -13.96,
    lon: 55.58,
    diameter_km: 467.0,
    elevation_m: 1500,
    description: 'Enormous ancient crater in Tyrrhena Terra exhibiting carbonate minerals and phyllosilicates.',
    origin_of_name: 'Christiaan Huygens, Dutch astronomer who first spotted Syrtis Major in 1659.',
    iau_approval_year: 1973,
  },
  {
    id: 'crater-cassini',
    name: 'Cassini Crater',
    type: 'Crater (Flooded Basin)',
    category: 'crater',
    lat: 23.36,
    lon: 32.11,
    diameter_km: 412.0,
    elevation_m: -1200,
    description: 'Large crater in Arabia Terra featuring ancient lacustrine and shoreline deposits.',
    origin_of_name: "Giovanni Cassini, Italian astronomer who determined Mars' rotation period.",
    iau_approval_year: 1973,
  },
  {
    id: 'crater-newton',
    name: 'Newton Crater',
    type: 'Crater',
    category: 'crater',
    lat: -40.5,
    lon: -158.1,
    diameter_km: 298.0,
    elevation_m: 500,
    description:
      'Deep crater in Sirenum Terra notable for displaying recurring slope lineae (RSL) on south-facing gullies.',
    origin_of_name: 'Sir Isaac Newton, English physicist and mathematician.',
    iau_approval_year: 1973,
  },
  {
    id: 'crater-holden',
    name: 'Holden Crater',
    type: 'Crater (Paleolake)',
    category: 'crater',
    lat: -26.0,
    lon: -34.0,
    diameter_km: 154.0,
    elevation_m: -2100,
    description:
      'Ancient crater with prominent alluvial fans and lakebed sediments, part of the Uzboi-Ladon-Morava drainage.',
    origin_of_name: 'Edward S. Holden, American astronomer.',
    iau_approval_year: 1973,
  },
  {
    id: 'crater-eberswalde',
    name: 'Eberswalde Crater',
    type: 'Crater (Exhumed Delta)',
    category: 'crater',
    lat: -23.86,
    lon: -33.25,
    diameter_km: 65.3,
    elevation_m: -1400,
    description:
      'Hosts the most famous inverted meandering river delta on Mars, proving persistent surface liquid water.',
    origin_of_name: 'Eberswalde, town in Brandenburg, Germany.',
    iau_approval_year: 2006,
  },
  {
    id: 'crater-victoria',
    name: 'Victoria Crater',
    type: 'Crater (Explored by Opportunity)',
    category: 'crater',
    lat: -2.05,
    lon: -5.5,
    diameter_km: 0.75,
    elevation_m: -1400,
    description: 'Scalloped crater explored by NASA Opportunity rover from Sol 951 to 1630.',
    origin_of_name: 'Named after the Victoria, ship of Ferdinand Magellan.',
    iau_approval_year: 2008,
  },
  {
    id: 'crater-endeavour',
    name: 'Endeavour Crater',
    type: 'Crater (Explored by Opportunity)',
    category: 'crater',
    lat: -2.28,
    lon: -5.23,
    diameter_km: 22.0,
    elevation_m: -1500,
    description: 'Crater rim explored by NASA Opportunity rover for over 7 years until mission end in 2018.',
    origin_of_name: "HMS Endeavour, Captain James Cook's research vessel.",
    iau_approval_year: 2008,
  },
  {
    id: 'crater-danielson',
    name: 'Danielson Crater',
    type: 'Crater (Rhythmic Bedding)',
    category: 'crater',
    lat: 7.93,
    lon: -7.11,
    diameter_km: 67.0,
    elevation_m: -2000,
    description:
      'Famed for its alternating light-and-dark cyclic sedimentary layers modulated by Mars orbital obliquity cycles.',
    origin_of_name: 'G. Edward Danielson Jr., planetary scientist.',
    iau_approval_year: 2009,
  },
  {
    id: 'crater-mojave',
    name: 'Mojave Crater',
    type: 'Crater (Fresh Alluvial Fans)',
    category: 'crater',
    lat: 7.5,
    lon: -33.0,
    diameter_km: 58.0,
    elevation_m: -2600,
    description: 'Exceptionally pristine impact crater displaying dendritic channels and braided fans.',
    origin_of_name: 'Mojave Desert, California.',
    iau_approval_year: 2006,
  },
  {
    id: 'crater-tooting',
    name: 'Tooting Crater',
    type: 'Crater (Multi-layered Ejecta)',
    category: 'crater',
    lat: 23.1,
    lon: -152.4,
    diameter_km: 27.2,
    elevation_m: -3800,
    description: 'Very fresh, young Martian impact crater displaying classic continuous fluidized ejecta blankets.',
    origin_of_name: 'Tooting, suburb of London.',
    iau_approval_year: 2006,
  },
  {
    id: 'crater-zunil',
    name: 'Zunil Crater',
    type: 'Crater (Rayed Impact)',
    category: 'crater',
    lat: 7.7,
    lon: 166.0,
    diameter_km: 10.4,
    elevation_m: -2200,
    description: 'Extremely young rayed impact crater surrounded by millions of secondary impact craters.',
    origin_of_name: 'Town in Guatemala.',
    iau_approval_year: 2003,
  },
  {
    id: 'hellas-planitia',
    name: 'Hellas Planitia (Hellas Basin)',
    type: 'Planitia (Giant Impact Basin)',
    category: 'planitia',
    lat: -42.4,
    lon: 70.5,
    diameter_km: 2300.0,
    elevation_m: -7152,
    description:
      'The deepest sub-aerial impact crater in the solar system, plunging over 7 km below datum with atmospheric pressure high enough to permit temporary liquid water.',
    origin_of_name: 'Classical name for Greece (Hellas).',
    iau_approval_year: 1973,
  },
  {
    id: 'argyre-planitia',
    name: 'Argyre Planitia',
    type: 'Planitia (Impact Basin)',
    category: 'planitia',
    lat: -49.7,
    lon: -43.8,
    diameter_km: 800.0,
    elevation_m: -3000,
    description: 'Second largest pristine impact basin on Mars, surrounded by rugged mountain massifs.',
    origin_of_name: 'Mythical silver island in the Indian Ocean.',
    iau_approval_year: 1973,
  },
  {
    id: 'isidis-planitia',
    name: 'Isidis Planitia',
    type: 'Planitia (Impact Basin)',
    category: 'planitia',
    lat: 12.9,
    lon: 87.0,
    diameter_km: 1500.0,
    elevation_m: -3800,
    description: 'Third major impact basin on Mars; Jezero Crater sits directly on its western rim.',
    origin_of_name: 'Isis, Egyptian goddess of fertility and motherhood.',
    iau_approval_year: 1973,
  },
  {
    id: 'utopia-planitia',
    name: 'Utopia Planitia',
    type: 'Planitia (Lowland Basin)',
    category: 'planitia',
    lat: 46.7,
    lon: 117.5,
    diameter_km: 3300.0,
    elevation_m: -4500,
    description:
      "Vast northern plains basin holding massive subsurface water ice deposits. Touchdown site of Viking 2 (1976) and China's Zhurong rover (2021).",
    origin_of_name: "Thomas More's fictional island Utopia ('nowhere').",
    iau_approval_year: 1973,
  },
  {
    id: 'chryse-planitia',
    name: 'Chryse Planitia',
    type: 'Planitia (Plain of Gold)',
    category: 'planitia',
    lat: 28.4,
    lon: -40.0,
    diameter_km: 1600.0,
    elevation_m: -3800,
    description:
      'Smooth circular lowland plain where multiple giant flood channels empty. Viking 1 landed here on July 20, 1976.',
    origin_of_name: 'Mythical golden island of classical antiquity.',
    iau_approval_year: 1973,
  },
  {
    id: 'elysium-planitia',
    name: 'Elysium Planitia',
    type: 'Planitia (Volcanic Plain)',
    category: 'planitia',
    lat: 3.0,
    lon: 154.7,
    diameter_km: 3000.0,
    elevation_m: -2000,
    description:
      'Second largest volcanic region on Mars with young basaltic flood lavas and Cerberus Fossae fissures. Landing site of NASA InSight (2018).',
    origin_of_name: 'Elysian Fields of classical mythology.',
    iau_approval_year: 1973,
  },
  {
    id: 'amazonis-planitia',
    name: 'Amazonis Planitia',
    type: 'Planitia (Smooth Volcanic Plain)',
    category: 'planitia',
    lat: 24.8,
    lon: -163.5,
    diameter_km: 2800.0,
    elevation_m: -3500,
    description:
      'One of the smoothest, least cratered plains on Mars, blanketed by fine dust and Amazonian lava flows.',
    origin_of_name: 'Named after the mythical warrior Amazons.',
    iau_approval_year: 1973,
  },
  {
    id: 'acidalia-planitia',
    name: 'Acidalia Planitia',
    type: 'Planitia (Lowland Basin)',
    category: 'planitia',
    lat: 49.8,
    lon: -20.7,
    diameter_km: 3000.0,
    elevation_m: -4500,
    description: "Expansive dark northern lowland basin featured prominently in the novel and film 'The Martian'.",
    origin_of_name: 'Fountain Acidalia where Venus bathed.',
    iau_approval_year: 1973,
  },
  {
    id: 'arabia-terra',
    name: 'Arabia Terra',
    type: 'Terra (Ancient Highlands)',
    category: 'terra',
    lat: 19.8,
    lon: 30.0,
    diameter_km: 5100.0,
    elevation_m: -1000,
    description: 'Densely cratered, ancient Noachian highlands rich in supervolcano calderas and layered deposits.',
    origin_of_name: 'Arabian Peninsula.',
    iau_approval_year: 1979,
  },
  {
    id: 'noachis-terra',
    name: 'Noachis Terra',
    type: 'Terra (Land of Noah)',
    category: 'terra',
    lat: -45.0,
    lon: 10.0,
    diameter_km: 4800.0,
    elevation_m: 2000,
    description: "Heavily cratered southern highlands representing the ancient 'Noachian' era (~4.1-3.7 Ga).",
    origin_of_name: 'Noah of biblical history.',
    iau_approval_year: 1979,
  },
  {
    id: 'terra-meridiani',
    name: 'Terra Meridiani (Sinus Meridiani)',
    type: 'Terra / Plain',
    category: 'terra',
    lat: -3.0,
    lon: 0.0,
    diameter_km: 1622.0,
    elevation_m: -1300,
    description:
      "Prime meridian datum region of Mars, characterized by grey crystalline hematite spherules ('blueberries') found by Opportunity.",
    origin_of_name: 'Prime meridian of Mars.',
    iau_approval_year: 1979,
  },
  {
    id: 'syrtis-major',
    name: 'Syrtis Major Planum',
    type: 'Planum (Dark Volcanic Plateau)',
    category: 'terra',
    lat: 8.4,
    lon: 69.5,
    diameter_km: 1200.0,
    elevation_m: 1000,
    description:
      'The first planetary feature recognized on Mars by Christiaan Huygens in 1659, a dark volcanic shield of unweathered basalt.',
    origin_of_name: 'Classical Gulf of Sidra (Syrtis Major) in Libya.',
    iau_approval_year: 1973,
  },
  {
    id: 'cimmeria-terra',
    name: 'Terra Cimmeria',
    type: 'Terra (Ancient Highlands)',
    category: 'terra',
    lat: -34.7,
    lon: 145.0,
    diameter_km: 5400.0,
    elevation_m: 2500,
    description: "Highland terrain exhibiting the strongest crustal remanent magnetic stripes from Mars' lost dynamo.",
    origin_of_name: 'Cimmerians of classical antiquity.',
    iau_approval_year: 1979,
  },
  {
    id: 'sirenum-terra',
    name: 'Terra Sirenum',
    type: 'Terra (Highlands)',
    category: 'terra',
    lat: -39.7,
    lon: -150.0,
    diameter_km: 3900.0,
    elevation_m: 2000,
    description: 'Southern highland region carved by gullies, inverted riverbeds, and chloride mineral deposits.',
    origin_of_name: 'Named after the Sirens of Greek mythology.',
    iau_approval_year: 1979,
  },
  {
    id: 'cydonia-mensae',
    name: 'Cydonia Mensae',
    type: 'Mensa (Flat-topped Plateaus)',
    category: 'terra',
    lat: 37.0,
    lon: -12.8,
    diameter_km: 400.0,
    elevation_m: -3000,
    description:
      "Knobby transition terrain between southern highlands and northern lowlands, location of the famous eroded mesa dubbed 'Face on Mars'.",
    origin_of_name: 'Classical Greek city of Cydonia on Crete.',
    iau_approval_year: 1973,
  },
  {
    id: 'planum-boreum',
    name: 'Planum Boreum (North Polar Cap)',
    type: 'Planum (Polar Ice Cap)',
    category: 'polar',
    lat: 88.0,
    lon: 0.0,
    diameter_km: 1100.0,
    elevation_m: -2000,
    description:
      'Permanent water ice cap exhibiting majestic counter-clockwise spiral troughs carved by katabatic winds and solar sublimation.',
    origin_of_name: "Latin for 'Northern Plain'.",
    iau_approval_year: 1973,
  },
  {
    id: 'planum-australe',
    name: 'Planum Australe (South Polar Cap)',
    type: 'Planum (Polar Ice Cap)',
    category: 'polar',
    lat: -85.0,
    lon: 0.0,
    diameter_km: 1450.0,
    elevation_m: 3000,
    description:
      'Elevated southern polar plateau capped by an 8-meter thick permanent carbon dioxide dry ice layer over massive water ice deposits.',
    origin_of_name: "Latin for 'Southern Plain'.",
    iau_approval_year: 1973,
  },
  {
    id: 'vastitas-borealis',
    name: 'Vastitas Borealis',
    type: 'Vastitas (Circumpolar Lowland)',
    category: 'polar',
    lat: 66.0,
    lon: 0.0,
    diameter_km: 9500.0,
    elevation_m: -4500,
    description:
      'The immense circumpolar ring plain surrounding the North Pole, where NASA Phoenix lander touched down in 2008 and scooped water ice.',
    origin_of_name: "Latin for 'Vast Northern Waste'.",
    iau_approval_year: 1973,
  },
  {
    id: 'cerberus-fossae',
    name: 'Cerberus Fossae',
    type: 'Fossae (Tectonic Fissures)',
    category: 'fossa',
    lat: 11.2,
    lon: 166.4,
    diameter_km: 1235.0,
    elevation_m: -2000,
    description:
      'Active seismic fissure system where NASA InSight detected recent marsquakes and young volcanic releases.',
    origin_of_name: 'Cerberus, the multi-headed hound guarding Hades.',
    iau_approval_year: 1973,
  },
  {
    id: 'nili-fossae',
    name: 'Nili Fossae',
    type: 'Fossae (Curved Tectonic Fractures)',
    category: 'fossa',
    lat: 22.0,
    lon: 76.8,
    diameter_km: 667.0,
    elevation_m: -1500,
    description:
      'Concentric graben complex near Isidis rim exposing rich varieties of olivine, carbonates, and clay minerals.',
    origin_of_name: 'Classical albedo feature connected to the Nile.',
    iau_approval_year: 1973,
  },
  {
    id: 'medusae-fossae',
    name: 'Medusae Fossae Formation',
    type: 'Formation (Volcanic Ash Beds)',
    category: 'fossa',
    lat: -1.5,
    lon: -163.0,
    diameter_km: 5000.0,
    elevation_m: -1000,
    description:
      'Massive, wind-sculpted yardang deposits of porous volcanic ignimbrite with kilometers-deep ice traps.',
    origin_of_name: 'Medusa of Greek mythology.',
    iau_approval_year: 1982,
  },
];

export const MARS_HOVER_REGIONS: MarsRegionItem[] = [
  {
    id: 'reg-tharsis',
    name: 'Tharsis Region',
    type: 'Volcanic Plateau (Continental Rise)',
    center: [-112.5, 5.0],
    bounds: [
      [-135, -20],
      [-90, -20],
      [-90, 30],
      [-135, 30],
      [-135, -20],
    ],
    area_sqkm: 8500000,
    elev_range_m: [3000, 21287],
    color: '#ff5722',
    description:
      'Vast volcanic plateau elevated up to 10 km above surrounding lowlands, hosting the colossal Tharsis Montes and Olympus Mons.',
    geology: 'Extensive Hesperian-to-Amazonian basaltic lava flows underlain by a massive mantle plume swell.',
    key_features: ['Olympus Mons', 'Ascraeus Mons', 'Pavonis Mons', 'Arsia Mons', 'Noctis Labyrinthus'],
  },
  {
    id: 'reg-arabia-terra',
    name: 'Arabia Terra',
    type: 'Ancient Highland Terra',
    center: [22.5, 15.0],
    bounds: [
      [0, 0],
      [45, 0],
      [45, 30],
      [0, 30],
      [0, 0],
    ],
    area_sqkm: 5200000,
    elev_range_m: [-3000, 2000],
    color: '#ffb300',
    description:
      'Heavily cratered, ancient Noachian highland terrain exhibiting cyclic layered deposits and remnants of supervolcano calderas.',
    geology: 'Noachian crust with explosive volcanism and ancient friable layered sulfate deposits.',
    key_features: ['Cassini Crater', 'Eden Patera', 'Oxia Planum', 'Pasteur Crater'],
  },
  {
    id: 'reg-terra-cimmeria',
    name: 'Terra Cimmeria',
    type: 'Cratered Highland Continent',
    center: [140.0, -35.0],
    bounds: [
      [110, -65],
      [170, -65],
      [170, -10],
      [110, -10],
      [110, -65],
    ],
    area_sqkm: 6800000,
    elev_range_m: [1000, 4500],
    color: '#8d6e63',
    description:
      'Densely cratered southern highlands preserving the strongest magnetic crustal stripes, indicating an ancient Martian core dynamo.',
    geology: 'Ancient Noachian basement with remanent crustal magnetization and valley network incisions.',
    key_features: ['Gusev Crater (adjacent)', "Ma'adim Vallis", 'Ariane Lacus'],
  },
  {
    id: 'reg-terra-sirenum',
    name: 'Terra Sirenum',
    type: 'Highland Terra',
    center: [-150.0, -35.0],
    bounds: [
      [-180, -65],
      [-120, -65],
      [-120, -10],
      [-180, -10],
      [-180, -65],
    ],
    area_sqkm: 6200000,
    elev_range_m: [500, 3500],
    color: '#a1887f',
    description:
      'Rugged southern upland characterized by recurring slope lineae (RSL), chloride mineral salt flats, and inverted river channels.',
    geology: 'Noachian-to-Hesperian impact breccia and chloride salt playa deposits.',
    key_features: ['Newton Crater', 'Sirenum Fossae', 'Gorgonum Chaos'],
  },
  {
    id: 'reg-xanthe-terra',
    name: 'Xanthe Terra',
    type: 'Equatorial Highland Terra',
    center: [-50.0, 10.0],
    bounds: [
      [-60, 0],
      [-40, 0],
      [-40, 20],
      [-60, 20],
      [-60, 0],
    ],
    area_sqkm: 2100000,
    elev_range_m: [-1500, 1500],
    color: '#d4e157',
    description:
      'Highland border zone carved by dramatic sinuous valleys and outflow channels draining toward Chryse Planitia.',
    geology: 'Sapping valley systems, incised river gorges, and fractured bedrock.',
    key_features: ['Nanedi Valles', 'Shalbatana Vallis', 'Maja Valles'],
  },
  {
    id: 'reg-noachis-terra',
    name: 'Noachis Terra',
    type: 'Highland Terra',
    center: [30.0, -45.0],
    bounds: [
      [0, -65],
      [60, -65],
      [60, -25],
      [0, -25],
      [0, -65],
    ],
    area_sqkm: 5900000,
    elev_range_m: [1000, 3500],
    color: '#795548',
    description:
      'The type locality for the Noachian geological epoch (~4.1-3.7 Ga); ancient heavily cratered terrain situated between Argyre and Hellas basins.',
    geology: 'Primitive planetary crust heavily degraded by the Late Heavy Bombardment.',
    key_features: ['Maunder Crater', 'Russell Crater', 'Proctor Dunes'],
  },
  {
    id: 'reg-elysium',
    name: 'Elysium Region',
    type: 'Volcanic Province',
    center: [155.0, 15.0],
    bounds: [
      [135, 0],
      [175, 0],
      [175, 35],
      [135, 35],
      [135, 0],
    ],
    area_sqkm: 4300000,
    elev_range_m: [-2500, 13900],
    color: '#ef5350',
    description:
      'The second largest volcanic center on Mars, characterized by Elysium Mons, Hecates Tholus, Albor Tholus, and young Cerberus Fossae fissures.',
    geology: 'Late Hesperian to Amazonian shield volcanism and catastrophic flood lavas.',
    key_features: ['Elysium Mons', 'Hecates Tholus', 'Albor Tholus', 'Cerberus Fossae'],
  },
  {
    id: 'reg-amazonis-planitia',
    name: 'Amazonis Planitia',
    type: 'Lowland Plain',
    center: [-160.0, 15.0],
    bounds: [
      [-180, 0],
      [-140, 0],
      [-140, 30],
      [-180, 30],
      [-180, 0],
    ],
    area_sqkm: 4900000,
    elev_range_m: [-4000, -2000],
    color: '#ffca28',
    description:
      'One of the smoothest and least cratered plains on Mars, defining the youngest Martian epoch (the Amazonian).',
    geology: 'Extremely young, pristine basaltic flood lavas thinly blanketed by bright atmospheric dust.',
    key_features: ['Medusae Fossae Formation', 'Gordii Dorsum', 'Lycus Sulci'],
  },
  {
    id: 'reg-arcadia-planitia',
    name: 'Arcadia Planitia',
    type: 'Smooth Lowland Plain',
    center: [-100.0, 45.0],
    bounds: [
      [-120, 30],
      [-80, 30],
      [-80, 60],
      [-120, 60],
      [-120, 30],
    ],
    area_sqkm: 4500000,
    elev_range_m: [-4500, -2000],
    color: '#26a69a',
    description:
      'Northern smooth plain holding vast, shallow subsurface water ice sheets accessible within 1-2 meters of the surface.',
    geology: 'Glacio-lacustrine and volcanic plains with periglacial polygon patterned ground.',
    key_features: ['Castorio Crater', 'Erebus Montes', 'Subsurface Ice Sheets'],
  },
  {
    id: 'reg-utopia-planitia',
    name: 'Utopia Planitia',
    type: 'Giant Lowland Impact Basin',
    center: [115.0, 45.0],
    bounds: [
      [90, 30],
      [140, 30],
      [140, 60],
      [90, 60],
      [90, 30],
    ],
    area_sqkm: 6800000,
    elev_range_m: [-5500, -3500],
    color: '#42a5f5',
    description:
      'Massive circular northern basin holding an estimated volume of water ice equivalent to Lake Superior. Landing site of Viking 2 and Zhurong.',
    geology: 'Sedimentary infill over buried impact basin with scallops and polygon ice wedges.',
    key_features: ['Zhurong Landing Site', 'Viking 2 Site', 'Utopia Ice Deposit'],
  },
  {
    id: 'reg-isidis-planitia',
    name: 'Isidis Planitia',
    type: 'Impact Basin',
    center: [88.0, 13.0],
    bounds: [
      [75, 0],
      [100, 0],
      [100, 25],
      [75, 25],
      [75, 0],
    ],
    area_sqkm: 1900000,
    elev_range_m: [-4000, -2500],
    color: '#29b6f6',
    description:
      'Ancient Noachian impact basin at the transition between southern highlands and northern lowlands. Jezero Crater sits on its western rim.',
    geology: 'Modified impact basin filled with Hesperian sedimentary and volcanic material.',
    key_features: ['Jezero Crater (western rim)', 'Beagle 2 Landing Site', 'Isidis Basin Ring'],
  },
  {
    id: 'reg-hellas-planitia',
    name: 'Hellas Planitia',
    type: 'Deep Impact Basin',
    center: [70.0, -42.0],
    bounds: [
      [50, -60],
      [95, -60],
      [95, -25],
      [50, -25],
      [50, -60],
    ],
    area_sqkm: 5100000,
    elev_range_m: [-7152, -2000],
    color: '#7e57c2',
    description:
      'The deepest planetary impact basin on Mars and in the solar system, plunging to -7,152 meters. Surface pressure is ~1,155 Pa, permitting pure water to theoretically exist as liquid briefly.',
    geology: 'Noachian basin floor modified by glaciers, fluvial inflows (Dao, Harmakhis, Niger), and eolian dunes.',
    key_features: ['Dao Vallis', 'Harmakhis Vallis', 'Hellas Floor Dunes', 'Alpheus Colles'],
  },
  {
    id: 'reg-chryse-planitia',
    name: 'Chryse Planitia',
    type: 'Outflow Basin Lowland',
    center: [-40.0, 27.0],
    bounds: [
      [-55, 15],
      [-25, 15],
      [-25, 40],
      [-55, 40],
      [-55, 15],
    ],
    area_sqkm: 2800000,
    elev_range_m: [-4200, -2500],
    color: '#ab47bc',
    description:
      "The 'Plain of Gold' \u2014 circular lowland plain where multiple colossal flood channels (Ares, Tiu, Simud, Kasei) discharged catastrophic floodwaters.",
    geology: 'Fluvial flood sedimentary deposits and volcanic wrinkle ridges. Viking 1 and Pathfinder landed here.',
    key_features: ['Viking 1 Lander', 'Pathfinder / Sojourner (Ares Vallis mouth)', 'Teardrop Islands'],
  },
  {
    id: 'reg-margaritifer-terra',
    name: 'Margaritifer Terra',
    type: 'Highland Terra & Chaotic Terrain',
    center: [-25.0, -10.0],
    bounds: [
      [-40, -25],
      [-10, -25],
      [-10, 5],
      [-40, 5],
      [-40, -25],
    ],
    area_sqkm: 3400000,
    elev_range_m: [-2000, 1500],
    color: '#8c9eff',
    description:
      'Heavily fractured region displaying the greatest concentration of chaotic terrain (Aram Chaos, Hydraotes Chaos) and channel origins.',
    geology: 'Catastrophic collapse of groundwater aquifers generating regional chaos blocks.',
    key_features: ['Aram Chaos', 'Hydraotes Chaos', 'Uzboi Vallis'],
  },
  {
    id: 'reg-meridiani-planum',
    name: 'Meridiani Planum',
    type: 'Equatorial Sedimentary Plain',
    center: [0.0, -2.0],
    bounds: [
      [-10, -8],
      [10, -8],
      [10, 5],
      [-10, 5],
      [-10, -8],
    ],
    area_sqkm: 1200000,
    elev_range_m: [-1800, -500],
    color: '#26c6da',
    description:
      "The Martian prime meridian datum plain, famous for grey crystalline hematite spherules ('blueberries') explored by NASA's Opportunity rover.",
    geology: 'Layered sulfate-rich sandstones formed in ancient acidic, shallow groundwater lake environments.',
    key_features: ['Opportunity Rover Traverse', 'Eagle Crater', 'Endeavour Crater', 'Victoria Crater'],
  },
  {
    id: 'reg-vastitas-borealis',
    name: 'Vastitas Borealis',
    type: 'Circumpolar Lowland Basin',
    center: [0.0, 75.0],
    bounds: [
      [-180, 65],
      [180, 65],
      [180, 85],
      [-180, 85],
      [-180, 65],
    ],
    area_sqkm: 18500000,
    elev_range_m: [-5000, -3500],
    color: '#3f51b5',
    description:
      'The vast northern circumpolar waste surrounding Planum Boreum. NASA Phoenix lander touched down here in 2008 and scraped subsurface water ice.',
    geology: 'Periglacial terrain, polygon grounds, pattern soils, and buried pure water ice slabs.',
    key_features: ['Phoenix Lander Site', 'Scandia Colles', 'Lomonosov Crater'],
  },
  {
    id: 'reg-terra-sabaea',
    name: 'Terra Sabaea',
    type: 'Ancient Highland Terra',
    center: [42.0, -10.0],
    bounds: [
      [25, -25],
      [60, -25],
      [60, 5],
      [25, 5],
      [25, -25],
    ],
    area_sqkm: 3900000,
    elev_range_m: [0, 3000],
    color: '#ff7043',
    description:
      'Highland plateau exhibiting lobate debris aprons (glacier-like viscous ice-rock flows) and pristine layered craters.',
    geology: 'Noachian crust with debris-covered glaciers and clay mineral deposits.',
    key_features: ['Schiaparelli Crater', 'Huygens Crater', 'Sinus Sabaeus'],
  },
  {
    id: 'reg-tempe-terra',
    name: 'Tempe Terra',
    type: 'Tectonic Highland Plateau',
    center: [-70.0, 38.0],
    bounds: [
      [-85, 25],
      [-55, 25],
      [-55, 50],
      [-85, 50],
      [-85, 25],
    ],
    area_sqkm: 2600000,
    elev_range_m: [-1500, 2500],
    color: '#81c784',
    description:
      'Extensively faulted highland plateau situated northeast of Tharsis Montes, dissected by complex graben systems.',
    geology: 'Tectonic extension grabens, volcanic fissure vents, and ancient cratered terrain.',
    key_features: ['Tempe Fossae', 'Mareotis Fossae', 'Tempe Terra Caldera'],
  },
];

function normalizeLon(lon: number): number {
  return ((((lon + 180) % 360) + 360) % 360) - 180;
}

function surfaceDistanceKm(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 3389.5;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

function isPointInBounds(lon: number, lat: number, bounds: number[][]): boolean {
  if (!bounds || bounds.length < 3) return false;
  let minLon = Infinity,
    maxLon = -Infinity;
  let minLat = Infinity,
    maxLat = -Infinity;
  for (const pt of bounds) {
    if (pt[0] < minLon) minLon = pt[0];
    if (pt[0] > maxLon) maxLon = pt[0];
    if (pt[1] < minLat) minLat = pt[1];
    if (pt[1] > maxLat) maxLat = pt[1];
  }
  return lon >= minLon && lon <= maxLon && lat >= minLat && lat <= maxLat;
}

/**
 * Returns dynamic, instant description for any latitude and longitude on Mars.
 * Evaluates feature proximity, continental basin boundaries, polar ice caps, and elevation.
 */
export function getHoverPlaceDescription(lat: number, lonInput: number, elevInput?: number): HoverPlaceInfo {
  const normLon = normalizeLon(lonInput);

  // 1. Polar ice caps check
  if (lat >= 78.0) {
    return {
      name: 'Planum Boreum (North Polar Ice Cap)',
      category: 'Polar Ice Cap',
      description:
        'Perennial water ice and seasonal frozen carbon dioxide sheet over 3 km thick with spiral troughs and chasmata carved by katabatic winds.',
      geologicalEra: 'Amazonian Polar Layered Deposits',
      elevation_m: -2000,
      isSpecificFeature: true,
    };
  }
  if (lat <= -78.0) {
    return {
      name: 'Planum Australe (South Polar Ice Cap)',
      category: 'Polar Ice Cap',
      description:
        'Residual perennial CO2 ice cap overlying thick layered water-ice and dust deposits (SPLD) exhibiting subglacial reflection anomalies.',
      geologicalEra: 'Amazonian Polar Layered Deposits',
      elevation_m: 3000,
      isSpecificFeature: true,
    };
  }

  // 2. Check proximity to all 78 IAU features
  let closestFeature: MarsFeatureItem | null = null;
  let minFeatureDist = Infinity;

  for (const f of MARS_HOVER_FEATURES) {
    const fLon = normalizeLon(f.lon);
    const dist = surfaceDistanceKm(lat, normLon, f.lat, fLon);
    if (dist < minFeatureDist) {
      minFeatureDist = dist;
      closestFeature = f;
    }
  }

  // Threshold: inside or immediately adjacent to feature
  if (closestFeature) {
    const effectiveRadius = Math.max(25, (closestFeature.diameter_km || 40) / 2 + 35);
    if (minFeatureDist <= effectiveRadius) {
      return {
        name: closestFeature.name,
        category: closestFeature.type || 'Martian Landmark',
        description: closestFeature.description,
        geologicalEra:
          closestFeature.elevation_m > 10000
            ? 'Amazonian Volcanic'
            : closestFeature.elevation_m < -2000
              ? 'Noachian/Hesperian Impact Basin'
              : 'Noachian Bedrock',
        elevation_m: closestFeature.elevation_m,
        distance_km: Math.round(minFeatureDist),
        isSpecificFeature: true,
      };
    }
  }

  // 3. Check membership in 18 Martian continental regions
  for (const reg of MARS_HOVER_REGIONS) {
    if (isPointInBounds(normLon, lat, reg.bounds)) {
      return {
        name: reg.name,
        category: reg.type,
        description: reg.description + (reg.geology ? ' ' + reg.geology : ''),
        geologicalEra: reg.geology?.includes('Noachian')
          ? 'Noachian Period'
          : reg.geology?.includes('Hesperian')
            ? 'Hesperian Epoch'
            : 'Amazonian Era',
        elevation_m: elevInput ?? (reg.type.includes('Lowland') ? -3500 : 1500),
        isSpecificFeature: false,
      };
    }
  }

  // 4. Proximity to closest major landmark within 450 km
  if (closestFeature && minFeatureDist <= 450) {
    const cardinal =
      lat > closestFeature.lat
        ? normLon > normalizeLon(closestFeature.lon)
          ? 'northeast'
          : 'northwest'
        : normLon > normalizeLon(closestFeature.lon)
          ? 'southeast'
          : 'southwest';
    return {
      name: `${Math.round(minFeatureDist)} km ${cardinal} of ${closestFeature.name}`,
      category: 'Regional Intercrater Terrain',
      description: `Transition plains situated ${Math.round(minFeatureDist)} km from ${closestFeature.name}. Characterized by impact ejecta blankets, wind-blown dunes, and basaltic regolith.`,
      geologicalEra: 'Hesperian Transition Period',
      elevation_m: elevInput ?? closestFeature.elevation_m,
      distance_km: Math.round(minFeatureDist),
      isSpecificFeature: false,
    };
  }

  // 5. Global crustal dichotomy fallback
  if (lat < 0 && (elevInput ?? 500) > 0) {
    return {
      name: 'Southern Cratered Highlands',
      category: 'Ancient Crustal Plateau',
      description:
        'Ancient, heavily cratered Martian crust dating to the Noachian period (> 3.8 Ga), preserving records of early planetary differentiation and impacts.',
      geologicalEra: 'Early Noachian (> 3.8 Ga)',
      elevation_m: elevInput ?? 1500,
      isSpecificFeature: false,
    };
  } else {
    return {
      name: 'Northern Lowland Plains (Vastitas Borealis)',
      category: 'Lowland Plain',
      description:
        'Extensive smooth northern plains lying 4 to 5 km below datum, surfaced by sediment infill, volcanic flood sheets, and periglacial features.',
      geologicalEra: 'Hesperian to Amazonian',
      elevation_m: elevInput ?? -4000,
      isSpecificFeature: false,
    };
  }
}

export function nearestHoverLandmarks(lat: number, lonInput: number, limit = 4) {
  const normLon = normalizeLon(lonInput);
  return MARS_HOVER_FEATURES.map((feature) => ({
    ...feature,
    distance_km: surfaceDistanceKm(lat, normLon, feature.lat, normalizeLon(feature.lon)),
  }))
    .sort((a, b) => a.distance_km - b.distance_km)
    .slice(0, limit);
}
