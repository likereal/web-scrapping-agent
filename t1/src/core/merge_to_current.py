import sqlite3
from core.config import DB_PATH


def merge_to_current():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Get latest record per product
    cur.execute("""
        SELECT lp.*
        FROM landing_products lp
        INNER JOIN (
            SELECT product_id, MAX(extracted_at) AS max_time
            FROM landing_products
            GROUP BY product_id
        ) latest
        ON lp.product_id = latest.product_id
        AND lp.extracted_at = latest.max_time
    """)

    rows = cur.fetchall()

    for row in rows:
        (
            platform,
            product_id,
            merchant_id,
            name,
            brand,
            price,
            mrp,
            inventory,
            is_sold_out,
            deep_link,
            search_url,
            extracted_at
        ) = row

        cur.execute("""
            SELECT price, inventory
            FROM current_products
            WHERE platform=? AND product_id=?
        """, (platform, product_id))

        existing = cur.fetchone()

        if not existing:
            # NEW PRODUCT
            cur.execute("""
                INSERT INTO current_products
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                platform,
                product_id,
                merchant_id,
                name,
                brand,
                price,
                mrp,
                inventory,
                is_sold_out,
                deep_link,
                search_url,
                extracted_at,
                extracted_at
            ))

            cur.execute("""
                INSERT INTO product_events
                (platform, product_id, event_type, event_timestamp)
                VALUES (?, ?, 'NEW_PRODUCT', ?)
            """, (platform, product_id, extracted_at))

        else:
            old_price, old_inventory = existing

            if price != old_price or inventory != old_inventory:

                cur.execute("""
                    UPDATE current_products
                    SET price=?, inventory=?, last_updated_at=?
                    WHERE platform=? AND product_id=?
                """, (
                    price,
                    inventory,
                    extracted_at,
                    platform,
                    product_id
                ))

                cur.execute("""
                    INSERT INTO product_events
                    (platform, product_id, event_type,
                     old_price, new_price,
                     old_inventory, new_inventory,
                     event_timestamp)
                    VALUES (?, ?, 'PRICE_OR_STOCK_CHANGE',
                            ?, ?, ?, ?, ?)
                """, (
                    platform,
                    product_id,
                    old_price,
                    price,
                    old_inventory,
                    inventory,
                    extracted_at
                ))

    conn.commit()
    conn.close()

    print("Merge complete.")
