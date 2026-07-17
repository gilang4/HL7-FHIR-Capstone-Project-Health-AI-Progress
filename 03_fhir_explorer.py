import requests
import json
from datetime import datetime

BASE_URL = "https://r4.smarthealthit.org"

    # ── 1. GET PATIENT ──────────────────────────────────────
patient = requests.get(
    f"{BASE_URL}/Patient",
    params={"_count": 1},
    headers={"Accept": "application/fhir+json"}
).json()

        # Parse out the first patient
        # digs through this wrapper (["entry"][0]["resource"]) to get to the actual patient data

"""
                To understand why the code has to dig through ["entry"][0]["resource"], it helps to look at exactly what the server hands back to your Python script.
            
                When you ask a FHIR server for data (even if you just ask for 1 patient), the server doesn't just hand you the raw patient data. Instead, FHIR server puts the data inside a digital "envelope" called a Bundle.

                        ##### the json sturcture #####

                                                    {
                            "resourceType": "Bundle",     <-- The Envelope
                            "total": 1,                   <-- Tells you how many items are inside
                            "entry": [                    <-- The List of Items inside the envelope
                                {
                                "fullUrl": "...",         <-- A web link to the patient
                                "resource": {             <-- THE ACTUAL PATIENT DATA IS HERE
                                    "resourceType": "Patient",
                                    "id": "12345",
                                    "name": [{"text": "John Doe"}],
                                    "birthDate": "1980-01-01"
                                }
                                }
                            ]
                            }
                        ##### the json sturcture #####

                patient["entry"] : Opens the envelope and looks at the list of items

                ["entry"][0] : Because you asked for only 1 patient (_count: 1), there is only one item in the list. [0] tells Python to grab the very first item in that list.

                ["entry"][0]["resource"] : Digs into that first item and pulls out the "resource", which is the actual Patient data (name, ID, birthdate).

                If you hadn't used ["resource"], your code would just be looking at the wrapper, and it wouldn't be able to find the patient's name or ID!

                your code had to take the patient_id it just extracted, and go knock on the doors of the /Condition and /MedicationRequest endpoints to get the rest of their medical story.

"""
p = patient["entry"][0]["resource"]
patient_id = p["id"]
"""
                    In Python, this specific structure is called a ternary operator. It is just a shorthand way of writing an if/else statement on a single line.

                    This line is a safety check (error handling) to prevent your code from crashing if the server sends back incomplete data

                            ##### the json sturcture #####
                                "name": [
                                    {
                                        "use": "official",
                                        "family": "Doe",
                                        "given": ["John", "Robert"],
                                        "text": "John Robert Doe"   <--- THIS IS THE "text" FIELD
                                    }
                                    ]

                            ##### the json sturcture #####

                    Python reads that line of code from left to right:

                        p["name"] : Grabs the whole list of names.
                        
                        p["name"][0] : Grabs the very first name in that list (the dictionary containing "family", "given", "text", etc.).

                        if "text" in p["name"][0] : This is the safety check. It asks, "Does this first name dictionary actually contain a key called 'text'?"
                        Note: In FHIR, the "text" field is optional. Sometimes a server only provides the "family" (last name) and "given" (first name) but forgets to combine them into a "text" field.
                        
                        p["name"][0]["text"] : If the answer to the safety check is YES, it grabs the actual readable name (e.g., "John Robert Doe").
                        else "Unknown" : If the answer to the safety check is NO (meaning the "text" key is missing), it assigns the word "Unknown" to the variable so the script doesn't crash with a KeyError.                      
"""
patient_name = p["name"][0]["text"] if "text" in p["name"][0] else "Unknown"
        # if the birthdate is missing, it prints "Unknown" instead of crashing the script.
patient_dob = p.get("birthDate", "Unknown")

print(f"👤 Patient: {patient_name} | DOB: {patient_dob} | ID: {patient_id}")

    # ── 2. GET CONDITIONS ────────────────────────────────────
conditions = requests.get(
    f"{BASE_URL}/Condition",
    params={"patient": patient_id, "_count": 10},
    headers={"Accept": "application/fhir+json"}
).json()

    # empty list initialize
condition_list = []

"""
        In the FHIR JSON specification, the list of actual results is always stored in an array field named "entry"

        .get("code", {}) looks for this field. If it is missing (which can happen in incomplete records), it safely returns an empty dictionary {} so the next step doesn't fail.

        .get("text", "Unknown")
        A FHIR CodeableConcept (the code dictionary) usually contains two ways of describing the illness:

        coding: A highly structured list of official medical codes (like ICD-10 or SNOMED-CT codes, e.g., ["code": "U07.1", "system": "[http://hl7.org/fhir/sid/icd-10-cm](http://hl7.org/fhir/sid/icd-10-cm)"]).

        text: A plain, human-readable description of the condition as entered by the clinician (e.g., "COVID-19" or "Acute bronchitis")

        .get("text", "Unknown"), your code is skipping the complex computer codes and grabbing the clean, plain-text description of the illness. If the record somehow has a code but no plain-text description, it defaults to "Unknown"
"""
for entry in conditions.get("entry", []):
    code = entry["resource"].get("code", {}).get("text", "Unknown")
    condition_list.append(code)

