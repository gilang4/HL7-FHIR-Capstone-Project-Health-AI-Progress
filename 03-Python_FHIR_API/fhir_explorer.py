import requests
import json

BASE_URL = "https://r4.smarthealthit.org"

# ── 1. GET PATIENT ──────────────────────────────────────
patient = requests.get(
    f"{BASE_URL}/Patient",
    params={"_count": 1},
    headers={"Accept": "application/fhir+json"}
).json()

# Parse out the first patient
p = patient["entry"][0]["resource"]
patient_id = p["id"]
patient_name = p["name"][0]["text"] if "text" in p["name"][0] else "Unknown"
patient_dob = p.get("birthDate", "Unknown")

print(f"👤 Patient: {patient_name} | DOB: {patient_dob} | ID: {patient_id}")

# ── 2. GET CONDITIONS ────────────────────────────────────
conditions = requests.get(
    f"{BASE_URL}/Condition",
    params={"patient": patient_id, "_count": 10},
    headers={"Accept": "application/fhir+json"}
).json()

print("\n🏥 Conditions:")
for entry in conditions.get("entry", []):
    code = entry["resource"]["code"]["text"]
    print(f"  - {code}")

# ── 3. GET MEDICATIONS ───────────────────────────────────
meds = requests.get(
    f"{BASE_URL}/MedicationRequest",
    params={"patient": patient_id, "_count": 5},
    headers={"Accept": "application/fhir+json"}
).json()

print("\n💊 Medications:")
for entry in meds.get("entry", []):
    med = entry["resource"]["medicationCodeableConcept"]["text"]
    print(f"  - {med}")