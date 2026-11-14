# zuhura-frontend

Web application for Zuhura Mars, built with React 18, TypeScript, CesiumJS, Three.js, Zustand and Tailwind CSS.

## Features

- 3D globe of Mars on the IAU 2015 ellipsoid with Viking, MOLA, CTX and HiRISE imagery layers
- Rover traverse planning, layer comparison, distance and area measurement, first-person surface view
- Planetary interior viewer based on InSight seismic models
- Ask Zuhura assistant, which sends the current map position with each question and shows cited sources
- Workspace for studies, notes, saved places and exports

## Development

```bash
npm install
npm run dev        # http://localhost:5173
```

The dev server proxies `/api` to the backend at `VITE_BACKEND_URL` (default `http://localhost:8000`). Set `VITE_API_URL` only when the built app must call an API on another origin.

## Scripts

| Command | Purpose |
| --- | --- |
| `npm run dev` | Start the development server |
| `npm run build` | Type-check and build to `dist/` |
| `npm run preview` | Serve the production build |
| `npm run typecheck` | Type-check without building |
| `npm run test:run` | Run the test suite once (Vitest) |

## Project layout

```
src/
  components/   Panels, dialogs and globe overlays
  eva/          EVA planner overlay and route logic
  lib/          API clients, Cesium configuration, geodesy helpers
  store/        Zustand stores
tests/          Vitest suites
```

## Styling

Colours are defined once as Tailwind tokens in `tailwind.config.js`:

| Token | Use |
| --- | --- |
| `brand-*` | Navy palette for the header, sidebar and primary actions |
| `accent` | Active state in the navigation |
| `ink-*` | Text |
| `line-*` | Borders |
| `surface-*` | Panel backgrounds |
| `success`, `warning`, `danger` | Status only |

Use these tokens instead of hex values or the default Tailwind palette.
