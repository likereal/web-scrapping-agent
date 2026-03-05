import sqlite3
import requests

from core.config import DB_PATH, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    response = requests.post(url, data=payload)

    if response.status_code != 200:
        raise Exception(f"Telegram send failed: {response.text}")


def process_notifications():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT e.event_id,
               e.platform,
               e.product_id,
               e.event_type,
               e.new_price,
               c.name,
               c.search_url
        FROM product_events e
        JOIN current_products c
          ON e.product_id = c.product_id
        WHERE e.notified = 0
    """)

    events = cur.fetchall()

    for event in events:
        event_id, platform, product_id, event_type, new_price, name, url = event

        if event_type == "NEW_PRODUCT":
            message = f"""
🆕 *New Product Detected*

*{name}*
Price: ₹{new_price}

[View on Blinkit]({url})
"""

        elif event_type == "PRICE_OR_STOCK_CHANGE":
            message = f"""
🔄 *Product Updated*

*{name}*
New Price: ₹{new_price}

[View on Blinkit]({url})
"""

        else:
            continue

        try:
            send_telegram_message(message)

            cur.execute("""
                UPDATE product_events
                SET notified = 1
                WHERE event_id = ?
            """, (event_id,))

            conn.commit()

        except Exception as e:
            print("Notification failed:", e)

    conn.close()


if __name__ == "__main__":
    process_notifications()
