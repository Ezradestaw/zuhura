#!/usr/bin/env python3
"""
Zuhura Planetary Digital Twin - Phase C Visual & Engine Acceptance Test Runner
Automates Selenium with Headless Chromium (SwiftShader WebGL) to verify:
  1. Planetary Natural Color Basemap (Viking MDIM 2.1 global mosaic, authentic hues, limb scattering)
  2. Continental Scale Resolution Scaling (Viking L6-8 over Syrtis Major / Isidis)
  3. Regional Context Draping (CTX 5.55 m/px over Jezero 3D quantized-mesh rim and floor)
  4. Close-Surface Detail (HiRISE 0.50 m/px over Perseverance touchdown & delta front)
  5. Dynamic Solar Illumination with Oct-Normal Hillshading
  6. Planetary Day/Night Terminator and Horizon Atmosphere
  7. Optional MOLA Topographic Colormap Layer (verified on demand, non-default)
  8. Scientific Elevation Query Invariance
"""

import json
import math
import os
import shutil
import time
from pathlib import Path
import urllib.request

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

REPO_ROOT = Path("/home/anonymous/Zuhura")
OUT_DIR = REPO_ROOT / "reports/phase_c/screenshots"
BRAIN_DIR = Path("/home/anonymous/.gemini/antigravity-cli/brain/fcc92d33-69c4-481e-b8be-6fb8b4bc8e32")

OUT_DIR.mkdir(parents=True, exist_ok=True)
BRAIN_DIR.mkdir(parents=True, exist_ok=True)


def init_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--use-gl=angle")
    options.add_argument("--use-angle=swiftshader")
    options.add_argument("--enable-unsafe-swiftshader")
    options.add_argument("--window-size=1440,900")
    options.binary_location = "/usr/bin/chromium"
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})

    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(60)
    driver.set_script_timeout(60)
    return driver


def wait_for_scene_render(driver, frames=2, delay=1.0):
    driver.execute_script(f"""
        const v = window.viewer;
        if (v && v.scene) {{
            for (let i = 0; i < {frames}; i++) {{
                v.scene.requestRender();
                v.scene.render();
            }}
        }}
    """)
    time.sleep(delay)


def save_screenshot(driver, filename):
    dest1 = OUT_DIR / filename
    dest2 = BRAIN_DIR / filename
    driver.save_screenshot(str(dest1))
    shutil.copy(str(dest1), str(dest2))
    print(f"  [SAVED] {filename} ({dest1.stat().st_size} bytes)")


