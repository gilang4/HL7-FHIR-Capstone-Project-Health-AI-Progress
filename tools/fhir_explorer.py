# tools/fhir_explorer.py
"""
FHIR Explorer Tool — Fetch patient data from a FHIR server.
Refactored from 03_fhir_explorer.py for Agentic AI integration.

Usage:
    from tools.fhir_explorer import explore_patient
    data = explore_patient(base_url="https://r4.smarthealthit.org")
"""

import requests
import json
import os
from datetime import datetime


def get_observations(patient_id: str, category: str, base_url: str) -> list:
    """Fetch Observations by category: 'laboratory' or 'vital-signs'"""
    obs = requests.get(
        f"{base_url}/Observation",
        params={"patient": patient_id, "category": category, "_count": 20},
        headers={"Accept": "application/fhir+json"}
    ).json()

    results = []
    for entry in obs.get("entry", []):
        resource = entry["resource"]
        code = resource.get("code", {}).get("text", "Unknown")
        
        value = "Unknown"
        if "valueQuantity" in resource:
            value = f"{resource['valueQuantity']['value']} {resource['valueQuantity'].get('unit', '')}"
        elif "valueCodeableConcept" in resource:
            value = resource["valueCodeableConcept"].get("text", "Unknown")
        elif "valueString" in resource:
            value = resource["valueString"]
        
        date = resource.get("effectiveDateTime", "Unknown")
        
        results.append({
            "code": code,
            "value": value,
            "date": date
        })
    return results


def explore_patient(
    base_url: str = "https://r4.smarthealthit.org",
    save_to_file: str | None = "patient_summary.json"
) -> dict:
    """
    Fetch a random patient from a FHIR server and return their complete data.
    
    Args:
        base_url: FHIR server base URL (default: SMART Health IT sandbox)
        save_to_file: If provided, saves JSON to this filename. 
                       Use None to skip file save.
    
    Returns:
        dict with keys: patient, conditions, medications, labs, vitals, encounters
    
    Example:
        data = explore_patient()
        print(data["patient"]["name"])
    """
    
    # ── 1. GET PATIENT ──────────────────────────────────────
    patient = requests.get(
        f"{base_url}/Patient",
        params={"_count": 1},
        headers={"Accept": "application/fhir+json"}
    ).json()

    p = patient["entry"][0]["resource"]
    patient_id = p["id"]
    patient_name = p["name"][0]["text"] if "text" in p["name"][0] else "Unknown"
    patient_dob = p.get("birthDate", "Unknown")

    # ── 2. GET CONDITIONS ────────────────────────────────────
    conditions = requests.get(
        f"{base_url}/Condition",
        params={"patient": patient_id, "_count": 10},
        headers={"Accept": "application/fhir+json"}
    ).json()
    
    condition_list = []
    for entry in conditions.get("entry", []):
        code = entry["resource"].get("code", {}).get("text", "Unknown")
        condition_list.append(code)

    # ── 3. GET MEDICATIONS ───────────────────────────────────
    meds = requests.get(
        f"{base_url}/MedicationRequest",
        params={"patient": patient_id, "_count": 10},
        headers={"Accept": "application/fhir+json"}
    ).json()
    
    med_list = []
    for entry in meds.get("entry", []):
        med = entry["resource"].get("medicationCodeableConcept", {}).get("text", "Unknown")
        med_list.append(med)

    # ── 4. GET OBSERVATIONS (LABS + VITALS) ──────────────────
    labs = get_observations(patient_id, "laboratory", base_url)
    vitals = get_observations(patient_id, "vital-signs", base_url)

    # ── 5. GET ENCOUNTERS ──────────────────────────────────
    encounters = requests.get(
        f"{base_url}/Encounter",
        params={"patient": patient_id, "_count": 10},
        headers={"Accept": "application/fhir+json"}
    ).json()
    
    encounter_list = []
    for entry in encounters.get("entry", []):
        res = entry["resource"]
        enc_id = res.get("id", "Unknown")
        status = res.get("status", "Unknown")
        cls = res.get("class", {}).get("code", "Unknown")
        period = res.get("period", {})
        start = period.get("start", "Unknown")
        encounter_list.append({
            "id": enc_id,
            "status": status,
            "class": cls,
            "start": start
        })

    # ── 6. ASSEMBLE OUTPUT ──────────────────────────────────
    output = {
        "patient": {
            "id": patient_id,
            "name": patient_name,
            "dob": patient_dob
        },
        "conditions": condition_list,
        "medications": med_list,
        "labs": labs,
        "vitals": vitals,
        "encounters": encounter_list
    }

    # ── 7. OPTIONAL FILE SAVE ────────────────────────────────
    if save_to_file:
        with open(save_to_file, "w") as f:
            json.dump(output, f, indent=2)

    return output


# ── Run standalone (for backward compatibility) ─────────────
if __name__ == "__main__":
    data = explore_patient()
    print(f"👤 Patient: {data['patient']['name']} | DOB: {data['patient']['dob']} | ID: {data['patient']['id']}")
    print(f"🏥 Conditions: {data['conditions']}")
    print(f"💊 Medications: {data['medications']}")
    print(f"🧪 Labs: {len(data['labs'])} entries")
    print(f"❤️ Vitals: {len(data['vitals'])} entries")
    print(f"🏨 Encounters: {len(data['encounters'])} visits")
    print(f"\n✅ Saved to patient_summary.json")