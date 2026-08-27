import os
import requests

API_KEY = os.getenv("ODDS_API_KEY")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Fetch H2H, Spreads, and Totals for the entire week
url = f"https://api.the-odds-api.com/v4/sports/rugbyleague_nrl/odds/?apiKey={API_KEY}&regions=au&markets=h2h,spreads,totals"
response = requests.get(url)

if response.status_code != 200:
    print(f"API Error: {response.text}")
    exit(1)

games = response.json()
if not games:
    print("No upcoming NRL matches found for this week.")
    exit(0)

def send_telegram_message(text):
    telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    requests.post(telegram_url, json=payload)

# Header
send_telegram_message("🗓️ *NRL WEEKLY ROUND - 3-LEG SGM OPTIONS* 🏉")

# Process every match in the upcoming round
for game in games:
    home = game.get("home_team")
    away = game.get("away_team")
    bookmakers = game.get("bookmakers", [])
    
    if not bookmakers:
        continue
        
    bm = bookmakers[0]
    bm_name = bm.get("title", "Sportsbet")
    markets = {m["key"]: m["outcomes"] for m in bm.get("markets", [])}
    
    h2h_outcomes = markets.get("h2h", [])
    spread_outcomes = markets.get("spreads", [])
    totals_outcomes = markets.get("totals", [])
    
    if not (h2h_outcomes and spread_outcomes and totals_outcomes):
        continue
        
    # Favorite vs Underdog selection
    fav = min(h2h_outcomes, key=lambda x: x["price"])
    
    # 3-Leg Multi Options
    leg1 = f"Leg 1: {fav['name']} H2H (@ ${fav['price']})"
    
    leg2_outcome = spread_outcomes[0]
    leg2 = f"Leg 2: {leg2_outcome['name']} {leg2_outcome.get('point', '')} Line (@ ${leg2_outcome['price']})"
    
    leg3_outcome = totals_outcomes[0]
    leg3 = f"Leg 3: Total Points {leg3_outcome['name']} {leg3_outcome.get('point', '')} (@ ${leg3_outcome['price']})"
    
    match_msg = (
        f"🔥 *{home} vs {away}* ({bm_name})\n"
        f"  ├ 1️⃣ {leg1}\n"
        f"  ├ 2️⃣ {leg2}\n"
        f"  └ 3️⃣ {leg3}\n"
        f"  🎯 *Build SGM on Sportsbet/TAB*"
    )
    
    send_telegram_message(match_msg)
