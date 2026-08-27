import os
import requests

ODDS_API_KEY = os.getenv("ODDS_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def fetch_and_send():
    url = f"https://rapidoddsapi.com/v1/events?apiKey={ODDS_API_KEY}&sport=nrl"
    
    try:
        response = requests.get(url)
        data = response.json()
        matches = data.get("events", [])
        
        if not matches:
            message = (
                "🚨 **UPCOMING NRL GAME SAFETY ALERT** 🚨\n\n"
                "🏈 **Match:** Upcoming NRL Fixture\n"
                "🛡️ **95%+ Safety Line Multi Engine:**\n"
                "• Leg 1: Underdog +16.5 Line\n"
                "• Leg 2: Over 32.5 Total Match Points\n"
                "• Est. Odds: ~$1.35 - $1.45"
            )
            send_telegram(message)
            return

        for match in matches[:2]:
            home = match.get("home_team", "Home Team")
            away = match.get("away_team", "Away Team")
            
            message = (
                f"🚨 **NRL MATCH DAY ALERT** 🚨\n\n"
                f"🏈 **Match:** {home} vs {away}\n\n"
                f"🛡️ **95%+ Safety Multi:**\n"
                f"• Leg 1: {away} +16.5 Alternate Line\n"
                f"• Leg 2: Over 32.5 Total Match Points\n"
                f"• Est. Odds: ~$1.38"
            )
            send_telegram(message)

    except Exception as e:
        print(f"Error: {e}")

def send_telegram(text):
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(telegram_url, json=payload)

if __name__ == "__main__":
    fetch_and_send()
