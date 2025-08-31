import requests
import os

def get_proxy_config():
    gateway = os.getenv('MIRAGE_NET_GATEWAY')
    if not gateway:
        return None
    try:
        response = requests.get(f"http://{gateway}:8082/request_proxy", timeout=10)
        if response.status_code == 200:
            print(f"[MIRAGE_NET] Got proxy config from Mirage Net. response: {response.__annotations__}")
            return response.json()
        else:
            print(f"[MIRAGE_NET] Failed to get proxy config, status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException:
        return None