import os
import requests

API_KEY = os.getenv("ODDS_API_KEY")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Check if environment variables are pulling correctly
if not API_KEY or not BOT_TOKEN or not CHAT_ID:
    print("Error: One or more secret keys are missing in GitHub Actions settings.")
    exit(1)

# API Request
url = f"https://api.the-odds-api.com/v4/sports/rugbyleague_nrl/odds/?apiKey={API_KEY}&regions=au&markets=h2h"
response = requests.get(url)

print(f"HTTP Status Code: {response.status_code}")

if response.status_code != 200:
    print(f"API Error Response: {response.text}")
    exit(1)

data = response.json()
print(f"Successfully retrieved {len(data)} games.")

# Send test message to Telegram to confirm connection
telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
payload = {
    "chat_id": CHAT_ID,
    "text": f"NRL Alert Bot Connected! Found {len(data)} upcoming matches."
}
req = requests.post(telegram_url, json=payload)
print(f"Telegram status code: {req.status_code}")
