import jwt
import time
import uuid
import requests
import json
from pathlib import Path

# --- CONFIGURATION ---
# UPDATE THIS with your Non-Production Client ID from Epic
CLIENT_ID = "7defd2fb-f768-4196-8e1a-bebae4975b68" 
TOKEN_URL = "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token"
PRIVATE_KEY_PATH = Path("epic_private_key.pem")
JWKS_PATH = Path("jwks.json")
# ---------------------

def get_access_token() -> str:
    # 1. Load Private Key
    with open(PRIVATE_KEY_PATH, "r") as f:
        private_key = f.read()

    # 2. Load JWKS to dynamically get the correct 'kid'
    with open(JWKS_PATH, "r") as f:
        jwks_data = json.load(f)
        kid = jwks_data["keys"][0]["kid"]

    # 3. Create JWT Payload
    now = int(time.time())
    payload = {
        "iss": CLIENT_ID,
        "sub": CLIENT_ID,
        "aud": TOKEN_URL,
        "jti": str(uuid.uuid4()),
        "exp": now + 300  # 5 minutes
    }

    # 4. Sign JWT
    client_assertion = jwt.encode(
        payload,
        private_key,
        algorithm="RS384",
        headers={"kid": kid, "typ": "JWT"}
    )

    # 5. Exchange for Access Token
    data = {
        "grant_type": "client_credentials",
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion": client_assertion,
        "scope": "system/Patient.read system/Encounter.read system/DocumentReference.write"
    }

    print(f"🔑 Using Client ID: {CLIENT_ID}")
    print(f"🏷️  Using Key ID (kid): {kid}")
    
    response = requests.post(TOKEN_URL, data=data)
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        # Save to file for other scripts
        with open("epic_token.txt", "w") as f:
            f.write(token)
        print("✅ Token successfully retrieved and saved to epic_token.txt")
        return token
    else:
        print(f"❌ Failed to get token. Status: {response.status_code}")
        print(f"Response: {response.text}")
        response.raise_for_status()