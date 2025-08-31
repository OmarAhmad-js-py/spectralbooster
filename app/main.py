import os

import random
import time
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, WebDriverException
from fake_useragent import UserAgent
from dotenv import load_dotenv
import signal
import sys
from datetime import datetime, timedelta

from kill_switch import KillSwitch
import mirage_net
import chat_ai

load_dotenv()
TARGET_CHANNEL = os.getenv('TARGET_CHANNEL')
INTENSITY = os.getenv('OPERATION_INTENSITY', 'med')
MIRAGE_NET_GATEWAY = os.getenv('MIRAGE_NET_GATEWAY')
SCHEDULED_DURATION = os.getenv('SCHEDULED_DURATION', '04:00:00')

INTENSITY_PROFILES = {
    "low": {"viewer_count": 25, "chat_frequency": 0.2},
    "med": {"viewer_count": 75, "chat_frequency": 0.4},
    "high": {"viewer_count": 150, "chat_frequency": 0.6}
}
profile = INTENSITY_PROFILES[INTENSITY]

ks = KillSwitch()

def parse_duration(duration_str):
    h, m, s = duration_str.split(':')
    return timedelta(hours=int(h), minutes=int(m), seconds=int(s))

class GhostViewer:
    def __init__(self, viewer_id):
        self.viewer_id = viewer_id
        self.ua = UserAgent()
        self.options = webdriver.ChromeOptions()
        self._setup_browser_options()
        self.driver = None
        self.is_active = False
        self.session_start = None
        self.planned_session_length = random.randint(int(os.getenv('MIN_VIEWTIME', 1200)), int(os.getenv('MAX_VIEWTIME', 7200)))
        self.will_chat = np.random.random() < float(os.getenv('CHAT_ENGAGEMENT_PROBABILITY', 0.4))

    def _setup_browser_options(self):
        #self.options.add_argument('--headless=new')
        self.options.add_argument('--disable-blink-features=AutomationControlled')
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('useAutomationExtension', False)
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--disable-software-rasterizer')
        self.options.add_argument('--disable-features=VizDisplayCompositor')
        self.options.add_argument('--disable-background-timer-throttling')
        self.options.add_argument('--disable-backgrounding-occluded-windows')
        self.options.add_argument('--disable-renderer-backgrounding')
        self.options.add_argument('--single-process')
        self.options.add_argument('--no-zygote')
        self.options.add_argument('--disable-extensions')
        self.options.add_argument('--disable-plugins')
        self.options.add_argument('--disable-background-networking')
        self.options.add_argument('--disable-sync')
        self.options.add_argument('--metrics-recording-only')
        self.options.add_argument('--disable-default-apps')
        self.options.add_argument('--mute-audio')
        self.options.add_argument('--no-first-run')
        self.options.add_argument('--disable-web-security')
        self.options.add_argument('--disable-features=VizDisplayCompositor')
        self.options.add_argument(f'--user-agent={self.ua.random}')
        self.options.add_argument('--window-size=1920,1080')
        self.options.add_argument('--lang=en-US')
        self.options.add_argument('--disable-blink-features=AutomationControlled')
        self.options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        self.options.add_experimental_option('useAutomationExtension', False)

            
        if MIRAGE_NET_GATEWAY:
            self.options.add_argument(f'--proxy-server=http://{MIRAGE_NET_GATEWAY}:8082')
            print(f"[DEBUG] Using HTTP proxy: {MIRAGE_NET_GATEWAY}")

    def activate(self):
        try:
            self.driver = webdriver.Chrome(options=self.options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.set_page_load_timeout(int(os.getenv('BROWSER_TIMEOUT', 30)))
            self.driver.implicitly_wait(int(os.getenv('CONNECTION_TIMEOUT', 10)))

            print(f"[INFO] Viewer {self.viewer_id}: Navigating to target.")
            self.driver.get(f"https://www.twitch.tv/{TARGET_CHANNEL}")

            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(random.uniform(3.0, 7.0))

            self.is_active = True
            self.session_start = time.time()
            print(f"[SUCCESS] Viewer {self.viewer_id}: Activated. Session planned for {self.planned_session_length}s. Chat: {self.will_chat} Title: {self.driver.title}")
            self.driver.save_screenshot(f"viewer_{self.viewer_id}_debug.png")
            print(f"[DEBUG] Viewer {self.viewer_id}: Screenshot saved")
            
            return True
        except (TimeoutException, WebDriverException) as e:
            print(f"[FAILURE] Viewer {self.viewer_id}: Failed to activate. {e}")
            self.terminate()
            return False

    def simulate_behavior(self):
        if not self.is_active:
            return

        actions = ActionChains(self.driver)
        last_action = time.time()
        next_chat = time.time() + random.randint(60, 300)

        try:
            while self.is_active and (time.time() - self.session_start) < self.planned_session_length:
                if ks.check_trigger():
                    return

                current_time = time.time()

                if self.will_chat and current_time > next_chat and np.random.random() < 0.7:
                    self.send_chat_message()
                    next_chat = current_time + random.randint(120, 600)

                if current_time - last_action > random.randint(30, 90):
                    self.perform_idle_action(actions)
                    last_action = current_time

                time.sleep(random.uniform(5.0, 15.0))

        except Exception as e:
            print(f"[ERROR] Viewer {self.viewer_id}: Behavior simulation error. {e}")
        finally:
            self.terminate()

    def perform_idle_action(self, actions):
        try:
            action_type = random.choice(['scroll', 'move_mouse', 'minimize'])
            if action_type == 'scroll':
                scroll_amount = random.randint(200, 800)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                time.sleep(random.uniform(0.5, 2.0))
                self.driver.execute_script(f"window.scrollBy(0, {-scroll_amount//2});")
            elif action_type == 'move_mouse':
                width = 1920
                height = 1080
                x = random.randint(0, width)
                y = random.randint(0, height)
                actions.move_by_offset(x, y).perform()
                actions.reset_actions()
        except:
            pass

    def send_chat_message(self):

        if not self.is_active:
            return
        try:
            message = chat_ai.generate_message()
            chat_input = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[data-a-target='chat-input']"))
            )
            for char in message:
                chat_input.send_keys(char)
                time.sleep(random.uniform(0.05, 0.1))
            if np.random.random() < 0.8:
                chat_input.submit()
                print(f"[CHAT] Viewer {self.viewer_id}: '{message}'")
            else:
                chat_input.clear()
                print(f"[CHAT] Viewer {self.viewer_id}: Typed but deleted message.")
            time.sleep(random.uniform(2.0, 5.0))
        except Exception as e:
            pass

    def terminate(self):
        self.is_active = False
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        print(f"[INFO] Viewer {self.viewer_id}: Session terminated.")

def main():
    print(f"[INIT] SPECTRAL BOOSTER v3.0 initiating on target: {TARGET_CHANNEL}")
    print(f"[PARAMS] Intensity: {INTENSITY}, Duration: {SCHEDULED_DURATION}")
    viewers = []
    successful_activations = 0

    for i in range(profile["viewer_count"]):
        if ks.check_trigger():
            break
        viewer = GhostViewer(i)
        if viewer.activate():
            viewers.append(viewer)
            successful_activations += 1
        time.sleep(random.uniform(1.0, 3.0))

    print(f"[STATUS] {successful_activations}/{profile['viewer_count']} viewers activated successfully.")

    operation_end = datetime.now() + parse_duration(SCHEDULED_DURATION)

    try:
        while datetime.now() < operation_end:
            if ks.check_trigger():
                break
            time.sleep(5)

    finally:
        print("[SHUTDOWN] Terminating operation and all viewer sessions.")
        for viewer in viewers:
            viewer.terminate()
        print("[SHUTDOWN] Operation complete. All assets scrubbed.")

if __name__ == "__main__":
    main()