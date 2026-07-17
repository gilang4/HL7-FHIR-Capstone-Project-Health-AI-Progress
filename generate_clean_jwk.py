import json
import base64
import uuid
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

def int_to_base64url(num):
    length = (num.bit_length() + 7) // 8
    b = num.to_bytes(length, byteorder='big')
    return base64.urlsafe_b64encode(b).rstrip(b'=').decode('ascii')

print("🔐 Generating CLEAN, space-free, single JWK for Epic...")
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

# Save Private Key
pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)
with open("epic_private_key.pem", "wb") as f:
    f.write(pem)

pub_numbers = private_key.public_key().public_numbers()
kid = str(uuid.uuid4())

# THIS IS THE SINGLE JWK OBJECT EPIC EXPECTS (No "keys" array wrapper!)
single_jwk = {
    "kty": "RSA",
    "alg": "RS384",
    "kid": kid,
    "n": int_to_base64url(pub_numbers.n),
    "e": int_to_base64url(pub_numbers.e)
}

# Save locally so Python can read it directly
with open("jwks.json", "w") as f:
    json.dump(single_jwk, f, indent=2)

print("\n✅ CLEAN SINGLE JWK GENERATED!")
print("⚠️  COPY EVERYTHING BETWEEN THE LINES BELOW.")
print("⚠️  NOTE: This is the SINGLE object, NOT the {'keys': [...]} wrapper!")
print("="*70)
print(json.dumps(single_jwk, indent=2))
print("="*70)
print(f"\n💡 New KEY ID (kid) is: {kid}")