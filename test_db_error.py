import sqlite3
from datetime import datetime

DB_NAME = "shop.db"

def send_message_to_shop(shop_id: int, subject: str, message: str) -> bool:
    """Envoie un message de l'admin à une boutique"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        conn.execute(
            """
            INSERT INTO vendor_admin_messages (shop_id, vendor_user_id, subject, message, created_at, is_from_vendor, is_read)
            VALUES (?, 0, ?, ?, ?, 0, 0)
            """,
            (shop_id, subject, message, datetime.utcnow().isoformat())
        )
        conn.commit()
        print("Success!")
        return True
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

result = send_message_to_shop(1, 'Test', 'Message test')
print('Result:', result)