print(f"🏥 Conditions: {condition_list}")

"""
                            ##### the json sturcture #####

                                                                                {
                                                "resourceType": "Bundle",
                                                "entry": [                          <-- THIS IS THE LIST THE LOOP WILL READ
                                                    {
                                                    "resource": {                   <-- Condition #1
                                                        "resourceType": "Condition",
                                                        "code": {
                                                        "text": "Asthma"            <-- THE DATA WE WANT
                                                        }
                                                    }
                                                    },
                                                    {
                                                    "resource": {                   <-- Condition #2
                                                        "resourceType": "Condition",
                                                        "code": {
                                                        "text": "Hypertension"      <-- THE DATA WE WANT
                                                        }
                                                    }
                                                    }
                                                ]
                                                }

                    conditions is a Python dictionary (the whole JSON envelope).
                    .get("entry", []) is a Python command that says: "Look for the key named 'entry'. If it exists, give me the list inside it. If it doesn't exist, give me an empty list []."


                            ##### the json sturcture #####

"""
    ### careful here....
for entry in conditions.get("entry", []):
    code = entry["resource"]["code"]["text"]
    print(f"  - {code}")

    # ── 3. GET MEDICATIONS ───────────────────────────────────
meds = requests.get(
    f"{BASE_URL}/MedicationRequest",
    params={"patient": patient_id, "_count": 10},
    headers={"Accept": "application/fhir+json"}
).json()
med_list = []
for entry in meds.get("entry", []):
    med = entry["resource"].get("medicationCodeableConcept", {}).get("text", "Unknown")
    med_list.append(med)

print(f"💊 Medications: {med_list}")

# ── 4. GET OBSERVATIONS (LABS + VITALS) ────────────────
def get_observations(patient_id, category):
    """Fetch Observations by category: 'laboratory' or 'vital-signs'"""
    obs = requests.get(
        f"{BASE_URL}/Observation",
        params={"patient": patient_id, "category": category, "_count": 20},
        headers={"Accept": "application/fhir+json"}
    ).json()
    
    """
        valueQuantity	Numeric measurement with a unit.	Used for measurable, continuous results. (e.g., Blood pressure, Glucose levels, Heart rate, Weight).	{"value": 120, "unit": "mmHg", "system": "http://unitsofmeasure.org", "code": "mm[Hg]"}	"120 mmHg"

        valueCodeableConcept	A coded, categorical, or ordinal choice.	Used for qualitative results. (e.g., "Positive/Negative", "Normal/Abnormal", "Present/Absent", or specific diagnosis codes).	{"text": "Negative", "coding": [{"system": "http://snomed.info/sct", "code": "260385009", "display": "Negative"}]}	"Negative"

        valueString	Free-form, unstructured text.	Used for narrative comments or descriptions that don't fit a code. (e.g., Pathologist's microscopic description, or "Specimen hemolyzed, results may be inaccurate").	"Squamous epithelial cells present in moderate numbers."
    """   
    results = []
    for entry in obs.get("entry", []):
        resource = entry["resource"]
        code = resource.get("code", {}).get("text", "Unknown")
            # Get value (could be Quantity, CodeableConcept, or just text)
        value = "Unknown"
        if "valueQuantity" in resource:
            value = f"{resource['valueQuantity']['value']} {resource['valueQuantity'].get('unit', '')}"
        elif "valueCodeableConcept" in resource:
            value = resource["valueCodeableConcept"].get("text", "Unknown")
        elif "valueString" in resource:
            value = resource["valueString"]
        
        # Get date if available
        date = resource.get("effectiveDateTime", "Unknown")
        
        results.append({
            "code": code,
            "value": value,
            "date": date
        })
    return results

labs = get_observations(patient_id, "laboratory")
vitals = get_observations(patient_id, "vital-signs")

print(f"🧪 Labs: {len(labs)} entries")
print(f"❤️ Vitals: {len(vitals)} entries")

# ── 5. GET ENCOUNTERS ──────────────────────────────────
encounters = requests.get(
        f"{BASE_URL}/Encounter",
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

print(f"🏨 Encounters: {len(encounter_list)} visits")



    ############################


    # ── 6. SAVE TO JSON ──────────────────────────────────────
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

with open("patient_summary.json", "w") as f:
    json.dump(output, f, indent=2)

print("\n✅ Saved expanded patient data to patient_summary.json")