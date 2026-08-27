import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Environment Variables from GitHub Secrets
API_KEY = os.getenv("ODDS_API_KEY")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not all([API_KEY, BOT_TOKEN, CHAT_ID]):
    print("Error: Missing one or more required environment variables.")
    exit(1)

# HTTP Session Configuration with Retries
session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retries))

def send_telegram_message(text):
    """Sends a clean message to Telegram."""
    telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        res = session.post(telegram_url, json=payload, timeout=10)
        res.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to send Telegram message: {e}")

# Fetch Odds Data for H2H, Spreads, and Totals
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

# Send Header
send_telegram_message("🎯 NRL WEEKLY ROUND - RULE-BASED ~2.00 SGM BUILDER 🏉")

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
    
    if not (h2h and spreads and totals):
        continue

    # --- SGM SELECTION LOGIC ---
    # 1. Leg 1: Find the match favorite (H2H price < $1.70) to act as an anchor
    h2h_sorted = sorted(h2h, key=lambda x: x["price"])
    favorite = h2h_sorted[0]
    
    if favorite["price"] > 1.70:
        # If no strong favorite, skip or pick the lowest priced head-to-head
        pass

    # 2. Leg 2: Select a conservative line outcome matching the favorite if possible, or first available spread
    matching_spread = next((s for s in spreads if favorite["name"] in s["name"]), spreads[0])
    
    # 3. Leg 3: Select an Over/Under total points market (defaulting to Over if available)
    matching_total = next((t for t in totals if "Over" in t["name"]), totals[0])

    # Calculate approximate combined multi odds (Decimal odds multiplication)
    approx_odds = round(favorite["price"] * matching_spread["price"] * matching_total["price"], 2)

    # Format Output Template
    match_msg = (
        f"🔥 {home_team} vs {away_team} ({bm_name})\n"
        f"- Leg 1: {favorite['name']} H2H (@ ${favorite['price']})\n"
        f"- Leg 2: {matching_spread['name']} {matching_spread.get('point', '')} Line (@ ${matching_spread['price']})\n"
        f"- Leg 3: Total Points {matching_total['name']} {matching_total.get('point', '')} (@ ${matching_total['price']})\n"
        f"📊 Est. Multi Odds: ~${approx_odds}\n"
        f"🎯 Build SGM on {bm_name}"
    )
    
    send_telegram_message(match_msg)
    processed_count += 1

print(f"Successfully sent {processed_count} rule-based SGM templates to Telegram.")
