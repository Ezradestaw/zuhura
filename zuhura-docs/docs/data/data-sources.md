# Data sources

External archives and services that Zuhura reads from. Check each provider's terms of use before redistributing derived products, and keep provider credits visible in the application.

## Imagery and map tiles

| Source | Provider | Used for | Access |
| --- | --- | --- | --- |
| Mars Trek | NASA JPL / SSERVI | Global basemaps (Viking MDIM 2.1, MOLA shaded relief, THEMIS IR day, TES mineral indices) | WMTS: `https://trek.nasa.gov/tiles/Mars/EQ/{layer}/1.0.0/WMTSCapabilities.xml`; API documentation: <https://trek.nasa.gov/tiles/apidoc/trekAPI.html?body=mars> |
| Mars Trek layer search | NASA JPL / SSERVI | Discovering available layers (equatorial, north and south polar) | `https://trek.nasa.gov/mars/TrekServices/ws/index/{eq,np,sp}/searchItems?itemType=layer` |

## Geology and nomenclature

| Source | Provider | Used for | Access |
| --- | --- | --- | --- |
| Geologic Map of Mars (SIM 3292) | USGS Astrogeology | Geological units and region discovery | <https://pubs.usgs.gov/sim/3292/> |
| Interactive maps of Mars | USGS Astrogeology | Reference layers | <https://astrogeology-usgs.hub.arcgis.com/pages/interactive-maps-mars> |
| Gazetteer of Planetary Nomenclature | IAU WGPSN / USGS | Place names, feature types, coordinates and diameters | <https://planetarynames.wr.usgs.gov/> |
| Mars crater database (Robbins and Hynek, 2012) | Robbins and Hynek | Craters of 1 km diameter and larger | Published database (JGR Planets, 2012) |

## Elevation and spectral data

| Source | Provider | Used for |
| --- | --- | --- |
| MGS MOLA MEGDR | NASA PDS Geosciences Node | Global elevation and the areoid reference |
| MGS TES mineral indices | NASA PDS | Mineral maps |
| MRO CRISM spectral parameters | NASA PDS | Spectral indices |
| MRO CTX and HiRISE | NASA PDS Imaging Node | High-resolution imagery where coverage exists |

## Rover images and mission products

| Source | Provider | Used for | Access |
| --- | --- | --- | --- |
| Mars 2020 raw images | NASA JPL-Caltech | Perseverance raw image gallery | Feed: `https://mars.nasa.gov/rss/api/?feed=raw_images&category=mars2020&feedtype=json`; site: <https://mars.nasa.gov/mars2020/multimedia/raw-images/> |
| Curiosity's proposed path up Mount Sharp (PIA23179) | NASA JPL-Caltech | Mount Sharp route and units | <https://photojournal.jpl.nasa.gov/catalog/PIA23179> |

### Perseverance camera codes

| Camera | Code | Purpose |
| --- | --- | --- |
| Mastcam-Z | `MCZ_LEFT`, `MCZ_RIGHT` | Multispectral stereo zoom imaging |
| Navigation cameras | `NAV_LEFT`, `NAV_RIGHT` | Terrain mapping and drive planning |
| Hazard cameras | `FRONT_HAZCAM`, `REAR_HAZCAM` | Obstacle detection and arm placement |
| SuperCam Remote Micro-Imager | `SUPERCAM_RMI` | Long-range close-up imaging |
| SHERLOC WATSON | `SHERLOC_WATSON` | Close-up rock textures |
| PIXL Micro Context Camera | `PIXL_MCC` | Context images for PIXL scans |

## Other

NASA Earthdata (CMR search and Worldview) was evaluated but holds little Mars data and is not used.
