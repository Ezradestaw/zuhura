# Zuhura – project guide

This guide is for explaining the project to someone else: an examiner, a supervisor or a
teammate. It covers how the system is built, the data it uses, how the traverse (A*) planner
and the chat assistant work, which libraries do what, and the questions you are likely to get.

---

## 1. The project in one paragraph

Zuhura is a web application that shows Mars as a 3D globe. The browser (React + CesiumJS)
draws the planet using real orbital images and elevation data. A Python server (FastAPI) reads
the elevation model, serves image tiles, finds drivable paths between two points with the A*
algorithm, and runs a chat assistant built on Google Gemini that can call our own terrain
functions to answer questions with real numbers.

---

## 2. Architecture

```
 Browser (React app)                         Server (FastAPI, Python)
 ───────────────────                         ────────────────────────
 CesiumJS globe  ── GET /api/v1/tiles/... ─▶  tiles.py  ── reads GeoTIFFs (GDAL)
 Traverse panel  ── POST /navigation/astar ─▶ navigation/astar.py ── reads MOLA DEM
 Ask Zuhura chat ── POST /api/v1/ai/chat ──▶  ai/scientist_engine.py ── Gemini API
                                                   │
                                                   └─ Gemini calls our tools (ai/tools.py)
                                                      e.g. get_elevation_at_point
```

- In development, Vite runs the frontend on port 3000 and forwards every `/api/...` request
  to the backend on port 8000 (`zuhura-frontend/vite.config.ts`).
- In production the frontend is on Vercel and the backend is a Docker container on Render.
  `zuhura-frontend/vercel.json` forwards `/api/...` to the Render URL, so the frontend code
  always uses relative URLs like `/api/v1/...`.
- The large data files (the 962 MB MOLA elevation model, the Viking mosaic) are not in git.
  `zuhura-backend/Dockerfile.render` downloads them from a GitHub release when the image is
  built and checks their SHA-256 hashes.

### Repository layout

| Folder | What is in it |
|---|---|
| `zuhura-frontend/src/components` | React components: globe, panels, nav bar, side bar |
| `zuhura-frontend/src/store` | Zustand stores (shared state such as "is the traverse panel open") |
| `zuhura-frontend/src/lib` | API clients and helpers (`traverse.ts`, `routeExport.ts`) |
| `zuhura-backend/src/zuhura/api/v1` | One file per group of HTTP endpoints |
| `zuhura-backend/src/zuhura/navigation/astar.py` | The A* path finder |
| `zuhura-backend/src/zuhura/ai` | Chat assistant: Gemini client, tools, sessions, citations |
| `zuhura-backend/src/zuhura/terrain_intelligence` | Slope, aspect, roughness, profiles |
| `zuhura-data` | Datasets and the `ZuhuraScienceAccess` class that reads them |

---

## 3. Frameworks and libraries

### Frontend

| Library | Used for | Why this one |
|---|---|---|
| **React 18** | Building the interface out of components | Most common UI library; components keep panels separate |
| **TypeScript** | Types on top of JavaScript | Catches mistakes (wrong field names) before running |
| **Vite** | Dev server and production build | Very fast reload; simple proxy to the backend |
| **CesiumJS** | The 3D globe | Built for planetary-scale 3D maps, supports custom ellipsoids (Mars), imagery tiles, terrain and polylines clamped to the ground |
| **vite-plugin-cesium** | Copies Cesium's workers and assets into the build | Cesium needs extra static files |
| **Zustand** | Shared state between components | Much smaller and simpler than Redux; a store is just a function |
| **Tailwind CSS** | Styling with utility classes | Fast to style; colours are defined once as tokens (AAU blue) |
| **lucide-react** | Icons | Clean line icons as React components |
| **Vitest** | Frontend unit tests | Works with Vite config out of the box |

### Backend

| Library | Used for |
|---|---|
| **FastAPI** | The web API. Endpoints are Python functions; request bodies are checked automatically |
| **Pydantic** | Request/response models with validation (e.g. latitude must be between −90 and 90) |
| **Uvicorn** | The server process that runs FastAPI |
| **GDAL (osgeo)** | Reading GeoTIFF rasters (the MOLA elevation model and image mosaics) |
| **NumPy** | Array maths: slope and roughness of the whole grid at once |
| **heapq** (Python standard library) | The priority queue inside A* |
| **pyproj** | Map projections and coordinate conversions |
| **google-genai** | Official Google SDK to call Gemini |
| **Pillow** | Making PNG/JPEG tiles |
| **pytest** | Backend tests |

---

## 4. Datasets

