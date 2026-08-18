# tools/azure_summarizer.py
"""
Azure OpenAI Clinical Summarizer Tool — Send patient data to Azure GPT and get a structured JSON summary.
Refactored from 05_azure_summarizer.py for Agentic AI integration.

Usage:
    from tools.azure_summarizer import summarize_with_azure
    
    # With a dict (from fhir_explorer or loaded JSON)
    result = summarize_with_azure(patient_data)
    print(result["summary"])
    
    # Or from a JSON file
    result = summarize_with_azure(json.load(open("patient_summary.json")))
"""

import json
import os
from dotenv import load_dotenv
from openai import AzureOpenAI


# ── Load Azure credentials ONCE when module is imported ─────
# This avoids re-reading .env on every function call
load_dotenv()

# Read Azure configuration from environment variables
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")

# Create the Azure OpenAI client once (reused across calls)
_client = None

def _get_client() -> AzureOpenAI:
    """
    Lazily create the Azure OpenAI client.
    Only connects when first needed, then reuses the connection.
    """
    global _client
    if _client is None:
        _client = AzureOpenAI(
            azure_endpoint=AZURE_ENDPOINT,
            api_key=AZURE_KEY,
            api_version=AZURE_API_VERSION
        )
    return _client


def summarize_with_azure(
    patient_data: dict,
    model: str | None = None,
    temperature: float = 1.0,
    save_to_file: str | None = "summary_output_AzureGPT.json"
) -> dict:
    """
    Send patient FHIR data to Azure OpenAI (GPT) and return a structured clinical summary.
    
    Args:
        patient_data: Dict with keys: patient, conditions, medications, labs, vitals, encounters
                      (Exactly what fhir_explorer.explore_patient() returns)
        model: Azure deployment name. If None, uses AZURE_OPENAI_DEPLOYMENT from .env
        temperature: LLM temperature (default: 1.0)
        save_to_file: If provided, saves JSON to this filename.
                       Use None to skip file save.
    
    Returns:
        dict with keys: patient_id, summary, conditions, medications, labs, vitals, encounters
    
    Example:
        from tools.fhir_explorer import explore_patient
        from tools.azure_summarizer import summarize_with_azure
        
        data = explore_patient()
        result = summarize_with_azure(data)
        print(result["summary"])
    """
    
    # Use deployment from .env if not explicitly provided
    deployment = model or AZURE_DEPLOYMENT
    
    # ── Format Helper: Turns observation lists into readable text ──
    def format_obs_list(obs_list):
        """
        Converts a list of observation dicts into newline-separated text.
        Each observation has: code, value, date
        Example output:
          "  - Hemoglobin: 14.2 g/dL (date: 2024-01-15)
             - Blood Pressure: 120/80 mmHg (date: 2024-01-15)"
        """
        if not obs_list:
            return "None recorded"
        return "\n".join([
            f"  - {item['code']}: {item['value']} (date: {item.get('date', 'Unknown')})"
            for item in obs_list
        ])
    
    # ── Format all input sections from patient_data ────────
    labs_text = format_obs_list(patient_data.get("labs", []))
    vitals_text = format_obs_list(patient_data.get("vitals", []))
    
    enc_list = patient_data.get("encounters", [])
    encounters_text = "None recorded"
    if enc_list:
        encounters_text = "\n".join([
            f"  - Visit {e['id']}: {e['class']} on {e['start']} (status: {e['status']})"
            for e in enc_list
        ])
    
    patient = patient_data.get("patient", {})
    patient_id = patient.get("id", "unknown")
    age = patient.get("dob", "Unknown")
    conditions_text = "\n".join([f"- {c}" for c in patient_data.get("conditions", ["None"])])
    medications_text = "\n".join([f"- {m}" for m in patient_data.get("medications", ["None"])])

    # ── THE PROMPT ─────────────────────────────────────────
    # This tells Azure GPT exactly what to do and how to format the output
    prompt = f"""You are a clinical summarization assistant for a healthcare integration test.

You are given synthetic patient data from a FHIR server. Your task is to generate a structured JSON summary.

## INPUT DATA:
Patient ID: {patient_id}
DOB: {age}
Conditions:
{conditions_text}
Medications:
{medications_text}
Laboratory Results:
{labs_text}
Vital Signs:
{vitals_text}
Encounters:
{encounters_text}

## INSTRUCTIONS:
1. Generate a 4-6 sentence clinical summary that is professional and factual.
2. Mention any notable trends in labs/vitals if they exist.
3. Do NOT infer, diagnose, or add any information not explicitly provided.
4. Return ONLY valid JSON in the format shown below.

## OUTPUT FORMAT:
{{
  "patient_id": "{patient_id}",
  "summary": "...",
  "conditions": [...],
  "medications": [...],
  "labs": [...],
  "vitals": [...],
  "encounters": [...]
}}
Make sure the lists match the input exactly.

## RULES:
- The summary should be written in plain English.
- The conditions and medications lists must be **exactly** as provided in the input.
- Do not add, remove, or modify any condition or medication names.
- Ensure the output is valid JSON (no trailing commas, quotes properly escaped).
- Return ONLY the JSON object. Do not include any other text or commentary.

## OUTPUT:
"""
    
    # ── Call Azure GPT ─────────────────────────────────────
    client = _get_client()
    
    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": "You are a clinical assistant. Always return valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=temperature
    )
    result = response.choices[0].message.content
    
    # ── Parse the JSON response ────────────────────────────
    # GPT sometimes wraps JSON in ```json ... ``` fences — we clean that
    try:
        clean = result.strip()
        if clean.startswith("```json"):
            clean = clean.replace("```json", "").replace("```", "").strip()
        elif clean.startswith("```"):
            clean = clean.replace("```", "").strip()
        summary_json = json.loads(clean)
        print("✅ Successfully parsed JSON response from Azure GPT")
    
    except json.JSONDecodeError as e:
        # Fallback: return raw text if JSON parsing fails
        print(f"⚠️ Azure JSON error: {e}")
        summary_json = {
            "patient_id": patient_id,
            "summary": result.strip(),
            "conditions": patient_data.get("conditions", []),
            "medications": patient_data.get("medications", []),
            "labs": patient_data.get("labs", []),
            "vitals": patient_data.get("vitals", []),
            "encounters": patient_data.get("encounters", [])
        }
    
    # ── Optional: Save to file ─────────────────────────────
    if save_to_file:
        with open(save_to_file, "w", encoding="utf-8") as f:
            json.dump(summary_json, f, indent=2)
        print(f"✅ Saved to {save_to_file}")
    
    return summary_json


# ── Run standalone (for backward compatibility) ─────────────
# You can still run this file directly, just like the old script!
if __name__ == "__main__":
    # Load patient data from the JSON file created by 03_fhir_explorer.py
    data = json.load(open("patient_summary.json", "r"))
    
    # Generate summary
    result = summarize_with_azure(data)
    
    # Display results
    print("\n📋 Clinical Summary (Azure GPT):")
    print("=" * 50)
    print(result.get("summary", "No summary generated"))
    print("=" * 50)
    print(f"\n📊 Conditions: {len(result.get('conditions', []))} items")
    print(f"💊 Medications: {len(result.get('medications', []))} items")
    print(f"🧪 Labs: {len(result.get('labs', []))} entries")
    print(f"❤️ Vitals: {len(result.get('vitals', []))} entries")
    print(f"🏨 Encounters: {len(result.get('encounters', []))} visits")
    
    print("\n✅ Azure Pipeline complete!")