import time
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

    try:
        # Load page
        log("Loading platform...")
        driver.get('http://localhost:5173')
        time.sleep(2.5)

        # 4. Planetary Interior X-Ray
        log("Testing X-Ray view...")
        btn_xray = driver.find_element(By.XPATH, "//button[contains(., 'X-Ray')]")
        driver.execute_script('arguments[0].click();', btn_xray)
        time.sleep(2.0)
        driver.save_screenshot('reports/view_04_interior_xray.png')
        log("Captured View 04: Interior X-Ray")
        # Close X-Ray
        driver.execute_script('arguments[0].click();', btn_xray)
        time.sleep(1.0)

        # 5. Rover Routing Planner
        log("Testing Traverse / Rover Routing...")
        btn_traverse = driver.find_element(By.XPATH, "//button[contains(., 'Traverse')]")
        driver.execute_script('arguments[0].click();', btn_traverse)
        time.sleep(1.5)
        driver.save_screenshot('reports/view_05_rover_routing.png')
        log("Captured View 05: Rover Routing")
        # Close Traverse
        driver.execute_script('arguments[0].click();', btn_traverse)
        time.sleep(1.0)

        # 6. Visual Intelligence Photo Match
        log("Testing Photo Match...")
        btn_photo = driver.find_element(By.XPATH, "//button[contains(., 'Photo Match')]")
        driver.execute_script('arguments[0].click();', btn_photo)
        time.sleep(1.5)
        driver.save_screenshot('reports/view_06_photo_match.png')
        log("Captured View 06: Photo Match")
        # Close Photo Match
        btn_close = driver.find_element(By.XPATH, "//div[contains(@class, 'fixed')]//button[contains(@class, 'hover:bg-slate-800')]")
        driver.execute_script('arguments[0].click();', btn_close)
        time.sleep(1.0)

        # 7. Mars Region Discovery
        log("Testing Region Discovery...")
        btn_regions = driver.find_element(By.XPATH, "//button[contains(., 'Regions')]")
        driver.execute_script('arguments[0].click();', btn_regions)
        time.sleep(1.5)
        driver.save_screenshot('reports/view_07_region_discovery.png')
        log("Captured View 07: Region Discovery")
        # Close Region Discovery
        driver.execute_script('arguments[0].click();', btn_regions)
        time.sleep(1.0)

        # 8. Researcher Workspace
        log("Testing Workspace...")
        btn_ws = driver.find_element(By.XPATH, "//button[contains(., 'Workspace')]")
        driver.execute_script('arguments[0].click();', btn_ws)
        time.sleep(1.5)
        driver.save_screenshot('reports/view_08_workspace.png')
        log("Captured View 08: Workspace")
        # Close Workspace
        driver.execute_script('arguments[0].click();', btn_ws)
        time.sleep(1.0)

        # 9. AI Scientist
        log("Testing Ask Zuhura AI Scientist...")
        btn_ai = driver.find_element(By.XPATH, "//button[contains(., 'Ask Zuhura')]")
        driver.execute_script('arguments[0].click();', btn_ai)
        time.sleep(1.5)
        driver.save_screenshot('reports/view_09_ai_scientist.png')
        log("Captured View 09: AI Scientist")

        log("All views captured successfully!")
    finally:
        driver.quit()

if __name__ == '__main__':
    run()
