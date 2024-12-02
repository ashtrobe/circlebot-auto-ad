import requests
import time
import logging
import sys
from datetime import datetime

# Setup logging for debugging and error tracking
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create handlers
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)  # General info logging for console

file_handler = logging.FileHandler('app.log')
file_handler.setLevel(logging.INFO)  # Log everything to a file

# Formatter for logs
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Suppress tracking URL logs in the console
class NoTrackingFilter(logging.Filter):
    def filter(self, record):
        return not any(substring in record.getMessage() for substring in [
            "Sending tracking request to:", 
            "Tracking request successful:",
            "Ad claimed successfully"
        ])

console_handler.addFilter(NoTrackingFilter())

# ANSI escape codes for color formatting
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"

# Headers for the requests
headers = {
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'authorization': 'Bearer your_authorization_token',  # Replace with your actual authorization token
    'cache-control': 'max-age=0',
    'content-type': 'application/json',
    'origin': 'https://bot.toncircle.org',
    'pragma': 'no-cache',
    'referer': 'https://bot.toncircle.org/',
    'x-requested-with': 'org.telegram.messenger',
}

# Constant block ID
BLOCK_ID = 3852

# Function to build the URL for claiming an ad
def build_ad_url(tg_id, tg_platform, platform, language, chat_type, chat_instance, top_domain):
    return f"https://api.adsgram.ai/adv?blockId={BLOCK_ID}&tg_id={tg_id}&tg_platform={tg_platform}&platform={platform}&language={language}&chat_type={chat_type}&chat_instance={chat_instance}&top_domain={top_domain}"

# Function to read session parameters from a file
def read_session_params(filename="data.txt"):
    session_params = {}
    try:
        with open(filename, "r") as file:
            for line in file:
                line = line.strip()
                if "=" in line:
                    key, value = line.split("=", 1)
                    session_params[key.strip()] = value.strip()

        required_keys = ['tg_id', 'tg_platform', 'language', 'chat_type', 'chat_instance', 'top_domain']
        missing_keys = [key for key in required_keys if key not in session_params]
        if missing_keys:
            logger.error(f"Missing required keys in the session file: {', '.join(missing_keys)}")
            return None

        return session_params
    except FileNotFoundError:
        logger.error(f"{RED}File {filename} not found.{RESET}")
        return None
    except Exception as e:
        logger.error(f"{RED}Error reading session parameters from file: {e}{RESET}")
        return None

# Function to send a request for claiming ads
def claim_ad(tg_id, tg_platform, platform, language, chat_type, chat_instance, top_domain):
    ad_url = build_ad_url(tg_id, tg_platform, platform, language, chat_type, chat_instance, top_domain)
    try:
        response = requests.get(ad_url, headers=headers)

        if response.status_code == 200:
            ad_data = response.json()
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"{CYAN}{timestamp} - ✨ Ad Reward Claimed, added +1000 Sparks!{RESET}")

            logger.info(f"Ad claimed successfully: {ad_url}")
            tracking_urls = [tracking.get("value") for tracking in ad_data.get("banner", {}).get("trackings", [])]
            for tracking_url in tracking_urls:
                logger.info(f"Sending tracking request to: {tracking_url}")
                try:
                    tracking_response = requests.get(tracking_url)
                    if tracking_response.status_code == 200:
                        logger.info(f"Tracking request successful: {tracking_url}")
                    else:
                        logger.error(f"Failed tracking request: {tracking_url}, Status Code: {tracking_response.status_code}")
                except Exception as e:
                    logger.error(f"Error during tracking request: {tracking_url}, Error: {e}")
        else:
            print(f"{RED}❌ Failed to claim ad. Status Code: {response.status_code}{RESET}")
            logger.error(f"Failed to claim ad: {ad_url}, Response: {response.text}")
    except Exception as e:
        print(f"{RED}⚠️ Error claiming ad. Check logs for more details.{RESET}")
        logger.error(f"Error claiming ad: {ad_url}, Error: {e}")

# Function to automatically watch ads in a loop
def watch_ads():
    session_params = read_session_params("data.txt")
    if session_params is None:
        return

    tg_id = session_params.get("tg_id")
    tg_platform = session_params.get("tg_platform")
    language = session_params.get("language")
    chat_type = session_params.get("chat_type")
    chat_instance = session_params.get("chat_instance")
    top_domain = session_params.get("top_domain")

    if not all([tg_id, tg_platform, language, chat_type, chat_instance, top_domain]):
        print(f"{RED}❌ Missing session parameters. Check your data file.{RESET}")
        logger.error("Missing one or more required parameters in the session file.")
        return

    while True:
        platform = 'Win32'
        claim_ad(tg_id, tg_platform, platform, language, chat_type, chat_instance, top_domain)
        print(f"{YELLOW}⏳ Waiting before claiming the next AD...{RESET}")
        time.sleep(150)

# Start the ad watching process
watch_ads()
