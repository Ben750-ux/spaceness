import sqlite3
conn = sqlite3.connect('shop.db')
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print('Tables:', tables)

# Check vendor_admin_messages structure
try:
    cursor = conn.execute("PRAGMA table_info(vendor_admin_messages)")
    cols = [row[1] for row in cursor.fetchall()]
    print('vendor_admin_messages columns:', cols)
except:
    print('Table vendor_admin_messages not found')

conn.close()
