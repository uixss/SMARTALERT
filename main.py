import os
import sqlite3
import time
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

def get_web_history(browser_name, path):
    profile_path = os.path.join(path, 'Default', 'History')
    if not os.path.exists(profile_path):
        return []
    
    temp_copy = os.path.join(os.getenv('TEMP', '/tmp'), f'{browser_name}_history')
    try:
        shutil.copy(profile_path, temp_copy)
    except Exception:
        return []
    
    conn = sqlite3.connect(temp_copy)
    cursor = conn.cursor()
    time_threshold = (datetime.now(timezone.utc) - timedelta(minutes=10)).timestamp() * 1000000 + 11644473600000000
    cursor.execute('SELECT url, title, last_visit_time FROM urls WHERE last_visit_time > ? ORDER BY last_visit_time DESC LIMIT 10', (time_threshold,))
    
    history = [(row[0], row[1], datetime.fromtimestamp(row[2] / 1000000 - 11644473600, timezone.utc).strftime('%Y-%m-%d %H:%M:%S')) for row in cursor.fetchall()]
    
    conn.close()
    os.remove(temp_copy)
    return history

def get_gecko_profiles():
    appdata = os.getenv("APPDATA", os.path.expanduser("~/.mozilla"))
    profiles_ini = Path(appdata, "Mozilla", "Firefox", "profiles.ini")
    profiles = []
    
    if profiles_ini.exists():
        with open(profiles_ini, "r", encoding="utf-8") as file:
            for line in file.readlines():
                if line.startswith("Path="):
                    profile_path = Path(appdata, "Mozilla", "Firefox", line.strip().split("=")[1])
                    if profile_path.exists():
                        profiles.append(profile_path)
    return profiles

def extract_history(profile):
    history_path = profile / "places.sqlite"
    if not history_path.exists():
        return []
    
    conn = sqlite3.connect(history_path)
    cursor = conn.cursor()
    time_threshold = (datetime.now(timezone.utc) - timedelta(minutes=10)).timestamp() * 1000000
    cursor.execute("SELECT url, title, last_visit_date FROM moz_places WHERE last_visit_date > ? ORDER BY last_visit_date DESC LIMIT 10", (time_threshold,))
    history = [(url, title, datetime.fromtimestamp(last_visit / 1000000, timezone.utc).strftime('%Y-%m-%d %H:%M:%S')) for url, title, last_visit in cursor.fetchall()]
    
    conn.close()
    return history

def monitor_history():
    appdata = os.getenv('LOCALAPPDATA', os.path.expanduser("~/.config"))
    roaming = os.getenv('APPDATA', os.path.expanduser("~/.config"))

    browsers = {
        'avast': os.path.join(appdata, 'AVAST Software', 'Browser', 'User Data'),
        'amigo': os.path.join(appdata, 'Amigo', 'User Data'),
        'torch': os.path.join(appdata, 'Torch', 'User Data'),
        'kometa': os.path.join(appdata, 'Kometa', 'User Data'),
        'orbitum': os.path.join(appdata, 'Orbitum', 'User Data'),
        'cent-browser': os.path.join(appdata, 'CentBrowser', 'User Data'),
        '7star': os.path.join(appdata, '7Star', '7Star', 'User Data'),
        'sputnik': os.path.join(appdata, 'Sputnik', 'Sputnik', 'User Data'),
        'vivaldi': os.path.join(appdata, 'Vivaldi', 'User Data'),
        'chromium': os.path.join(appdata, 'Chromium', 'User Data'),
        'chrome-canary': os.path.join(appdata, 'Google', 'Chrome SxS', 'User Data'),
        'chrome': os.path.join(appdata, 'Google', 'Chrome', 'User Data'),
        'epic-privacy-browser': os.path.join(appdata, 'Epic Privacy Browser', 'User Data'),
        'msedge': os.path.join(appdata, 'Microsoft', 'Edge', 'User Data'),
        'msedge-canary': os.path.join(appdata, 'Microsoft', 'Edge SxS', 'User Data'),
        'msedge-beta': os.path.join(appdata, 'Microsoft', 'Edge Beta', 'User Data'),
        'msedge-dev': os.path.join(appdata, 'Microsoft', 'Edge Dev', 'User Data'),
        'uran': os.path.join(appdata, 'uCozMedia', 'Uran', 'User Data'),
        'yandex': os.path.join(appdata, 'Yandex', 'YandexBrowser', 'User Data'),
        'brave': os.path.join(appdata, 'BraveSoftware', 'Brave-Browser', 'User Data'),
        'iridium': os.path.join(appdata, 'Iridium', 'User Data'),
        'coccoc': os.path.join(appdata, 'CocCoc', 'Browser', 'User Data'),
        'opera': os.path.join(roaming, 'Opera Software', 'Opera Stable'),
        'opera-gx': os.path.join(roaming, 'Opera Software', 'Opera GX Stable')
    }

        
    keywords = ["hacking", "malware", "facebook","phishing", "darkweb", "exploit"]
    alerted_urls = set()
    
    alerted_urls = {}

    while True:
        for browser, path in browsers.items():
            if os.path.exists(path):
                history = get_web_history(browser, path)
                for url, title, visit_time in history:
                    visit_time_obj = datetime.strptime(visit_time, '%Y-%m-%d %H:%M:%S')

                    if any(keyword in url.lower() for keyword in keywords):
                        if url not in alerted_urls or visit_time_obj > alerted_urls[url]:
                            print(f'[ALERTA] {browser}: {url} - {title} ({visit_time})')
                            alerted_urls[url] = visit_time_obj  

        for profile in get_gecko_profiles():
            history = extract_history(profile)
            for url, title, visit_time in history:
                visit_time_obj = datetime.strptime(visit_time, '%H:%M:%S')

                if any(keyword in url.lower() for keyword in keywords):
                    if url not in alerted_urls or visit_time_obj > alerted_urls[url]:
                        print(f'[ALERTA] Firefox: {url} - {title} ({visit_time})')
                        alerted_urls[url] = visit_time_obj  

        time.sleep(2)


if __name__ == "__main__":
    monitor_history()
