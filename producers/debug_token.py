import os
from dotenv import load_dotenv
import requests

load_dotenv()

client_id = os.getenv('SENTINEL_CLIENT_ID')
client_secret = os.getenv('SENTINEL_CLIENT_SECRET')

print("OAuth2 Token Debug")
print("-" * 60)
print(f"Client ID: {client_id}")
print(f"Client Secret: {client_secret[:10]}***" if client_secret else "None")
print()

if not client_id or not client_secret:
    print("❌ ERROR: Missing credentials in .env")
    exit(1)

# Direct POST request - részletekért
print("Sending POST request to token endpoint...")
print()

response = requests.post(
    'https://services.sentinel-hub.com/auth/realms/main/protocol/openid-connect/token',
    headers={
        'Content-Type': 'application/x-www-form-urlencoded'
    },
    data={
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    }
)

print(f"Status Code: {response.status_code}")
print(f"Response Headers: {dict(response.headers)}")
print()
print("Response Body:")
print(response.text)