| Dataset | Resolution | Where it comes from | Used for |
|---|---|---|---|
| **MOLA MEGDR** global elevation (`mola_global_meg128_cog.tif`) | 128 pixels per degree ≈ **463 m per pixel** | Mars Global Surveyor, Mars Orbiter Laser Altimeter; NASA PDS Geosciences Node | Heights, slopes, the A* planner, the assistant's elevation tool |
| **Viking MDIM 2.1** colour mosaic | 232 m/px | Viking orbiters; USGS Astrogeology | The base colour image of the whole planet |
| **CTX** mosaic of Jezero | ≈ 5–6 m/px | Mars Reconnaissance Orbiter Context Camera; MSSS / NASA PDS | Sharper image around Jezero crater |
| **HiRISE** image of Jezero | 0.25–0.5 m/px | MRO HiRISE camera; University of Arizona | Very close-up detail at the Perseverance landing site |
| MOLA polar DEMs | 128 px/deg | NASA PDS | Elevation above 88° latitude |
| JSON files in `zuhura-data/data` | – | Compiled from IAU nomenclature and mission pages | Place names, missions, rover tracks, regions |
| NASA Mars rover raw images API | – | NASA | The "Rover images" panel |

Things to know about MOLA, because examiners like asking:

- Elevations are relative to the **areoid**, Mars' version of "sea level" (a surface of equal
  gravity potential). So −2,600 m at Jezero means 2.6 km below that reference.
- The file is stored in a simple cylindrical (equirectangular) projection: each column is a
  fixed step in longitude and each row a fixed step in latitude, 1/128 of a degree. That is
  why converting latitude/longitude to a pixel is just multiplication.
- Values are 16-bit integers in metres.
- 463 m per pixel means the planner cannot see boulders or small dunes. It plans at the scale
  of crater rims, hills and canyon walls.

Coordinates in the whole app are **planetocentric latitude** and **east-positive longitude
(0–360° E)**, the IAU convention for Mars.

---

## 5. The traverse planner (A*)

### 5.1 What the user does

1. Opens **Traverse** (nav bar or side bar, shortcut `1`).
2. Presses **Pick on map** next to *Start* and clicks the globe; the same for *Destination*.
3. Chooses a vehicle: **Car** (max slope 10°) or **Rover** (max slope 20°).
4. Presses **Find path**. A yellow line shows the A* path; a dashed white line shows the
   straight line for comparison. The panel shows length, straight-line distance, steepest
   point, total climb/descent and an elevation profile. The path can be downloaded as GeoJSON,
   CSV or KML.

Code: `zuhura-frontend/src/components/RoutePlanningDrawer.tsx` (panel),
`zuhura-frontend/src/lib/traverse.ts` (API call), and the click handling in
`MarsGlobe.tsx` (search for `routePickTarget`).

### 5.2 What the server does – `zuhura-backend/src/zuhura/navigation/astar.py`

Endpoint: `POST /api/v1/spatial/navigation/astar` with
`{start_latitude, start_longitude, destination_latitude, destination_longitude, vehicle}`.

**Step 1 – read the terrain around the two points (`build_grid`)**
Take the box that contains both points and add a margin (40 % of the distance, at least
0.15°) so the path has room to go around obstacles. Convert the box to pixel rows/columns and
read just that block of the MOLA file with GDAL. Longitude wraps around at 0°/360°, so a box
crossing that line is read in two pieces and joined.

**Step 2 – measure every cell**

- *Slope* (degrees): how steep the ground is. Using NumPy's `gradient` we get the height
  change per metre in the east–west (dz/dx) and north–south (dz/dy) directions, then
  `slope = atan( sqrt(dzdx² + dzdy²) )`.
  The east–west size of a pixel shrinks towards the poles (`463 m × cos(latitude)`), and the
  code takes that into account, otherwise slopes near the poles would be wrong.
- *Roughness* – the **Terrain Ruggedness Index (TRI)**, Riley et al. 1999: for each cell,
  the average absolute height difference to its 8 neighbours, in metres. Flat plains are a
  few metres, crater rims and ridges are 100+ m.

Both are measured at the full 463 m resolution. If the area is big (more than 300 cells per
side), the grid is then averaged down in blocks so the search stays fast. Doing the
measurements first means "10° slope limit" means the same thing for a 10 km trip and a
400 km trip.

**Step 3 – decide what is drivable**

A cell is **blocked** if `slope > max_slope` or `TRI > max_roughness`.

| Vehicle | Max slope | Max roughness (TRI) |
|---|---|---|
| Car | 10° | 60 m |
| Rover | 20° | 120 m |

(Real Mars rovers are designed for about 20–30° slopes; a car-like vehicle is kept much
gentler.)

**Step 4 – A\* search (`astar`)**

The grid is a graph: each cell connects to its 8 neighbours (up, down, left, right and the
4 diagonals).

A* keeps a priority queue (`heapq`) of cells to look at, ordered by

