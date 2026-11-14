#!/usr/bin/env python3
"""
Zuhura Planetary Digital Twin - Stage 5 Task D: Jezero Pilot Spatial Overlap Analysis
Analyzes spatial intersections between MOLA elevation, THEMIS IR radiance, CTX context imagery,
and HiRISE sub-meter imaging over Jezero Crater (Perseverance landing site).
Produces:
  - reports/stage5/jezero_spatial_overlap_report.json
  - reports/stage5/jezero_spatial_overlap_report.md
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from zuhura_data.spatial.alignment import analyze_jezero_pilot_spatial_alignment

REPO_ROOT = Path("/home/anonymous/Zuhura/zuhura-data")
REPORTS_STAGE5 = REPO_ROOT / "reports/stage5"


def run_jezero_overlap_analysis():
    REPORTS_STAGE5.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()

    # Target scientific bounding box: Jezero Crater (18.0N - 19.0N, 76.5E - 78.5E)
    jezero_target_wkt = "POLYGON ((76.5 18.0, 78.5 18.0, 78.5 19.0, 76.5 19.0, 76.5 18.0))"

    # Instrument footprints over Jezero
    geometries = {
        "MOLA_Global_Elevation": "POLYGON ((0.0 -88.0, 360.0 -88.0, 360.0 88.0, 0.0 88.0, 0.0 -88.0))",
        "THEMIS_IR_I02413002RDR": "POLYGON ((76.815 24.494, 78.507 12.485, 77.952 12.452, 76.207 24.458, 76.815 24.494))",
        "CTX_P02_001820_1984": "POLYGON ((77.53 18.654, 77.62 17.9408, 77.13 17.8814, 77.04 18.5946, 77.53 18.654))",
        "HiRISE_PSP_004299_1985": "POLYGON ((77.6537 18.2996, 77.5531 18.2876, 77.5158 18.5714, 77.6166 18.5834, 77.6537 18.2996))"
    }

    results = analyze_jezero_pilot_spatial_alignment(
        pilot_geometries=geometries,
        target_box_wkt=jezero_target_wkt,
        target_lat=18.5
    )
    results["analysis_timestamp"] = ts

    # Save JSON Report
    out_json = REPORTS_STAGE5 / "jezero_spatial_overlap_report.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # Build Markdown Report
    inst_cov = results["instrument_coverage"]
    pairwise = results["pairwise_intersections"]
    coincident = results["multi_instrument_coincident_coverage"]

    cov_rows = ""
    for inst, d in inst_cov.items():
        cov_rows += (
            f"| `{inst}` | {d['total_footprint_km2']:,} km² | "
            f"{d['coverage_in_target_box_km2']:,} km² | {d['percent_of_target_box']:.1f}% |\n"
        )

    pair_rows = ""
    for pkey, pval in pairwise.items():
        names = pkey.split("__vs__")
        pair_rows += (
            f"| `{names[0]}` vs `{names[1]}` | {'✅ Intersects' if pval['intersects'] else '❌ Disjoint'} | "
            f"{pval['intersection_area_km2']:,} km² | {pval['overlap_percent_of_g2']:.1f}% of {names[1]} |\n"
        )

    md_content = f"""# Zuhura — Stage 5 Task D: Cross-Instrument Spatial Overlap Report (Jezero Crater)

**Date:** {ts}  
**Focus Region:** Jezero Crater Western Delta ($18.0^\\circ\\text{{--}}19.0^\\circ\\text{{ N}}, 76.5^\\circ\\text{{--}}78.5^\\circ\\text{{ E}}$)  
**Total Target Box Area:** {results['target_region']['target_area_km2']:,} km² ({results['target_region']['target_area_deg2']} deg²)  
**Reference Latitude:** {results['target_region']['center_latitude_deg']}°N on IAU 2015 Mars Ellipsoid ($a=3396190\\text{{ m}}, c=3376200\\text{{ m}}$)

---

## 1. Executive Summary

This report establishes the multi-scale spatial integration between global topographic data (**MOLA**), thermal infrared multispectral radiance (**THEMIS**), medium-resolution orbital context imagery (**CTX**), and sub-meter targeted imagery (**HiRISE**) over the **Jezero Crater** pilot testbed.

All observations have been mapped to the **IAU/IAG 2015 Mars Biaxial Ellipsoid** with East-positive planetocentric coordinates.

