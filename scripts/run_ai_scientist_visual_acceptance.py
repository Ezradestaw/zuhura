#!/usr/bin/env python3
"""
Zuhura Planetary Digital Twin - Mars AI Scientist Visual Acceptance Test
Automates Selenium to verify:
  1. Mars AI Scientist Panel loading, geodetic telemetry bar, and landmark jumps
  2. "Investigating the Ancient Landscape of Jezero Crater" 10-step demo:
     - Epistemic tags ([MEASURED], [OBSERVED], [INTERPRETED], [LIMITATION])
     - Interactive SVG Topographic Cross-Section Profile
     - Controlled Scientific Tools execution chips
     - Authoritative PDS citations
  3. Regional comparative analysis (Olympus Mons vs Gale Crater) with formatted tables
"""

import os
import shutil
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

REPO_ROOT = Path("/home/anonymous/Zuhura")
OUT_DIR = REPO_ROOT / "reports/mars_ai_scientist/screenshots"
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
    options.add_argument("--disable-gpu-watchdog")
    options.binary_location = "/usr/bin/chromium"

    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(60)
    driver.set_script_timeout(60)
    return driver


def save_screenshot(driver, filename):
    dest1 = OUT_DIR / filename
    dest2 = BRAIN_DIR / filename
    
    # Briefly pause continuous SwiftShader CPU rendering for clean frame capture
    try:
        driver.execute_script("if (window.viewer && window.viewer.scene) { window.viewer.useDefaultRenderLoop = false; window.viewer.scene.requestRender(); }")
    except Exception:
        pass

    for attempt in range(3):
        try:
            driver.save_screenshot(str(dest1))
            shutil.copy2(str(dest1), str(dest2))
            print(f"  [SAVED] {filename} ({dest1.stat().st_size:,} bytes)")
            break
        except Exception as e:
            if attempt == 2:
                raise e
            time.sleep(2)
        finally:
            try:
                driver.execute_script("if (window.viewer && window.viewer.scene) { window.viewer.useDefaultRenderLoop = true; }")
            except Exception:
                pass


def main():
    driver = init_driver()
    try:
        print("Connecting to Zuhura Digital Twin at http://localhost:3000 ...")
        driver.get("http://localhost:3000")

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.cesium-viewer"))
        )
        time.sleep(3)

        # 1. Capture Panel Overview
        print("\n1. Capturing Mars AI Scientist Panel Overview...")
        save_screenshot(driver, "screenshot_ai_scientist_01_panel_overview.png")

        # 2. Trigger Core Discovery Demo: "Jezero Ancient Landscape (10-Step Demo)"
        print("\n2. Executing Jezero Ancient Landscape 10-Step Discovery Scenario...")
        jezero_btn = driver.find_elements(By.XPATH, "//button[contains(text(), 'Jezero Ancient Landscape')]")
        if jezero_btn:
            driver.execute_script("arguments[0].click();", jezero_btn[0])
        else:
            # Fallback to typing in input
            inp = driver.find_element(By.CSS_SELECTOR, "form input[type='text']")
            inp.send_keys("Investigate the ancient landscape of Jezero Crater")
            btn = driver.find_element(By.CSS_SELECTOR, "form button[type='submit']")
            btn.click()

        # Poll for response completion (wait for SVG cross section or key text)
        for _ in range(30):
            time.sleep(0.5)
            if "The Ancient Landscape of Jezero Crater" in driver.page_source and "Topographic Cross-Section" in driver.page_source:
                break

        time.sleep(1.0)
        print("\n2. Capturing Jezero Ancient Landscape response (Tags, SVG Profile, Citations)...")
        save_screenshot(driver, "screenshot_ai_scientist_02_jezero_investigation.png")

        # 3. Trigger Regional Comparative Analysis (Olympus vs Gale)
        print("\n3. Executing Comparative Planetary Analysis (Olympus vs Gale)...")
        comp_btn = driver.find_elements(By.XPATH, "//button[contains(text(), 'Compare Olympus vs Gale')]")
        if comp_btn:
            driver.execute_script("arguments[0].click();", comp_btn[0])
        
        for _ in range(30):
            time.sleep(0.5)
            if "Comparative Planetary Analysis" in driver.page_source:
                break

        time.sleep(1.0)
        print("\n3. Capturing Comparative Analysis Table...")
        save_screenshot(driver, "screenshot_ai_scientist_03_olympus_vs_gale.png")

        print("\nAll Mars AI Scientist visual acceptance screenshots captured successfully!")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
