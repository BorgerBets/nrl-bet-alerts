import os
import requests

API_KEY = os.getenv("ODDS_API_KEY")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 1. Fetch H2H Odds from The Odds API
url = f"https://api.the-odds-api.com/v4/sports/rugbyleague_nrl/odds/?apiKey={API_KEY}&regions=au&markets=h2h"
response = requests.get(url)

if response.status_code != 200:
    print(f"API Error: {response.text}")
    exit(1)

games = response.json()
if not games:
    print("No upcoming NRL matches found.")
    exit(0)

# 2. Format output message
message_lines = ["🏉 *NRL Upcoming Match Odds* 🏉\n"]

for game in games[:5]:  # Formats the next 5 upcoming matches
    home_team = game.get("home_team")
    away_team = game.get("away_team")
    
    # Extract bookmaker odds (uses first available AU bookmaker)
    bookmakers = game.get("bookmakers", [])
    odds_str = "Odds currently unavailable"
    
    if bookmakers:
        bm_name = bookmakers[0].get("title")
        markets = bookmakers[0].get("markets", [])
        if markets:
            outcomes = markets[0].get("outcomes", [])
            odds_list = [f"{o['name']}: {o['price']}" for o in outcomes]
            odds_str = f"({bm_name}) " + " | ".join(odds_list)
            
    message_lines.append(f"• *{home_team} vs {away_team}*\n  └ {odds_str}\n")

message_text = "\n".join(message_lines)

# 3. Send formatted message to Telegram
telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
payload = {
    "chat_id": CHAT_ID,
    "text": message_text,
    "parse_mode": "Markdown"
}
requests.post(telegram_url, json=payload)
