import sys
import os
import sqlite3

# Add src to python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from core.config import DB_PATH

def query_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("SELECT name, price, inventory FROM current_products LIMIT 5")
    rows = cur.fetchall()
    
    print("\n--- Current Products Sample ---")
    for row in rows:
        print(f"Name: {row[0]} | Price: {row[1]} | Stock: {row[2]}")
    
    conn.close()

if __name__ == "__main__":
    query_db()
