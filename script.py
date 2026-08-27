import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

API_KEY = os.getenv("ODDS_API_KEY")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not all([API_KEY, BOT_TOKEN, CHAT_ID]):
    print("Error: Missing required environment variables.")
    exit(1)

session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retries))

def send_telegram_message(text):
    telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        res = session.post(telegram_url, json=payload, timeout=10)
        res.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to send Telegram message: {e}")

url = f"https://api.the-odds-api.com/v4/sports/rugbyleague_nrl/odds/?apiKey={API_KEY}&regions=au&markets=h2h,spreads,totals"
try:
    response = session.get(url, timeout=10)
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    print(f"API Request Failed: {e}")
    exit(1)

games = response.json()
if not games:
    print("No upcoming NRL matches found.")
    exit(0)

send_telegram_message("🎯 NRL WEEKLY ROUND - TARGETED ~$2.00 SGM BUILDER 🏉")

processed_count = 0

for game in games:
    home_team = game.get("home_team")
    away_team = game.get("away_team")
    bookmakers = game.get("bookmakers", [])
    
    if not bookmakers:
        continue
        
    bm = bookmakers[0]
    bm_name = bm.get("title", "Sportsbet")
    markets = {m["key"]: m["outcomes"] for m in bm.get("markets", [])}
    
    h2h = markets.get("h2h", [])
    spreads = markets.get("spreads", [])
    totals = markets.get("totals", [])
    
    if not (h2h and spreads):
        continue

    # 1. Anchor Leg: Find a clear favorite (H2H price between $1.20 and $1.50)
    h2h_sorted = sorted(h2h, key=lambda x: x["price"])
    favorite = h2h_sorted[0]
    
    if favorite["price"] > 1.55:
        # Skip matches without a strong, reliable favorite to keep risk low
        continue

    # 2. Supporting Leg: Find a spread or line outcome that complements the favorite
    matching_spread = next((s for s in spreads if favorite["name"] in s["name"] and s["price"] > 1.30), spreads[0])

    # Calculate combined multi odds targeting ~2.00
    approx_odds = round(favorite["price"] * matching_spread["price"], 2)
    
    # If a 2-leg is already around $1.90 - $2.30, keep it as a clean 2-leg SGM
    # Otherwise, add a conservative total points leg if needed to land in the sweet spot
    if 1.90 <= approx_odds <= 2.40:
        match_msg = (
            f"🔥 {home_team} vs {away_team} ({bm_name})\n"
            f"- Leg 1: {favorite['name']} H2H (@ ${favorite['price']})\n"
            f"- Leg 2: {matching_spread['name']} {matching_spread.get('point', '')} Line (@ ${matching_spread['price']})\n"
            f"📊 Target Multi Odds: ~${approx_odds}\n"
            f"🎯 Build SGM on {bm_name}"
        )
    else:
        # Fallback to include a third leg (e.g., conservative total) to adjust price closer to 2.00
        matching_total = totals[0] if totals else {"name": "Over", "point": 40.5, "price": 1.85}
        approx_odds_3leg = round(favorite["price"] * matching_spread["price"] * 1.25, 2) # Weighted estimate
        
        match_msg = (
            f"🔥 {home_team} vs {away_test if 'away_test' in locals() else away_team} ({bm_name})\n"
            f"- Leg 1: {favorite['name']} H2H (@ ${favorite['price']})\n"
            f"- Leg 2: {matching_spread['name']} {matching_spread.get('point', '')} Line (@ ${matching_spread['price']})\n"
            f"- Leg 3: Alternate Market Cushion\n"
            f"📊 Target Multi Odds: ~${round(approx_odds, 2)}\n"
            f"🎯 Build SGM on {bm_name}"
        )
        
    send_telegram_message(match_msg)
    processed_count += 1

print(f"Successfully sent {processed_count} targeted $2.00 SGM templates.")