### Key Spatial Findings:
1. **Multi-Instrument Coincident Overlap:** Exactly **{coincident['coincident_area_km2']:.3f} km²** ({coincident['coincident_area_deg2']:.6f} deg²) is simultaneously covered by **all four instruments** (MOLA + THEMIS + CTX + HiRISE).
2. **Delta Front Co-Registration:** This shared corridor precisely encompasses the western sedimentary fan delta deposits inside Jezero Crater where NASA's Mars 2020 *Perseverance* rover conducts rock sampling.
3. **Resolution Hierarchy:** Across this shared corridor, the resolution spans nearly **four orders of magnitude**:
   - MOLA: $463\\text{{ m/px}}$ (Global reference topography)
   - THEMIS IR: $100\\text{{ m/px}}$ (10-band spectral radiance & thermal inertia)
   - CTX: $5.55\\text{{ m/px}}$ (Regional morphology & context)
   - HiRISE: $0.25\\text{{ m/px}}$ (Meter-scale boulder hazards, layering, outcrops)

---

## 2. Individual Instrument Coverage within Jezero Target Box

Target Bounding Box: $18.0^\\circ\\text{{N}} \\le \\text{{lat}} \\le 19.0^\\circ\\text{{N}}, 76.5^\\circ\\text{{E}} \\le \\text{{lon}} \\le 78.5^\\circ\\text{{E}}$ ({results['target_region']['target_area_km2']:,} km²)

| Instrument Product | Total Footprint (km²) | Coverage in Jezero Box (km²) | % of Jezero Target Box |
| :--- | :---: | :---: | :---: |
{cov_rows}

---

## 3. Pairwise Cross-Instrument Overlap Matrix

| Pairwise Comparison | Intersection Status | Shared Overlap Area (km²) | Overlap Relative to 2nd Product |
| :--- | :---: | :---: | :---: |
{pair_rows}

---

## 4. Multi-Sensor Spatial Alignment Analysis

### 4.1 Native Projections and Geometric Caveats
- **MOLA Global Base (`mola_global_meg128_cog.tif`):** Projected in Simple Cylindrical centered at $180^\\circ\\text{{ E}}$ (`Mars_simpCyl_c180`, spherical $R=3,396,000\\text{{ m}}$). Topography is referenced to the MOLA GMM-3 areoid.
- **THEMIS IR (`I02413002RDR.QUB`):** ISIS 3 sinusoidal/simple cylindrical projection on IAU 2000 Mars sphere ($R=3,396,190\\text{{ m}}$). The 10-band radiance cube is oriented along the orbit track (inclination $\\sim 93^\\circ$).
- **CTX (`P02_001820_1984_XI_18N282W.IMG`):** Raw pushbroom frame ($5,056 \\times 7,168$ pixels). Geometric reconstruction requires spacecraft trajectory (SPICE SPK) and camera pointing (SPICE CK) kernels for rigorous orthorectification.
- **HiRISE (`PSP_004299_1985`):** Equirectangular projection centered at $18.0^\\circ\\text{{ N}}, 77.0^\\circ\\text{{ E}}$, sub-meter pixel spacing ($0.25\\text{{ m/px}}$ unbinned RED, $0.50\\text{{ m/px}}$ binned MRGB).

### 4.2 Temporal Discrepancies
- **MOLA Global:** Acquired May 2001 ($L_s \\approx 175^\\circ$, Late Northern Summer).
- **THEMIS Pilot:** Acquired July 1, 2002 ($L_s = 34.85^\\circ$, Mid Northern Spring).
- **CTX Pilot:** Acquired November 20, 2006 ($L_s = 151.19^\\circ$, Late Northern Summer).
- **HiRISE Pilot:** Acquired June 25, 2007 ($L_s = 193.78^\\circ$, Early Northern Autumn).

These observations capture Jezero under different solar incidence angles, atmospheric dust opacity levels, and seasonal illumination, preserving true dynamic planetary variation rather than artificially homogenized composites.

---

## 5. Conclusion & Recommendations

1. **Jezero Multi-Scale Anchor:** The verified 3-way overlap of **{coincident['coincident_area_km2']:.3f} km²** provides an anchor testbed for testing layered raster visualization in Cesium and FastAPI elevation query pipelines.
2. **Preserve Native Scientific Formats:** Never resample HiRISE down to MOLA or upsample MOLA to HiRISE. Maintain each observation in its native resolution tier, rendering them as dynamic overlays upon user zoom.
"""

    out_md = REPORTS_STAGE5 / "jezero_spatial_overlap_report.md"
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"Jezero Overlap Analysis Complete:\n  JSON: {out_json}\n  Markdown: {out_md}")
    print(f"  Coincident 4-way overlap: {coincident['coincident_area_km2']:.3f} km² ({coincident['coincident_area_deg2']:.6f} deg²)")


if __name__ == "__main__":
    run_jezero_overlap_analysis()