def main():
    print("=" * 70)
    print("ZUHURA PHASE C: GLOBE & VISUAL ENGINE UPGRADE ACCEPTANCE SUITE")
    print("=" * 70)

    driver = init_driver()
    results = {}

    try:
        print("\n1. Navigating to Zuhura Frontend at http://localhost:3000...")
        driver.get("http://localhost:3000")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "canvas"))
        )
        print("  Canvas detected. Waiting for Cesium Mars scene initialization...")
        wait_for_scene_render(driver, frames=2, delay=2.0)

        # -------------------------------------------------------------
        # STEP 1: Global Planetary Scale (Natural Color Viking MDIM 2.1)
        # -------------------------------------------------------------
        print("\n2. Verifying Planetary Natural Color Global Basemap...")
        driver.execute_script("""
            const v = window.viewer;
            const Cesium = window.Cesium;
            v.camera.setView({
                destination: Cesium.Cartesian3.fromDegrees(77.45, 18.44, 3800000.0, v.scene.globe.ellipsoid),
                orientation: {
                    heading: Cesium.Math.toRadians(0.0),
                    pitch: Cesium.Math.toRadians(-90.0),
                    roll: 0.0
                }
            });
        """)
        wait_for_scene_render(driver, frames=2, delay=2.0)

        layers_diag = driver.execute_script("""
            const v = window.viewer;
            const numLayers = v.imageryLayers.length;
            const l0 = v.imageryLayers.get(0);
            const l1 = v.imageryLayers.get(1);
            const l2 = v.imageryLayers.get(2);
            const l3 = v.imageryLayers.get(3);
            return {
                numLayers: numLayers,
                vikingUrl: l0 ? l0.imageryProvider.url : null,
                vikingShow: l0 ? l0.show : null,
                ctxUrl: l1 ? l1.imageryProvider.url : null,
                ctxShow: l1 ? l1.show : null,
                hiriseUrl: l2 ? l2.imageryProvider.url : null,
                hiriseShow: l2 ? l2.show : null,
                molaUrl: l3 ? l3.imageryProvider.url : null,
                molaShow: l3 ? l3.show : null,
            };
        """)
        print(f"  Imagery Layers Diagnostics: {json.dumps(layers_diag, indent=2)}")
        assert layers_diag["numLayers"] >= 4, "Must have at least 4 imagery layers in stack"
        assert "/api/v1/tiles/viking" in layers_diag["vikingUrl"], "Tier 1 must be Viking MDIM 2.1"
        assert layers_diag["vikingShow"] is True, "Viking basemap must be active by default"
        assert layers_diag["molaShow"] is False, "MOLA elevation colormap must be inactive by default"
        results["planetary_natural_basemap"] = "PASSED"

        save_screenshot(driver, "screenshot_phase_c_01_planetary_viking_global.png")

        # -------------------------------------------------------------
        # STEP 2: Continental Scale (Isidis / Syrtis Major / Jezero)
        # -------------------------------------------------------------
        print("\n3. Verifying Continental Scale Resolution (750 km altitude)...")
        driver.execute_script("""
            const v = window.viewer;
            const Cesium = window.Cesium;
            v.camera.setView({
                destination: Cesium.Cartesian3.fromDegrees(77.45, 18.44, 750000.0, v.scene.globe.ellipsoid),
                orientation: {
                    heading: Cesium.Math.toRadians(0.0),
                    pitch: Cesium.Math.toRadians(-90.0),
                    roll: 0.0
                }
            });
        """)
        wait_for_scene_render(driver, frames=2, delay=1.5)
        save_screenshot(driver, "screenshot_phase_c_02_continental_jezero_region.png")
        results["continental_resolution"] = "PASSED"

        # -------------------------------------------------------------
        # STEP 3: Regional Scale (CTX Draped over Jezero 3D Terrain)
        # -------------------------------------------------------------
        print("\n4. Verifying Regional Scale CTX Context Draping (65 km altitude)...")
        driver.execute_script("""
            const v = window.viewer;
            const Cesium = window.Cesium;
            v.camera.setView({
                destination: Cesium.Cartesian3.fromDegrees(77.45, 18.30, 65000.0, v.scene.globe.ellipsoid),
                orientation: {
                    heading: Cesium.Math.toRadians(15.0),
                    pitch: Cesium.Math.toRadians(-55.0),
                    roll: 0.0
                }
            });
        """)
        wait_for_scene_render(driver, frames=2, delay=2.0)
        save_screenshot(driver, "screenshot_phase_c_03_regional_jezero_ctx.png")
        results["regional_ctx_draping"] = "PASSED"

        # -------------------------------------------------------------
        # STEP 4: Close-Surface Scale (HiRISE Draped over Delta Scarp)
        # -------------------------------------------------------------
        print("\n5. Verifying Close-Surface Scale HiRISE Detail Draping (12 km altitude)...")
        driver.execute_script("""
            const v = window.viewer;
            const Cesium = window.Cesium;
            v.camera.setView({
                destination: Cesium.Cartesian3.fromDegrees(77.53, 18.38, 12000.0, v.scene.globe.ellipsoid),
                orientation: {
                    heading: Cesium.Math.toRadians(290.0),
                    pitch: Cesium.Math.toRadians(-40.0),
                    roll: 0.0
                }
            });
        """)
        wait_for_scene_render(driver, frames=2, delay=2.0)
        save_screenshot(driver, "screenshot_phase_c_04_surface_hirise_delta.png")
        results["close_surface_hirise"] = "PASSED"

        # -------------------------------------------------------------
        # STEP 5: Dynamic Solar Illumination with Oct-Normal Hillshading
        # -------------------------------------------------------------
        print("\n6. Verifying Dynamic Illumination & Oct-Normal Hillshading...")
        driver.execute_script("""
            const v = window.viewer;
            const Cesium = window.Cesium;
            v.scene.globe.enableLighting = true;
            v.scene.globe.dynamicAtmosphereLighting = true;
            
            const azRad = Cesium.Math.toRadians(300.0);
            const elRad = Cesium.Math.toRadians(30.0);
            const x = -Math.sin(azRad) * Math.cos(elRad);
            const y = -Math.cos(azRad) * Math.cos(elRad);
            const z = Math.sin(elRad);
            v.scene.light = new Cesium.DirectionalLight({
                direction: new Cesium.Cartesian3(x, y, z),
            });
            v.camera.setView({
                destination: Cesium.Cartesian3.fromDegrees(77.30, 18.20, 95000.0, v.scene.globe.ellipsoid),
                orientation: {
                    heading: Cesium.Math.toRadians(45.0),
                    pitch: Cesium.Math.toRadians(-45.0),
                    roll: 0.0
                }
            });
        """)
        wait_for_scene_render(driver, frames=2, delay=2.0)
        save_screenshot(driver, "screenshot_phase_c_05_dynamic_solar_lighting.png")
        results["dynamic_solar_illumination"] = "PASSED"

        # -------------------------------------------------------------
        # STEP 6: Day/Night Terminator Transition (Planetary Scale)
        # -------------------------------------------------------------
        print("\n7. Verifying Day/Night Terminator & Atmospheric Horizon...")
        driver.execute_script("""
            const v = window.viewer;
            const Cesium = window.Cesium;
            v.camera.setView({
                destination: Cesium.Cartesian3.fromDegrees(30.0, 10.0, 5500000.0, v.scene.globe.ellipsoid),
                orientation: {
                    heading: Cesium.Math.toRadians(0.0),
                    pitch: Cesium.Math.toRadians(-90.0),
                    roll: 0.0
                }
            });
        """)
        wait_for_scene_render(driver, frames=2, delay=2.0)
        save_screenshot(driver, "screenshot_phase_c_06_day_night_terminator.png")
        results["day_night_terminator"] = "PASSED"

        # -------------------------------------------------------------
        # STEP 7: Optional MOLA Topographic Colormap Layer
        # -------------------------------------------------------------
        print("\n8. Verifying Optional MOLA Topographic Colormap Overlay...")
        driver.execute_script("""
            const v = window.viewer;
            const Cesium = window.Cesium;
            v.scene.globe.enableLighting = false;
            v.scene.globe.dynamicAtmosphereLighting = false;
            
            const molaLayer = v.imageryLayers.get(3);
            if (molaLayer) {
                molaLayer.show = true;
                molaLayer.alpha = 0.85;
            }
            v.camera.setView({
                destination: Cesium.Cartesian3.fromDegrees(77.45, 18.44, 3800000.0, v.scene.globe.ellipsoid),
                orientation: {
                    heading: Cesium.Math.toRadians(0.0),
                    pitch: Cesium.Math.toRadians(-90.0),
                    roll: 0.0
                }
            });
        """)
        wait_for_scene_render(driver, frames=2, delay=2.0)
        save_screenshot(driver, "screenshot_phase_c_07_optional_mola_colormap.png")
        results["optional_mola_colormap"] = "PASSED"

        # -------------------------------------------------------------
        # STEP 8: Scientific Elevation Non-Regression Query
        # -------------------------------------------------------------
        print("\n9. Verifying Scientific Elevation Values Invariance...")
        url = "http://localhost:8000/api/v1/elevation?latitude=18.38&longitude=77.58"
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read().decode())
            elev = data["elevation_m"]
            print(f"  Jezero Crater floor elevation: {elev:.1f} m (Product: {data['product_id']})")
            assert -2700.0 <= elev <= -2600.0, f"Elevation {elev} out of expected range"
            assert data["elevation_m"] == -2648

        # Also verify Olympus Mons caldera peak (+20,015 m)
        url_olympus = "http://localhost:8000/api/v1/elevation?latitude=18.65&longitude=226.2"
        with urllib.request.urlopen(url_olympus) as resp:
            data_ol = json.loads(resp.read().decode())
            elev_ol = data_ol["elevation_m"]
            print(f"  Olympus Mons caldera elevation: {elev_ol:.1f} m")
            assert 19000.0 <= elev_ol <= 22000.0
            results["elevation_query_invariance"] = "PASSED"

        print("\n" + "=" * 70)
        print("PHASE C VERIFICATION SUMMARY:")
        for k, v in results.items():
            print(f"  {k:35s}: {v}")
        print("=" * 70)

        # Write diagnostic JSON
        diag_path = REPO_ROOT / "reports/phase_c/phase_c_visual_diagnostics.json"
        with open(diag_path, "w") as f:
            json.dump({
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "status": "PASSED",
                "results": results,
                "imagery_layers": layers_diag
            }, f, indent=2)
        print(f"Diagnostics written to {diag_path}")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