```
f(n) = g(n) + h(n)
g(n) = cheapest known cost from the start to n
h(n) = straight-line distance from n to the goal (the heuristic)
```

It always expands the cell with the smallest `f`. When it pops the goal, it walks back
through `came_from` to rebuild the path.

Cost of moving from cell *a* to neighbour *b*:

```
cost = distance(a,b) × (1 + 4·(slope_b / max_slope)² + 2·(TRI_b / max_TRI)²)
       + 3 × (metres climbed, if going uphill)
```

- `distance` is the real ground distance in metres: the cell size, or ×√2 for diagonals,
  with the east–west part scaled by cos(latitude).
- The squared terms make gentle ground almost free and ground close to the limit expensive,
  so the path prefers flat ground but can still use a moderate slope if it saves a long detour.
- The climb term prefers going around a hill rather than over it.
- A step is also refused if the height change between the two cells is steeper than the
  vehicle limit, even if each cell on its own is fine.

**Why the result is optimal (on this grid):** every step costs at least its distance
(the multiplier is ≥ 1 and the climb term is ≥ 0). The heuristic is the straight-line
distance (measured with the smallest east–west cell size in the grid, so it is never
longer than any real path). A heuristic that never overestimates
is called **admissible**, and with an admissible heuristic A* is guaranteed to return the
cheapest path. It is also **consistent** (it obeys the triangle inequality), which is why a
cell never has to be re-opened once it is closed.

**Why A\* and not Dijkstra?** Dijkstra is A* with `h = 0`: it spreads out in every direction
equally. The heuristic pulls A* towards the goal, so it looks at far fewer cells for the same
answer. In our tests a 25 km Jezero route expanded about 2,600 cells out of about 6,000.

**If there is no way through** (for example a car trying to climb Mount Sharp or cross Valles
Marineris), the queue empties without reaching the goal and the server returns HTTP 422 with
a message suggesting the rover setting or closer points.

**Step 5 – straighten the path (`straighten`)**

On a grid, A* paths zig-zag (they can only move in 8 directions). The code looks ahead along
the path and replaces a zig-zag between two points with a straight line *only if* the straight
line is drivable and costs no more. Endpoints never change. This makes the line look like
something a driver would actually follow.

**Step 6 – build the answer**

For each point on the final path the server returns latitude, longitude, elevation, distance
from the start, slope and roughness, plus totals: path length, straight-line distance, detour
factor, climb, descent, max and mean slope, grid size and the percentage of blocked cells.

### 5.3 Complexity and speed

- Grid of *N* cells, 8 neighbours each. A* with a binary heap is **O(N log N)** in the worst
  case; with the heuristic it usually explores a small part of the grid.
- The grid is capped at 300 × 300 = 90,000 cells. Measured times: 10–30 km routes 0.02–0.2 s;
  300–500 km routes about 1–1.5 s.
- Maximum distance between points: 600 km. Points must be between 85° S and 85° N.

### 5.4 Limitations (say these before they ask)

- 463 m pixels: rocks, small craters and sand ripples are invisible.
- No soil model: sand vs. bedrock is not considered.
- 8-direction grid: paths are optimal on the grid, not in continuous space (the straightening
  step reduces this).
- The vehicle limits are reasonable values, not taken from a specific vehicle's datasheet.

### 5.5 Tests

`zuhura-backend/tests/unit/navigation/test_astar.py` builds small fake terrains:
flat ground gives a straight line; a wall with a gap forces the path through the gap;
a full wall gives `NoPathError`; a 10° ramp measures as 10°.

---

## 6. The chat assistant (Ask Zuhura)

### 6.1 Flow

1. The user types a question. The frontend (`src/store/aiStore.ts`) sends
   `POST /api/v1/ai/chat` with the question, a session id and the current camera position.
2. `ai/scientist_engine.py` adds the camera position to the prompt and sends it to Gemini
   with a short system instruction (how to talk about Mars coordinates and units, keep
   answers short) and a list of **tools**: our own Python functions such as
   `get_elevation_at_point`, `get_terrain_morphometry`, `generate_terrain_profile`,
   `search_scientific_catalog`.
3. **Function calling**: Gemini decides it needs a number, asks to call e.g.
   `get_terrain_morphometry(latitude=18.4, longitude=77.5)`. The google-genai SDK runs that
   Python function on our server, sends the result back to Gemini, and Gemini writes the answer
   using that real value. This is what stops the model from making up elevations.
4. `ai/grounding.py` turns the tools that were used into a list of dataset citations
   (e.g. MOLA MEGDR), shown under the answer as *Sources*.
5. `ai/session_manager.py` keeps the conversation per session id in memory.

### 6.2 What was wrong and how it was fixed

