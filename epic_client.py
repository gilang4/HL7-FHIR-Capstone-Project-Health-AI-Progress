import time
import jwt
import requests

# ============================================
# CONFIGURATION — UPDATE THESE 3 LINES
# ============================================
CLIENT_ID = "2c64db89-3d78-46a2-b4c3-381e414bd7d9"          # From Epic portal
PRIVATE_KEY_PATH = "private_key.pem"       # Your private key file
TOKEN_URL = "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token"
# ============================================

def get_access_token():
    """Get an access token from Epic using JWT client assertion."""
    
    # Read your private key
    with open(PRIVATE_KEY_PATH, "r") as f:
        private_key = f.read()

    # Build the JWT payload
    now = int(time.time())
    payload = {
        "iss": "2c64db89-3d78-46a2-b4c3-381e414bd7d9",
        "sub": "2c64db89-3d78-46a2-b4c3-381e414bd7d9",
        "aud": TOKEN_URL,
        "jti": str(now),
        "exp": now + 300  # 5 minutes
    }

    # Sign the JWT — make sure the 'kid' matches your JWKS!
    signed_jwt = jwt.encode(
        payload,
        private_key,
        algorithm="RS384",
        headers={"kid": "72ad3b61-b0b2-4a60-acf9-6f7aec2e24db"}  # <-- CHANGE THIS TO YOUR KID!
    )
    
    # Debug: print the JWT so you can check it at jwt.io
    print("🔑 JWT:", signed_jwt)

    # Request the access token
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion": signed_jwt,
        "scope": "system/Patient.read system/Condition.read"
    }

    response = requests.post(TOKEN_URL, data=data, headers=headers)
    response.raise_for_status()
    return response.json()["access_token"]

# ============================================
# RUN THE SCRIPT
# ============================================
if __name__ == "__main__":
    try:
        token = get_access_token()
        print(f"✅ Token received! First 20 chars: {token[:20]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
