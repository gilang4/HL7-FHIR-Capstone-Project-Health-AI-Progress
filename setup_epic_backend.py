import json
import base64
import uuid
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

def int_to_base64url(num):
    length = (num.bit_length() + 7) // 8
    b = num.to_bytes(length, byteorder='big')
    return base64.urlsafe_b64encode(b).rstrip(b'=').decode('ascii')

print("🔐 Generating clean, space-free RSA Key Pair...")

# 1. Generate Private Key
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

# 2. Save Private Key (Keep this secret!)
pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)
with open("epic_private_key.pem", "wb") as f:
    f.write(pem)
print("✅ Private key saved to 'epic_private_key.pem'")

# 3. Generate Public JWK
pub_numbers = private_key.public_key().public_numbers()
kid = str(uuid.uuid4())

jwk = {
    "kty": "RSA",
    "alg": "RS384",
    "kid": kid,
    "n": int_to_base64url(pub_numbers.n),
    "e": int_to_base64url(pub_numbers.e)
}

jwks = {"keys": [jwk]}

# 4. Save clean JWKS (No trailing spaces!)
with open("jwks.json", "w") as f:
    json.dump(jwks, f, indent=2)

print("\n✅ CLEAN JWKS GENERATED!")
print("Copy EVERYTHING between the lines below and paste it into Epic:")
print("="*60)
print(json.dumps(jwks, indent=2))
print("="*60)
print(f"\n💡 IMPORTANT: Your new KEY ID (kid) is: {kid}")