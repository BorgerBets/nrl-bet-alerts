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

# Send Header Notification
send_telegram_message("🎯 NRL WEEKLY ROUND - HIGH-PROBABILITY 2-LEG SGMs (Max $2.50) 🏉")

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
    
    if not h2h:
        continue

    # Find the shortest-priced H2H favourite
    best_h2h = min(h2h, key=lambda x: x["price"])
    fav_team = best_h2h["name"]
    
    match_msg = None

    # Priority 1: Check Spreads belonging strictly to the H2H favourite
    if spreads:
        team_spreads = [s for s in spreads if s.get("name") == fav_team]
        if team_spreads:
            # Find a spread combo that fits under the $2.50 cap (prioritising the lowest/safest line)
            valid_spreads = [s for s in team_spreads if round(best_h2h["price"] * s["price"], 2) <= 2.50]
            if valid_spreads:
                best_spread = min(valid_spreads, key=lambda x: x["price"])
            else:
                # Fallback: grab the lowest available price for this team's line to get as close to target as possible
                best_spread = min(team_spreads, key=lambda x: x["price"])
            
            odds_h2h_spread = round(best_h2h["price"] * best_spread["price"], 2)
            match_msg = (
                f"🔥 {home_team} vs {away_team} ({bm_name})\n"
                f"  ├ Leg 1: {fav_team} H2H (@ ${best_h2h['price']})\n"
                f"  └ Leg 2: {best_spread['name']} {best_spread.get('point', '')} (@ ${best_spread['price']})\n"
                f"📊 Combined 2-Leg Odds: ~${odds_h2h_spread}\n"
                f"🎯 Build SGM on {bm_name}"
            )

    # Priority 2: Fallback to Total Points if no valid spread was found
    if not match_msg and totals:
        best_total = min(totals, key=lambda x: x["price"])
        odds_h2h_total = round(best_h2h["price"] * best_total["price"], 2)
        match_msg = (
            f"🔥 {home_team} vs {away_team} ({bm_name})\n"
            f"  ├ Leg 1: {fav_team} H2H (@ ${best_h2h['price']})\n"
            f"  └ Leg 2: Total Points {best_total['name']} {best_total.get('point', '')} (@ ${best_total['price']})\n"
            f"📊 Combined 2-Leg Odds: ~${odds_h2h_total}\n"
            f"🎯 Build SGM on {bm_name}"
        )

    # Dispatch to Telegram
    if match_msg:
        send_telegram_message(match_msg)
        processed_count += 1

print(f"Successfully sent {processed_count} round match templates to Telegram.")
