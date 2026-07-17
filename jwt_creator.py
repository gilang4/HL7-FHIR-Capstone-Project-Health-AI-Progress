# jwt_creator.py
import time
import uuid
import jwt
from pathlib import Path

# --- Configuration ---
# IMPORTANT: Set these to your actual values
CLIENT_ID = "7defd2fb-f768-4196-8e1a-bebae4975b68"
TOKEN_URL = "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token"
# This MUST match the 'kid' in your JWKS!
KEY_ID = "20c4ea2b-fa69-4a15-84db-93c623e39315"
PRIVATE_KEY_PATH = Path("epic_private_key.pem") # Path to your private key file
# -------------------

def create_signed_jwt() -> str:
    """
    Creates a JWT signed with your private key.
    Returns the encoded JWT as a string.
    """
    # 1. Load the private key
    with open(PRIVATE_KEY_PATH, "r") as key_file:
        private_key = key_file.read()

    # 2. Create the payload (the body of the token)
    now = int(time.time())
    payload = {
        "iss": CLIENT_ID,
        "sub": CLIENT_ID,
        "aud": TOKEN_URL,
        "jti": str(uuid.uuid4()), # Unique ID for the token
        "exp": now + 300          # Token expires in 5 minutes
    }

    # 3. Create the header with the 'kid'
    headers = {"kid": KEY_ID} # <-- This is the crucial part!

    # 4. Encode and sign the JWT
    # The algorithm MUST be RS384 for Epic's backend services flow[reference:8]
    signed_jwt = jwt.encode(
        payload, 
        private_key, 
        algorithm="RS384", 
        headers=headers
    )

    
    print(f"🔑 Client ID: {CLIENT_ID}")
    print(f"🏷️  Key ID: {KEY_ID}")
    print(f"🌐 Audience (aud): {TOKEN_URL}")
    print(f"📝 Full JWT: {signed_jwt}")  # <--- ADD THIS
    return signed_jwt


    return signed_jwt