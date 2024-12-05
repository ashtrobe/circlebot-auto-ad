import requests
import time
import logging
import sys
from datetime import datetime
import urllib.parse
import threading

logger = logging.getLogger()
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

file_handler = logging.FileHandler('app.log', encoding='utf-8')
file_handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)

class NoTrackingFilter(logging.Filter):
    def filter(self, record):
        if "✨ Ad Reward Claimed" in record.getMessage():
            return True
        return not any(substring in record.getMessage() for substring in [
            "Sending tracking request to:", 
            "Tracking request successful:",
            "Ad claimed successfully"
        ])

console_handler.addFilter(NoTrackingFilter())

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
PURPLE = "\033[95m"
RESET = "\033[0m"

headers = {
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'authorization': 'Bearer your_authorization_token',
    'cache-control': 'max-age=0',
    'content-type': 'application/json',
    'origin': 'https://bot.toncircle.org',
    'pragma': 'no-cache',
    'referer': 'https://bot.toncircle.org/',
    'x-requested-with': 'org.telegram.messenger',
}

BLOCK_ID = 3852

def decode_query_ids(filename="data.txt"):
    try:
        with open(filename, "r") as file:
            ids = file.readlines()
            query_data = []
            for query_id in ids:
                query_id = query_id.strip()
                parsed_params = urllib.parse.parse_qs(query_id)
                user_encoded = parsed_params.get("user", [None])[0]
                if not user_encoded:
                    logger.error("Missing 'user' parameter in query ID.")
                    continue
                user_decoded = urllib.parse.unquote(user_encoded)
                user_fixed = user_decoded.replace("true", "True").replace("false", "False")
                user_data = eval(user_fixed)
                tg_id = user_data.get("id")
                username = user_data.get("username", "Unknown")
                chat_instance = parsed_params.get("chat_instance", [None])[0]
                chat_type = parsed_params.get("chat_type", [None])[0]
                language = parsed_params.get("language_code", ["en"])[0]
                if not all([tg_id, chat_instance, chat_type]):
                    logger.error("Missing required parameters in the query ID.")
                    continue
                query_data.append({
                    "tg_id": tg_id,
                    "username": username,
                    "tg_platform": "android",
                    "language": language,
                    "chat_type": chat_type,
                    "chat_instance": chat_instance,
                    "top_domain": "app.notpx.app"
                })
            return query_data
    except Exception as e:
        logger.error(f"Error decoding query IDs: {e}")
        return []

def load_proxies(filename="proxy.txt"):
    try:
        with open(filename, "r") as file:
            proxies = file.readlines()
            proxies = [proxy.strip() for proxy in proxies if proxy.strip()]
            return proxies
    except FileNotFoundError:
        logger.error(f"{RED}Proxy file not found: {filename}{RESET}")
        return []

def build_ad_url(tg_id, tg_platform, platform, language, chat_type, chat_instance, top_domain):
    return f"https://api.adsgram.ai/adv?blockId={BLOCK_ID}&tg_id={tg_id}&tg_platform={tg_platform}&platform={platform}&language={language}&chat_type={chat_type}&chat_instance={chat_instance}&top_domain={top_domain}"

def claim_ad(tg_id, username, tg_platform, platform, language, chat_type, chat_instance, top_domain, proxy=None):
    ad_url = build_ad_url(tg_id, tg_platform, platform, language, chat_type, chat_instance, top_domain)
    try:
        proxy_dict = {
            "http": proxy
        } if proxy else None  # Using only HTTP proxy.

        if proxy:
            logger.info(f"{GREEN}Connecting to {PURPLE}{username}{RESET} {GREEN}using {proxy}{RESET}")

        response = requests.get(ad_url, headers=headers, proxies=proxy_dict)

        if response.status_code == 200:
            ad_data = response.json()
            tracking_urls = [tracking.get("value") for tracking in ad_data.get("banner", {}).get("trackings", [])]
            if not tracking_urls:
                logger.error(f"{RED}No Claim URLs found for {PURPLE}{username}{RESET}. Retrying after 5 minutes...")
                time.sleep(300)  # 5-minute delay before retrying.
                return False

            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"{CYAN}{timestamp} - ✨ Ad Reward Claimed, added +1000 Sparks to {PURPLE}{username}{RESET}!")

            for tracking_url in tracking_urls:
                logger.info(f"Sending tracking request to: {tracking_url}")
                try:
                    tracking_response = requests.get(tracking_url, proxies=proxy_dict)
                    if tracking_response.status_code == 200:
                        logger.info(f"Tracking request successful: {tracking_url}")
                    else:
                        logger.error(f"{RED}Failed tracking request: {tracking_url}, Status Code: {tracking_response.status_code}{RESET}")
                        return False

                except Exception as e:
                    logger.error(f"{RED}Error during tracking request: {tracking_url}, Error: {e}{RESET}")
                    return False

            return True
        else:
            logger.error(f"{RED}Failed to claim ad: {ad_url}, Response: {response.text}{RESET}")
            return False

    except Exception as e:
        logger.error(f"{RED}Error claiming ad: {ad_url}, Error: {e}{RESET}")
        return False

def process_account(session_params, proxy):
    tg_id = session_params.get("tg_id")
    username = session_params.get("username")
    tg_platform = session_params.get("tg_platform")
    language = session_params.get("language")
    chat_type = session_params.get("chat_type")
    chat_instance = session_params.get("chat_instance")
    top_domain = session_params.get("top_domain")

    if not all([tg_id, tg_platform, language, chat_type, chat_instance, top_domain]):
        logger.error(f"Missing one or more required parameters for {username}.")
        return

    while True:
        try:
            platform = 'Win32'
            ad_claimed = claim_ad(tg_id, username, tg_platform, platform, language, chat_type, chat_instance, top_domain, proxy)

            if not ad_claimed:
                logger.error(f"{RED}Retrying for {PURPLE}{username}{RESET} after delay...")
                continue

            logger.info(f"{YELLOW}⏳ Waiting before claiming the next AD for {PURPLE}{username}{RESET}...")
            sys.stdout.flush()
            time.sleep(150)
        except Exception as e:
            logger.error(f"{RED}An error occurred for {PURPLE}{username}{RESET}, Retrying... Error: {e}")
            continue

def watch_ads():
    session_params_list = decode_query_ids("data.txt")
    if not session_params_list:
        return

    proxies = load_proxies("proxy.txt")
    if len(session_params_list) > 1 and len(proxies) < len(session_params_list):
        logger.error("Not enough proxies to match the amount of accounts.")
        return

    threads = []
    for idx, session_params in enumerate(session_params_list):
        proxy = proxies[idx] if len(session_params_list) > 1 else None
        thread = threading.Thread(target=process_account, args=(session_params, proxy))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

watch_ads()
