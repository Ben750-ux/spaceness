from admin.api import app
client = app.test_client()
resp = client.get('/api/shops')
shops = resp.get_json()
print('=== Shops ===')
for s in shops:
    print(f"{s['shop_name']}: owner={s.get('owner_name', 'N/A')}, email={s.get('owner_email', 'N/A')}")
