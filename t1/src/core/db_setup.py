import sqlite3

from core.config import DB_PATH

def create_tables(drop_first=False):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    if drop_first:
        cur.execute("DROP TABLE IF EXISTS landing_products;")
        cur.execute("DROP TABLE IF EXISTS current_products;")
        cur.execute("DROP TABLE IF EXISTS product_events;")
    # Landing (append-only)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS landing_products (
        platform TEXT,
        product_id TEXT,
        merchant_id TEXT,
        name TEXT,
        brand TEXT,
        price REAL,
        mrp REAL,
        inventory INTEGER,
        is_sold_out BOOLEAN,
        deep_link TEXT,
        search_url TEXT,
        extracted_at TEXT
    )
    """)

    # Current state
    cur.execute("""
    CREATE TABLE IF NOT EXISTS current_products (
        platform TEXT,
        product_id TEXT,
        merchant_id TEXT,
        name TEXT,
        brand TEXT,
        price REAL,
        mrp REAL,
        inventory INTEGER,
        is_sold_out BOOLEAN,
        deep_link TEXT,
        search_url TEXT,
        first_seen_at TEXT,
        last_updated_at TEXT,
        PRIMARY KEY (platform, product_id)
    )
    """)

    # Event table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS product_events (
        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform TEXT,
        product_id TEXT,
        event_type TEXT,
        old_price REAL,
        new_price REAL,
        old_inventory INTEGER,
        new_inventory INTEGER,
        event_timestamp TEXT,
        notified INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_tables()
    print("Tables created.")
