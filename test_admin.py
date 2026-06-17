"""
Simple test script
"""
import os
print("Current dir:", os.getcwd())
print("DB exists:", os.path.exists("shop.db"))

# Test imports
from admin.api import app, STATIC_DIR
print("Static dir:", STATIC_DIR)
print("Static dir exists:", os.path.exists(STATIC_DIR))
print("Index exists:", os.path.exists(os.path.join(STATIC_DIR, "index.html")))
print("Style exists:", os.path.exists(os.path.join(STATIC_DIR, "style.css")))
print("App.js exists:", os.path.exists(os.path.join(STATIC_DIR, "app.js")))

print("\nFlask routes:")
for rule in app.url_map.iter_rules():
    if rule.rule == '/':
        print("  ROOT:", rule.rule, "->", rule.endpoint)
    elif 'api' in rule.rule:
        print("  API:", rule.rule)

# Test database
import database as db
print("\nDatabase check:")
users = db.get_all_users()
print("  Users:", len(users))
products = db.get_all_products()
print("  Products:", len(products))
