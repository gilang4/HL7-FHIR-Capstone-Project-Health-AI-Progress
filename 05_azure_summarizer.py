import json
from openai import AzureOpenAI

import os
from dotenv import load_dotenv


    # ============================================================
    # 🔑 CONFIGURATION
    # ============================================================

    # Load secrets from .env file
load_dotenv()

# Now read them as environment variables
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_key = os.getenv("AZURE_OPENAI_KEY")
DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT")

    # ============================================================
    # 🔌 CREATE CLIENT
    # ============================================================

    # Use them in your code
client = AzureOpenAI(
    azure_endpoint=endpoint,
    api_key=api_key,
    api_version="2024-10-21"
)


    # ============================================================
    # 📂 LOAD PATIENT DATA
    # ============================================================
def load_patient_data(filepath="patient_summary.json"):
    with open(filepath, "r") as f:
        return json.load(f)

    # ============================================================
    # 🤖 GENERATE SUMMARY WITH AZURE
    # ============================================================
def generate_summary_with_azure(patient_data: dict) -> dict:
    # Prepare the data
    patient = patient_data.get("patient", {})
    patient_id = patient.get("id", "unknown")
    age = patient.get("dob", "Unknown")
    
    conditions_text = "\n".join([f"- {c}" for c in patient_data.get("conditions", ["None recorded"])])
    medications_text = "\n".join([f"- {m}" for m in patient_data.get("medications", ["None recorded"])])
    
    prompt = f"""You are a clinical summarization assistant for a healthcare integration test.

You are given synthetic patient data from a FHIR server. Your task is to generate a structured JSON summary.

## INPUT DATA:
Patient ID: {patient_id}
Age (Year of Birth): {age}
Conditions:
{conditions_text}
Medications:
{medications_text}

## INSTRUCTIONS:
1. Generate a 3-5 sentence clinical summary that is professional and factual.
2. Do NOT infer, diagnose, or add any information not explicitly provided.
3. Return ONLY valid JSON in the format shown below.

## OUTPUT FORMAT:
{{
  "patient_id": "{patient_id}",
  "summary": "Your clinical summary text here...",
  "conditions": ["List", "of", "conditions", "exactly", "as", "provided"],
  "medications": ["List", "of", "medications", "exactly", "as", "provided"]
}}

## RULES:
- The summary should be written in plain English.
- The conditions and medications lists must be **exactly** as provided in the input.
- Do not add, remove, or modify any condition or medication names.
- Ensure the output is valid JSON (no trailing commas, quotes properly escaped).
- Return ONLY the JSON object. Do not include any other text or commentary.

## OUTPUT:
"""
    
    # --- Call Azure GPT-5-mini ---
    response = client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=[
            {"role": "system", "content": "You are a clinical assistant. Always return valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=1  # Deterministic output
    )
    
    result = response.choices[0].message.content
    
    # --- Parse JSON Response ---
    try:
        clean_result = result.strip()
        if clean_result.startswith("```json"):
            clean_result = clean_result.replace("```json", "").replace("```", "").strip()
        elif clean_result.startswith("```"):
            clean_result = clean_result.replace("```", "").strip()
        
        summary_json = json.loads(clean_result)
        print("✅ Successfully parsed JSON response from Azure GPT-5-mini")
        return summary_json
        
    except json.JSONDecodeError as e:
        print(f"⚠️ Failed to parse JSON: {e}")
        return {
            "patient_id": patient_id,
            "summary": result.strip(),
            "conditions": patient_data.get("conditions", []),
            "medications": patient_data.get("medications", [])
        }

    # ============================================================
    # 💾 SAVE OUTPUT
    # ============================================================
def save_summary_output(summary_json: dict, filepath="summary_output.json"):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(summary_json, f, indent=2)
    print(f"✅ Saved to {filepath}")

    # ============================================================
    # 🚀 MAIN
    # ============================================================
if __name__ == "__main__":
    data = load_patient_data()
    result = generate_summary_with_azure(data)
    
    print("\n📋 Clinical Summary (Azure):")
    print("=" * 50)
    print(result.get("summary", "No summary generated"))
    print("=" * 50)
    print(f"\n📊 Conditions: {len(result.get('conditions', []))} items")
    print(f"💊 Medications: {len(result.get('medications', []))} items")
    
    save_summary_output(result)
    print("\n✅ Azure Pipeline complete!")