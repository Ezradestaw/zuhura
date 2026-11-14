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
        time.sleep(2.5)

        # 4. Planetary Interior X-Ray (key '4')
        try:
            log("Capturing View 04: Interior X-Ray (Key 4)...")
            driver.execute_script("window.dispatchEvent(new KeyboardEvent('keydown', {'key': '4'}));")
            time.sleep(2.0)
            driver.save_screenshot('reports/view_04_interior_xray.png')
            log("Saved view_04_interior_xray.png")
            driver.execute_script("window.dispatchEvent(new KeyboardEvent('keydown', {'key': 'Escape'}));")
            time.sleep(1.0)
        except Exception as e:
            log(f"View 04 error: {e}")

        # 5. Rover Routing Planner (key '3')
        try:
            log("Capturing View 05: Rover Routing (Key 3)...")
            driver.execute_script("window.dispatchEvent(new KeyboardEvent('keydown', {'key': '3'}));")
            time.sleep(1.5)
            driver.save_screenshot('reports/view_05_rover_routing.png')
            log("Saved view_05_rover_routing.png")
            driver.execute_script("window.dispatchEvent(new KeyboardEvent('keydown', {'key': 'Escape'}));")
            time.sleep(1.0)
        except Exception as e:
            log(f"View 05 error: {e}")

        # 6. Visual Intelligence Photo Match (key '5')
        try:
            log("Capturing View 06: Photo Match (Key 5)...")
            driver.execute_script("window.dispatchEvent(new KeyboardEvent('keydown', {'key': '5'}));")
            time.sleep(1.5)
            driver.save_screenshot('reports/view_06_photo_match.png')
            log("Saved view_06_photo_match.png")
            driver.execute_script("window.dispatchEvent(new KeyboardEvent('keydown', {'key': 'Escape'}));")
            time.sleep(1.0)
        except Exception as e:
            log(f"View 06 error: {e}")

        # 7. Mars Region Discovery (key '6')
        try:
            log("Capturing View 07: Region Discovery (Key 6)...")
            driver.execute_script("window.dispatchEvent(new KeyboardEvent('keydown', {'key': '6'}));")
            time.sleep(1.5)
            driver.save_screenshot('reports/view_07_region_discovery.png')
            log("Saved view_07_region_discovery.png")
            driver.execute_script("window.dispatchEvent(new KeyboardEvent('keydown', {'key': 'Escape'}));")
            time.sleep(1.0)
        except Exception as e:
            log(f"View 07 error: {e}")

        # 8. Researcher Workspace (key '8')
        try:
            log("Capturing View 08: Workspace (Key 8)...")
            driver.execute_script("window.dispatchEvent(new KeyboardEvent('keydown', {'key': '8'}));")
            time.sleep(1.5)
            driver.save_screenshot('reports/view_08_workspace.png')
            log("Saved view_08_workspace.png")
            driver.execute_script("window.dispatchEvent(new KeyboardEvent('keydown', {'key': 'Escape'}));")
            time.sleep(1.0)
        except Exception as e:
            log(f"View 08 error: {e}")

        # 9. AI Scientist (key '7')
        try:
            log("Capturing View 09: AI Scientist (Key 7)...")
            driver.execute_script("window.dispatchEvent(new KeyboardEvent('keydown', {'key': '7'}));")
            time.sleep(1.5)
            driver.save_screenshot('reports/view_09_ai_scientist.png')
            log("Saved view_09_ai_scientist.png")
            driver.execute_script("window.dispatchEvent(new KeyboardEvent('keydown', {'key': 'Escape'}));")
            time.sleep(1.0)
        except Exception as e:
            log(f"View 09 error: {e}")

        log("All views completed successfully!")
    finally:
        driver.quit()

if __name__ == '__main__':
    run()
