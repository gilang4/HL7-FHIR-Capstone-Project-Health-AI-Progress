


import json
import re
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate

def load_patient_data(filepath="patient_summary.json"):
    """Reads the FHIR JSON file that Project 1 created."""
    with open(filepath, "r") as f:
        return json.load(f)

def generate_summary(patient_data: dict) -> dict:
    """
    Sends patient JSON fields to Llama3.2 and returns a structured JSON summary.
    Returns: dict with keys: patient_id, summary, conditions, medications
    """
    
    llm = OllamaLLM(model="llama3.2", temperature=0)
    
    # --- THE UPGRADED PROMPT ---
    template = """You are a clinical summarization assistant for a healthcare integration test.

You are given synthetic patient data from a FHIR server. Your task is to generate a structured JSON summary.

## INPUT DATA:
Patient ID: {patient_id}
Age (Year of Birth): {age}
Conditions:
{conditions}
Medications:
{medications}

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

    prompt = PromptTemplate(
        input_variables=["patient_id", "age", "conditions", "medications"],
        template=template
    )
    
    chain = prompt | llm
    
    # --- Prepare Input Data ---
    patient = patient_data.get("patient", {})
    patient_id = patient.get("id", "unknown")
    age = patient.get("dob", "Unknown")
    
    conditions_text = "\n".join([f"- {c}" for c in patient_data.get("conditions", ["None recorded"])])
    medications_text = "\n".join([f"- {m}" for m in patient_data.get("medications", ["None recorded"])])
    
    # --- Run the LLM ---
    result = chain.invoke({
        "patient_id": patient_id,
        "age": age,
        "conditions": conditions_text,
        "medications": medications_text
    })
    
    # --- Parse the JSON Response ---
    try:
        # Clean the response (remove markdown code blocks if present)
        clean_result = result.strip()
        if clean_result.startswith("```json"):
            clean_result = clean_result.replace("```json", "").replace("```", "").strip()
        elif clean_result.startswith("```"):
            clean_result = clean_result.replace("```", "").strip()
        
        # Parse JSON
        summary_json = json.loads(clean_result)
        print("✅ Successfully parsed JSON response from Ollama")
        return summary_json
        
    except json.JSONDecodeError as e:
        print(f"⚠️ Failed to parse JSON response: {e}")
        print(f"Raw response: {result[:200]}...")
        
        # Fallback: Build a minimal JSON structure
        return {
            "patient_id": patient_id,
            "summary": result.strip(),
            "conditions": patient_data.get("conditions", []),
            "medications": patient_data.get("medications", [])
        }

def save_summary_output(summary_json: dict, filepath="summary_output.json"):
    """Saves the structured JSON summary to a file."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(summary_json, f, indent=2)
    print(f"✅ Saved structured summary to {filepath}")

if __name__ == "__main__":
    # --- Load data from Project 1 ---
    data = load_patient_data()
    
    # --- Generate structured JSON summary ---
    result = generate_summary(data)
    
    # --- Print the summary ---
    print("\n📋 Clinical Summary:")
    print("=" * 50)
    print(result.get("summary", "No summary generated"))
    print("=" * 50)
    print(f"\n📊 Conditions: {len(result.get('conditions', []))} items")
    print(f"💊 Medications: {len(result.get('medications', []))} items")
    
    # --- Save the JSON output for FHIR writeback ---
    save_summary_output(result)
    
    print("\n✅ Pipeline complete!")
    print("📄 Next step: Run fhir_writeback.py summary_output.json")