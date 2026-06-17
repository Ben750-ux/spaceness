from admin.api import app
client = app.test_client()

# Check conversations
resp = client.get('/api/conversations/shops')
data = resp.get_json()
print('=== Conversations Boutiques ===')
for c in data:
    print(f"- {c['shop_name']}: {c['message_count']} messages, non lus admin: {c['unread_admin']}")

# Get messages for shop 1
resp = client.get('/api/conversations/shops/1')
msgs = resp.get_json()
print('\n=== Messages Boutique Tech ===')
for m in msgs:
    print(f"[{m['id']}] {m['subject']} - {m['message'][:50]}")
