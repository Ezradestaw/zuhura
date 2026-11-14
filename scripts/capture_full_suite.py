import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

def log(msg):
    print(msg, flush=True)

def run():
    options = Options()
    options.binary_location = '/usr/bin/chromium'
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.page_load_strategy = 'eager'

    service = Service('/usr/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=options)

    try:
        log("Loading platform...")
        driver.get('http://localhost:5173')
        time.sleep(3.0)

        # 1. Clean Explorer View
        driver.save_screenshot('reports/view_01_explorer.png')
        log("Saved view_01_explorer.png")

        # 2. Layer Panel Expanded
        driver.execute_script("window.__zuhura.globe.getState().setIsLayerPanelCollapsed(false);")
        time.sleep(1.0)
        driver.save_screenshot('reports/view_10_layers_expanded.png')
        log("Saved view_10_layers_expanded.png")
        driver.execute_script("window.__zuhura.globe.getState().setIsLayerPanelCollapsed(true);")
        time.sleep(0.5)

        # 3. Mission Briefing Modal
        driver.execute_script("window.__zuhura.globe.getState().setIsMissionBriefingOpen(true);")
        time.sleep(1.0)
        driver.save_screenshot('reports/view_02_briefing.png')
        log("Saved view_02_briefing.png")
        driver.execute_script("window.__zuhura.globe.getState().setIsMissionBriefingOpen(false);")
        time.sleep(0.5)

        # 4. Mission Cockpit Dashboard
        driver.execute_script("window.__zuhura.globe.getState().setActiveMainView('overview');")
        time.sleep(1.2)
        driver.save_screenshot('reports/view_03_cockpit.png')
        log("Saved view_03_cockpit.png")
        driver.execute_script("window.__zuhura.globe.getState().setActiveMainView('explorer');")
        time.sleep(0.5)

        # 5. Rover Routing Planner
        driver.execute_script("window.__zuhura.globe.getState().setIsRoutePlannerOpen(true);")
        time.sleep(1.2)
        driver.save_screenshot('reports/view_05_rover_routing.png')
        log("Saved view_05_rover_routing.png")
        driver.execute_script("window.__zuhura.globe.getState().setIsRoutePlannerOpen(false);")
        time.sleep(0.5)

        # 6. Visual Intelligence Photo Match
        driver.execute_script("window.__zuhura.globe.getState().setIsPinpointOpen(true);")
        time.sleep(1.2)
        driver.save_screenshot('reports/view_06_photo_match.png')
        log("Saved view_06_photo_match.png")
        driver.execute_script("window.__zuhura.globe.getState().setIsPinpointOpen(false);")
        time.sleep(0.5)

        # 7. Mars Region Discovery
        driver.execute_script("window.__zuhura.globe.getState().setIsRegionDiscoveryOpen(true);")
        time.sleep(1.2)
        driver.save_screenshot('reports/view_07_region_discovery.png')
        log("Saved view_07_region_discovery.png")
        driver.execute_script("window.__zuhura.globe.getState().setIsRegionDiscoveryOpen(false);")
        time.sleep(0.5)

        # 8. Researcher Workspace
        driver.execute_script("window.__zuhura.workspace.getState().setIsWorkspaceOpen(true);")
        time.sleep(1.2)
        driver.save_screenshot('reports/view_08_workspace.png')
        log("Saved view_08_workspace.png")
        driver.execute_script("window.__zuhura.workspace.getState().setIsWorkspaceOpen(false);")
        time.sleep(0.5)

        # 9. AI Scientist
        driver.execute_script("window.__zuhura.ai.getState().setIsOpen(true);")
        time.sleep(1.2)
        driver.save_screenshot('reports/view_09_ai_scientist.png')
        log("Saved view_09_ai_scientist.png")
        driver.execute_script("window.__zuhura.ai.getState().setIsOpen(false);")
        time.sleep(0.5)

        # 10. Planetary Interior X-Ray
        log("Opening Interior X-Ray...")
        driver.execute_script("window.__zuhura.globe.getState().setIsXRayMarsOpen(true);")
        time.sleep(2.5)
        driver.save_screenshot('reports/view_04_interior_xray.png')
        log("Saved view_04_interior_xray.png")
        driver.execute_script("window.__zuhura.globe.getState().setIsXRayMarsOpen(false);")

        log("COMPLETE: All 10 views captured!")
    finally:
        driver.quit()

if __name__ == '__main__':
    run()