- **The chatbot stopped answering** because the configured model `gemini-2.5-flash` was
  retired by Google: every request returned *404 – model no longer available*, and the user
  only saw "could not answer right now".
- Fixes in `ai/gemini_client.py`:
  - Default model is now `gemini-3.5-flash-lite` (fast and supports tools). Set in
    `.env`, `render.yaml` and the config default.
  - If a model returns 404 the client automatically tries the next model in
    `FALLBACK_MODELS`, so the next model retirement will not break the app.
  - The real reason is now shown to the user (quota used up, bad API key, timeout) instead
    of a generic message.
  - Tool calls made automatically by the SDK are now read from
    `automatic_function_calling_history`, so the answer's sources are correct.
- The system prompt was shortened and no longer asks for `[MEASURED]`-style tags.

Note for deployment: if the Render dashboard has `GEMINI_MODEL=gemini-2.5-flash` set by hand,
change it to `gemini-3.5-flash-lite` (the fallback will still work, but the first request will
be slower).

---

## 7. What was removed in this round, and why

| Removed | Reason |
|---|---|
| Planetary interior (X-Ray Mars) – panel, backend API, assistant tool, tests | Not wanted in the project |
| Mission lab (adaptive 3D mission simulation) | Not wanted; was never committed |
| Mission overview dashboard | Removed from side bar with "Mission" |
| "Regions" button in the nav bar | Still available in the side bar |
| "Hover details" toggle and hover card | Removed from side bar |
| Old point-to-point "pinpoint route" HUD and client-side fake route fallback | Replaced by the new A* traverse panel |

A copy of the Mission lab code was kept outside the repository in case it is ever needed.

---

## 8. Likely questions and short answers

**Why A\*?** It finds the cheapest path like Dijkstra but uses a heuristic to search towards
the goal, so it is much faster. With an admissible heuristic it is still optimal.

**What is your heuristic and is it admissible?** Straight-line ground distance to the goal.
Every move costs at least its length, so the heuristic never overestimates – it is admissible.

**How do you know the ground is too rough for a car?** Two measures from the MOLA elevation
model: slope (from the elevation gradient) and Terrain Ruggedness Index (average height
difference to neighbours). Cells above the vehicle's limits are blocked; cells near the
limits cost more.

**What resolution is the planner working at?** 463 m per pixel (MOLA 128 px/deg). Longer
routes are averaged to keep the grid ≤ 300 × 300.

**Why do you need a margin around the two points?** Without it the search box is just the
rectangle between the points, and the path cannot go around an obstacle on the edge.

**What happens if there is no path?** A* runs out of cells to explore, the server returns
HTTP 422 and the panel shows the message.

**Why not just draw a straight line?** The straight line can cross crater rims and cliffs.
The dashed line on the globe shows it so you can compare.

**How is distance measured on Mars?** Haversine (great-circle) formula with the MOLA sphere
radius 3,396 km for totals; inside the grid, cell size × cos(latitude) for east–west steps.

**How does the chatbot avoid making up numbers?** Gemini function calling: it calls our
Python functions that read the real MOLA data, and the answer lists the datasets used.

**What is the areoid?** The Mars reference surface for heights, equivalent to sea level on
Earth, defined by gravity.

**Why FastAPI?** Fast, automatic request validation with Pydantic, automatic API docs at
`/docs`, and Python has the scientific libraries (NumPy, GDAL) we need.

**Why CesiumJS instead of Three.js or Leaflet?** Cesium handles a whole planet in 3D with
real coordinates, tiled imagery and terrain, and lets us set the Mars ellipsoid. Leaflet is
2D only; Three.js would mean writing all the map logic ourselves.

**Why Zustand?** Several components need the same state (e.g. the globe needs to know the
traverse panel is waiting for a click). Zustand gives a shared store with very little code.

**How is it deployed?** Frontend on Vercel, backend as a Docker image on Render; Vercel
forwards `/api` to Render. The Docker build downloads the big datasets and checks hashes.

**How did you test it?** pytest (149 backend tests, including A* on synthetic terrain) and
Vitest (87 frontend tests, including the traverse API client and file export).

---

## 9. Running it

```bash
# backend
cd zuhura-backend && cp .env.example .env   # add GEMINI_API_KEY
pip install -e . && uvicorn zuhura.api.main:app --port 8000 --reload

# frontend
cd zuhura-frontend && npm install && npm run dev   # http://localhost:3000
```

Try the A* endpoint directly:

```bash
curl -X POST localhost:8000/api/v1/spatial/navigation/astar \
  -H 'Content-Type: application/json' \
  -d '{"start_latitude":18.38,"start_longitude":77.58,"destination_latitude":18.6,"destination_longitude":77.2,"vehicle":"car"}'
```

API docs with every endpoint: http://localhost:8000/docs
