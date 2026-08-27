import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from google import genai

# Environment Variables from GitHub Secrets
API_KEY = os.getenv("ODDS_API_KEY")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not all([API_KEY, BOT_TOKEN, CHAT_ID, GEMINI_API_KEY]):
    print("Error: Missing one or more required environment variables.")
    exit(1)

# Initialize Gemini Client
ai_client = genai.Client(api_key=GEMINI_API_KEY)

# HTTP Session Configuration
session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retries))

def send_telegram_message(text, parse_mode="HTML"):
    telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": parse_mode}
    try:
        res = session.post(telegram_url, json=payload, timeout=10)
        res.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to send Telegram message: {e}")
        if res is not None:
            print(f"Telegram response: {res.text}")

# Fetch Odds Data
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

# Send Header using simple HTML
send_telegram_message("🤖 <b>NRL WEEKLY ROUND - GEMINI AI 3-LEG SGM ANALYSIS</b> 🏉")

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

    match_context = f"""
    Match: {home_team} vs {away_team} ({bm_name})
    Head-to-Head Odds: {[{'team': o['name'], 'price': o['price']} for o in h2h]}
    Spreads/Lines: {[{'outcome': o['name'], 'point': o.get('point'), 'price': o['price']} for o in spreads]}
    Total Points Lines: {[{'type': o['name'], 'point': o.get('point'), 'price': o['price']} for o in totals]}
    """

    prompt = f"""
    You are an NRL sports betting analyst.
    Analyze the following match fixture and available odds:
    {match_context}

    Select 3 logical, correlated legs for a 3-leg Same Game Multi (SGM).
    
    Format the response strictly in plain text / basic HTML like this:
    🔥 <b>{home_team} vs {away_team}</b> ({bm_name})
      ├ 1️⃣ Leg 1: [Selection & Odds]
      ├ 2️⃣ Leg 2: [Selection & Odds]
      └ 3️⃣ Leg 3: [Selection & Odds]
      💡 <b>AI Rationale:</b> [1-2 concise sentences explaining the tactical logic]
    """

    try:
        ai_response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        print(f"Generated analysis for {home_team} vs {away_team}")
        send_telegram_message(ai_response.text, parse_mode="HTML")
    except Exception as e:
        print(f"Gemini generation failed for {home_team} vs {away_team}: {e}")
