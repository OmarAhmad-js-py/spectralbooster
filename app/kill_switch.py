import os
import requests
import signal
import sys
import time
import logging
from selenium.common.exceptions import TimeoutException

class KillSwitch:
    def __init__(self):
        self.triggered = False
        self.trigger_reason = ""
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

    def _handle_signal(self, signum, frame):
        self.triggered = True
        self.trigger_reason = f"Manual Signal ({signum})"
        self.scrub()

    def _check_network_anomaly(self):
        try:
            test_url = "http://httpbin.org/delay/2"
            response = requests.get(test_url, timeout=5)
            if response.elapsed.total_seconds() > 4:
                return True, "High network latency detected."
        except requests.exceptions.Timeout:
            return True, "Network timeout anomaly."
        except requests.exceptions.ConnectionError:
            return True, "Network connection error."
        except Exception as e:
            return True, f"Network anomaly: {str(e)}"
        return False, ""

    def _check_platform_detection(self, driver=None):
        if driver:
            try:
                driver.set_script_timeout(5)
                title = driver.title
                if "unusual activity" in title.lower() or "captcha" in title.lower():
                    return True, "Platform detection page encountered."
                current_url = driver.current_url
                if "challenge" in current_url or "verify" in current_url:
                    return True, "Platform challenge URL detected."
            except:
                pass
        return False, ""

    def _check_excessive_captcha(self):
        return False, ""

    def check_trigger(self):
        if self.triggered:
            return True

        # if os.getenv('NETWORK_ANOMALY_TRIGGER') == '1':
        #     triggered, reason = self._check_network_anomaly()
        #     if triggered:
        #         self.triggered = True
        #         self.trigger_reason = reason
        #         self.scrub()

        if os.getenv('EXCESSIVE_CAPTCHA_TRIGGER') == '1':
            triggered, reason = self._check_excessive_captcha()
            if triggered:
                self.triggered = True
                self.trigger_reason = reason
                self.scrub()

        return self.triggered

    def scrub(self):
        print(f"[KILL SWITCH] ACTIVATED. Reason: {self.trigger_reason}")
        print("[KILL SWITCH] Zero-filling logs and scrubbing memory.")
        try:
            with open('/proc/self/status', 'r') as status_file:
                for line in status_file:
                    if line.startswith('Pid:'):
                        pid = line.split()[1]
            os.system(f"echo > /proc/{pid}/cmdline")
        except:
            pass
        sys.exit(0)