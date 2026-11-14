import time
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

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
    driver.set_page_load_timeout(15)

    try:
        log("Opening http://localhost:5173...")
        driver.get('http://localhost:5173')
        time.sleep(3)
        driver.save_screenshot('reports/view_01_explorer.png')
        log("Captured 01: Explorer")

        # 2. Mission Briefing Modal: click the briefing button
        log("Opening Mission Briefing...")
        driver.execute_script("window.dispatchEvent(new KeyboardEvent('keydown', {'key': '?'}));")
        time.sleep(1.5)
        driver.save_screenshot('reports/view_02_briefing.png')
        log("Captured 02: Briefing Modal")

        # Close with Escape
        driver.execute_script("window.dispatchEvent(new KeyboardEvent('keydown', {'key': 'Escape'}));")
        time.sleep(1)

        # 3. Mission Cockpit Dashboard: click Cockpit button or dispatch '2'
        log("Opening Mission Cockpit Dashboard...")
        driver.execute_script("window.dispatchEvent(new KeyboardEvent('keydown', {'key': '2'}));")
        time.sleep(1.5)
        driver.save_screenshot('reports/view_03_cockpit.png')
        log("Captured 03: Cockpit Dashboard")

        # Return to Explorer
        driver.execute_script("window.dispatchEvent(new KeyboardEvent('keydown', {'key': '1'}));")
        time.sleep(1)

        # 4. Planetary Interior X-Ray: dispatch '4'
        log("Opening Planetary Interior X-Ray...")
        driver.execute_script("window.dispatchEvent(new KeyboardEvent('keydown', {'key': '4'}));")
        time.sleep(2)
        driver.save_screenshot('reports/view_04_interior_xray.png')
        log("Captured 04: Interior X-Ray")

        # Close X-Ray
        driver.execute_script("window.dispatchEvent(new KeyboardEvent('keydown', {'key': 'Escape'}));")
        time.sleep(1)

        # 5. Rover Mobility Planner: dispatch '3'
        log("Opening Rover Mobility Planner...")
        driver.execute_script("window.dispatchEvent(new KeyboardEvent('keydown', {'key': '3'}));")
        time.sleep(1.5)
        driver.save_screenshot('reports/view_05_rover_routing.png')
        log("Captured 05: Rover Routing")

        # Close Routing
        driver.execute_script("window.dispatchEvent(new KeyboardEvent('keydown', {'key': 'Escape'}));")
        time.sleep(1)

        # 6. Visual Intelligence Photo Match: dispatch '5'
        log("Opening Visual Intelligence Photo Match...")
        driver.execute_script("window.dispatchEvent(new KeyboardEvent('keydown', {'key': '5'}));")
        time.sleep(1.5)
        driver.save_screenshot('reports/view_06_photo_match.png')
        log("Captured 06: Photo Match")

        # Close Photo Match
        driver.execute_script("window.dispatchEvent(new KeyboardEvent('keydown', {'key': 'Escape'}));")
        time.sleep(1)

        # 7. Mars Region Discovery: dispatch '6'
        log("Opening Mars Region Discovery...")
        driver.execute_script("window.dispatchEvent(new KeyboardEvent('keydown', {'key': '6'}));")
        time.sleep(1.5)
        driver.save_screenshot('reports/view_07_region_discovery.png')
        log("Captured 07: Region Discovery")

        # Close Region Discovery
        driver.execute_script("window.dispatchEvent(new KeyboardEvent('keydown', {'key': 'Escape'}));")
        time.sleep(1)

        # 8. Researcher Workspace: dispatch '8'
        log("Opening Researcher Workspace...")
        driver.execute_script("window.dispatchEvent(new KeyboardEvent('keydown', {'key': '8'}));")
        time.sleep(1.5)
        driver.save_screenshot('reports/view_08_workspace.png')
        log("Captured 08: Researcher Workspace")

        log("All views captured successfully!")
    except Exception as e:
        log(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == '__main__':
    run()
