from admin.api import app
client = app.test_client()

print('=== Test envoi message admin ===')
resp = client.post('/api/shops/1/message', json={
    'subject': 'Reponse administration',
    'message': 'Bonjour boutique, nous avons recu votre message'
})
print('Send:', resp.get_json())

print('\n=== Verifier les messages ===')
resp = client.get('/api/conversations/shops/1')
msgs = resp.get_json()
for m in msgs:
    print(f'  [{m["id"]}] from_vendor={m["is_from_vendor"]}, reply={m["admin_reply"]}')

print('\n=== Test reponse a un message ===')
# Reply to message id 6
resp = client.post('/api/vendor-messages/6/reply', json={
    'reply': 'Merci pour votre retour!'
})
print('Reply:', resp.get_json())

# Check again
resp = client.get('/api/conversations/shops/1')
msgs = resp.get_json()
for m in msgs:
    print(f'  [{m["id"]}] from_vendor={m["is_from_vendor"]}, reply={m["admin_reply"]}')

print('\n=== Test vendor voit les messages ===')
from admin import vendor_api
vendor_client = vendor_api.app.test_client()
vendor_client.post('/vendor_api/login', json={
    'email': 'tech@shop.local',
    'password': 'vendor123'
})
resp = vendor_client.get('/vendor_api/messages')
msgs = resp.get_json()
print('Vendor messages:')
for m in msgs:
    print(f'  [{m["id"]}] subject={m["subject"]}, reply={m["admin_reply"]}')
