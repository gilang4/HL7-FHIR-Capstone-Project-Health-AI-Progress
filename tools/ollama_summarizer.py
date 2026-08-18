# tools/ollama_summarizer.py
"""
Ollama Clinical Summarizer Tool — Send patient data to Llama 3.2 and get a structured JSON summary.
Refactored from 05_ai_summarizer.py for Agentic AI integration.

Usage:
    from tools.ollama_summarizer import summarize_patient
    
    # With a dict (from fhir_explorer or loaded JSON)
    result = summarize_patient(patient_data)
    print(result["summary"])
    
    # Or from a JSON file
    result = summarize_patient(json.load(open("patient_summary.json")))
"""

import json
import re
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate


def summarize_patient(
    patient_data: dict,
    model: str = "llama3.2",
    temperature: int = 0,
    base_url: str = "http://127.0.0.1:11434",
    save_to_file: str | None = "summary_output_Ollama.json"
) -> dict:
    """
    Send patient FHIR data to Ollama (Llama 3.2) and return a structured clinical summary.
    
    Args:
        patient_data: Dict with keys: patient, conditions, medications, labs, vitals, encounters
                      (Exactly what fhir_explorer.explore_patient() returns)
        model: Ollama model name (default: "llama3.2")
        temperature: LLM temperature, 0 = deterministic (default: 0)
        base_url: Ollama server URL (default: "http://127.0.0.1:11434")
        save_to_file: If provided, saves JSON to this filename.
                       Use None to skip file save.
    
    Returns:
        dict with keys: patient_id, summary, conditions, medications, labs, vitals, encounters
    
    Example:
        from tools.fhir_explorer import explore_patient
        from tools.ollama_summarizer import summarize_patient
        
        data = explore_patient()
        result = summarize_patient(data)
        print(result["summary"])
    """
    
    # ── Initialize Ollama LLM ─────────────────────────────
    # NOTE: base_url must be explicit on Windows to avoid connection hangs
    llm = OllamaLLM(model=model, temperature=temperature, base_url=base_url)
    
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
        lines = []
        for item in obs_list:
            date = item.get("date", "Unknown")
            lines.append(f"  - {item['code']}: {item['value']} (date: {date})")
        return "\n".join(lines)

    # ── Format all input sections from patient_data ────────
    labs_text = format_obs_list(patient_data.get("labs", []))
    vitals_text = format_obs_list(patient_data.get("vitals", []))
    
    encounters_text = "None recorded"
    enc_list = patient_data.get("encounters", [])
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

    # ── THE PROMPT TEMPLATE ────────────────────────────────
    # This tells Llama 3.2 exactly what to do and how to format the output
    template = """You are a clinical summarization assistant.

You are given synthetic patient data from a FHIR server. Generate a structured JSON summary.

## INPUT DATA:
Patient ID: {patient_id}
DOB: {age}
Conditions:
{conditions}
Medications:
{medications}

Laboratory Results:
{labs}

Vital Signs:
{vitals}

Encounters (visits):
{encounters}

## INSTRUCTIONS:
1. Write a 4-6 sentence clinical summary that is professional and factual.
2. Include relevant trends from labs/vitals if present (e.g., "Blood pressure was elevated on 2 of 3 visits").
3. Do NOT infer new diagnoses — stick to the data.
4. Return ONLY valid JSON in this format:
{{
  "patient_id": "{patient_id}",
  "summary": "Your summary here...",
  "conditions": [...],
  "medications": [...],
  "labs": [...],
  "vitals": [...],
  "encounters": [...]
}}
Make sure the last three lists match the input exactly.

## OUTPUT:
"""
    
    # ── Build the LangChain pipeline ───────────────────────
    prompt = PromptTemplate(
        input_variables=["patient_id", "age", "conditions", "medications", "labs", "vitals", "encounters"],
        template=template
    )
    
    chain = prompt | llm
    
    # ── Invoke the LLM ─────────────────────────────────────
    result = chain.invoke({
        "patient_id": patient_id,
        "age": age,
        "conditions": conditions_text,
        "medications": medications_text,
        "labs": labs_text,
        "vitals": vitals_text,
        "encounters": encounters_text
    })
    
    # ── Parse the JSON response ────────────────────────────
    # LLMs sometimes wrap JSON in ```json ... ``` fences — we clean that
    try:
        clean = result.strip()
        if clean.startswith("```json"):
            clean = clean.replace("```json", "").replace("```", "").strip()
        elif clean.startswith("```"):
            clean = clean.replace("```", "").strip()
        summary_json = json.loads(clean)
        print("✅ Ollama JSON parsed successfully")
        return summary_json
    
    except json.JSONDecodeError as e:
        # Fallback: return raw text if JSON parsing fails
        print(f"⚠️ JSON parse error: {e}")
        return {
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
        print(f"✅ Saved summary to {save_to_file}")
    
    return summary_json


# ── Run standalone (for backward compatibility) ─────────────
# You can still run this file directly, just like the old script!
if __name__ == "__main__":
    # Load patient data from the JSON file created by 03_fhir_explorer.py
    data = json.load(open("patient_summary.json", "r"))
    
    # Generate summary
    result = summarize_patient(data)
    
    # Display results
    print("\n📋 Clinical Summary (Ollama - Llama 3.2):")
    print("=" * 50)
    print(result.get("summary", "No summary generated"))
    print("=" * 50)
    print(f"\n📊 Conditions: {len(result.get('conditions', []))} items")
    print(f"💊 Medications: {len(result.get('medications', []))} items")
    print(f"🧪 Labs: {len(result.get('labs', []))} entries")
    print(f"❤️ Vitals: {len(result.get('vitals', []))} entries")
    print(f"🏨 Encounters: {len(result.get('encounters', []))} visits")
    print("\n✅ Pipeline complete!")