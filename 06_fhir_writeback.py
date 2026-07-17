

import requests
import base64
import json
import argparse
from datetime import datetime, timezone

FHIR_BASE_URL = "https://r4.smarthealthit.org"


def write_document_reference(patient_data: dict, summary: str) -> str:
        
    """
    POSTs the AI summary as a FHIR DocumentReference resource.
    Returns the FHIR ID of the created resource.
    """
    
    summary_b64 = base64.b64encode(summary.encode("utf-8")).decode("utf-8")
    patient_id = patient_data.get("patient_id", "unknown")
    doc_ref = {
        "resourceType": "DocumentReference",
        "status": "current",
        "type": {
            "coding": [{
                "system": "http://loinc.org",
                "code": "34133-9",
                "display": "Summarization of Episode Note"
            }]
        },
        "subject": {
            "reference": f"Patient/{patient_id}"
        },
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "description": "AI-generated clinical summary (synthetic test data)",
        "content": [{
            "attachment": {
                "contentType": "text/plain",
                "language": "en-US",
                "data": summary_b64,
                "title": "AI Clinical Summary_SlowPo"
            }
        }]
    }
    
    response = requests.post(
        f"{FHIR_BASE_URL}/DocumentReference",
        headers={"Content-Type": "application/fhir+json"},
        json=doc_ref
    )
    response.raise_for_status()
    doc_id = response.json().get("id", "unknown")
    print(f"FHIR write-back success — DocumentReference ID: {doc_id}")
    # return doc_id

# --- STEP 2: GET (Verify) ---
    print(f"🔍 Verifying resource {doc_id}...")
    verify_response = requests.get(
        f"{FHIR_BASE_URL}/DocumentReference/{doc_id}",
        headers={"Accept": "application/fhir+json"}
    )

    if verify_response.status_code == 200:
        print("✅ Verification successful! Resource is safely stored and readable.")
        # Optional: print or save the full resource
        # print(verify_response.json())
    else:
        print(f"⚠️ Verification failed: Could not read resource. Status: {verify_response.status_code}")

    return doc_id




def load_summary_file(filepath: str) -> tuple[dict, str]:
    
    """
    Reads a JSON file produced by the LLM summarization step.
    Expected shape: {"patient_id": "...", "summary": "..."}
    Returns (patient_data, summary) ready to hand to write_document_reference.
    """

    with open(filepath, "r", encoding="utf-8") as f:
        record = json.load(f)

    if "patient_id" not in record or "summary" not in record:
        raise ValueError(
            f"{filepath} is missing required fields 'patient_id' and/or 'summary'. "
            f"Got keys: {list(record.keys())}"
        )

    patient_data = {"patient_id": record["patient_id"]}
    summary = record["summary"]
    return patient_data, summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Push an LLM-generated summary file to FHIR as a DocumentReference."
    )
    parser.add_argument(
        "summary_file",
        help="Path to the JSON file written by the summarization step "
             "(must contain 'patient_id' and 'summary')."
    )
    args = parser.parse_args()

    patient_data, summary = load_summary_file(args.summary_file)
    write_document_reference(patient_data, summary)


"""
With the DocumentReference ID: XXXXXXXX

Opern browser and run this code:

https://r4.smarthealthit.org/DocumentReference/XXXXXXXX

https://r4.smarthealthit.org/DocumentReference/4759042

"""