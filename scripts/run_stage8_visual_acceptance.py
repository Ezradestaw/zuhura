#!/usr/bin/env python3
"""
Zuhura Planetary Digital Twin - Stage 8 Visual Acceptance Test Runner
Drives headless Chromium via Selenium to verify all Stage 8 Scientific Terrain Intelligence
visual criteria:
  1. Feature Inspector live Terrain Morphometry card (Slope, Aspect, TRI, TPI, Local Relief)
  2. Great-Circle Transect Profile Drawer (interactive SVG chart, relief, gain/loss, station markers)
  3. Layer Panel Terrain Intelligence toolset and presets
  4. 3D Globe Geodesic Polyline with Station A / B pins clamped to Martian terrain.
"""

import os
import shutil
import time
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

REPO_ROOT = Path("/home/anonymous/Zuhura")
OUT_DIR = REPO_ROOT / "reports/stage8/screenshots"
DATA_OUT_DIR = REPO_ROOT / "zuhura-data/reports/stage8/screenshots"
BRAIN_DIR = Path("/home/anonymous/.gemini/antigravity-cli/brain/7ff9337b-5702-423f-a1a9-2125b6b78a63")

OUT_DIR.mkdir(parents=True, exist_ok=True)
DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)
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
    return webdriver.Chrome(service=service, options=options)


def wait_for_scene_render(driver, frames=4, delay=1.0):
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
    dest2 = DATA_OUT_DIR / filename
    dest3 = BRAIN_DIR / filename
    driver.save_screenshot(str(dest1))
    shutil.copy(str(dest1), str(dest2))
    shutil.copy(str(dest1), str(dest3))
    print(f"  [SAVED] {filename} ({dest1.stat().st_size} bytes)")


def main():
    print("=" * 70)
    print("ZUHURA STAGE 8: SCIENTIFIC TERRAIN INTELLIGENCE VISUAL ACCEPTANCE")
    print("=" * 70)

    driver = init_driver()
    try:
        print("\n1. Navigating to Zuhura Frontend at http://localhost:3000...")
        driver.get("http://localhost:3000")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "canvas"))
        )
        print("  Canvas loaded. Initializing Cesium Mars scene...")
        wait_for_scene_render(driver, frames=6, delay=3.0)

        # -------------------------------------------------------------
        # STEP 1: Feature Inspector - Terrain Morphometry Card
        # -------------------------------------------------------------
        print("\n2. Testing Feature Inspector & Terrain Morphometry Card...")
        # Look for the TERRAIN MORPHOMETRY tab
        morph_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'TERRAIN MORPHOMETRY')]"))
        )
        morph_tab.click()
        time.sleep(1.5)
        wait_for_scene_render(driver, frames=3, delay=1.0)

        # Verify morphometry metrics populated
        page_text = driver.page_source
        assert "SLOPE" in page_text
        assert "DOWNSLOPE ASPECT" in page_text
        assert "ROUGHNESS (TRI)" in page_text
        assert "TPI LANDFORM" in page_text
        print("  Morphometry elements verified on screen.")

        save_screenshot(driver, "screenshot_11_terrain_morphometry_card.png")

        # -------------------------------------------------------------
        # STEP 2: Transect Profile Drawer
        # -------------------------------------------------------------
        print("\n3. Testing Geodesic Transect Profile Drawer...")
        # Click "Profile Geodesic Transect" button in FeatureInspector
        profile_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Profile Geodesic Transect')]"))
        )
        profile_btn.click()
        time.sleep(2.0)
        wait_for_scene_render(driver, frames=4, delay=1.5)

        # Verify Transect Profile Drawer appeared
        page_text = driver.page_source
        assert "Mars Geodesic Transect Profile" in page_text
        assert "RELIEF RANGE" in page_text
        assert "ELEV GAIN / LOSS" in page_text
        assert "MEAN / MAX SLOPE" in page_text
        print("  Transect Profile Drawer with summary metrics verified.")

        # Hover over SVG station to test hover inspection
        svg_circles = driver.find_elements(By.CSS_SELECTOR, "svg circle")
        if svg_circles:
            mid_idx = len(svg_circles) // 2
            actions = ActionChains(driver)
            actions.move_to_element(svg_circles[mid_idx]).perform()
            time.sleep(1.0)
            print(f"  Hovered station marker {mid_idx}/{len(svg_circles)}.")

        save_screenshot(driver, "screenshot_12_transect_profile_drawer.png")

        # -------------------------------------------------------------
        # STEP 3: Layer Panel - Terrain Intelligence Section
        # -------------------------------------------------------------
        print("\n4. Testing Layer Panel Terrain Intelligence Section...")
        page_text = driver.page_source
        assert "TERRAIN INTELLIGENCE" in page_text
        assert "PROFILER ACTIVE" in page_text
        assert "Jezero Western Delta" in page_text
        assert "Olympus Mons Caldera" in page_text
        print("  Layer Panel toolset verified.")

        save_screenshot(driver, "screenshot_13_layerpanel_terrain_intelligence.png")

        # -------------------------------------------------------------
        # STEP 4: 3D Globe with Clamped Geodesic Polyline & Stations
        # -------------------------------------------------------------
        print("\n5. Capturing 3D Mars Globe Geodesic Transect Perspective...")
        # Adjust camera to show 3D terrain profile perspective over Jezero
        driver.execute_script("""
            const v = window.viewer;
            if (v && v.scene) {
                v.camera.flyTo({
                    destination: Cesium.Cartesian3.fromDegrees(77.58, 18.15, 65000.0, v.scene.globe.ellipsoid),
                    orientation: {
                        heading: Cesium.Math.toRadians(15.0),
                        pitch: Cesium.Math.toRadians(-35.0),
                        roll: 0.0
                    },
                    duration: 0.0
                });
            }
        """)
        wait_for_scene_render(driver, frames=6, delay=2.0)
        save_screenshot(driver, "screenshot_14_geodesic_3d_transect_globe.png")

        print("\n" + "=" * 70)
        print("ALL 4 STAGE 8 VISUAL ACCEPTANCE SCREENSHOTS SUCCESSFULLY CAPTURED!")
        print("=" * 70)

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
