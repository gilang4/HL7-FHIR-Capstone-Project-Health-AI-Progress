
import json
import re
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate


def load_patient_data(filepath="patient_summary.json"):
    """Reads the FHIR JSON file that 03_ created."""
    with open(filepath, "r") as f:
        return json.load(f)

def generate_summary(patient_data: dict) -> dict:
    """
    Sends patient JSON fields to Llama3.2 and returns a structured JSON summary.
    Returns: dict with keys: patient_id, summary, conditions, medications, labs, vitals, encounters
    """
    
    llm = OllamaLLM(model="llama3.2", temperature=0)
    ######################################################################################333
    # --- THE UPGRADED PROMPT ---
    
    # ── Format the new sections ──
    def format_obs_list(obs_list, label):
        if not obs_list:
            return "None recorded"
        lines = []
        for item in obs_list:
            date = item.get("date", "Unknown")
            lines.append(f"  - {item['code']}: {item['value']} (date: {date})")
        return "\n".join(lines)

    labs_text = format_obs_list(patient_data.get("labs", []), "Labs")
    vitals_text = format_obs_list(patient_data.get("vitals", []), "Vitals")
    
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
    prompt = PromptTemplate(
        input_variables=["patient_id", "age", "conditions", "medications", "labs", "vitals", "encounters"],
        template=template
    )
    
    chain = prompt | llm
    result = chain.invoke({
        "patient_id": patient_id,
        "age": age,
        "conditions": conditions_text,
        "medications": medications_text,
        "labs": labs_text,
        "vitals": vitals_text,
        "encounters": encounters_text
    })
    
    # ── Parse JSON ──
    try:
        clean = result.strip()
        if clean.startswith("```json"):
            clean = clean.replace("```json", "").replace("```", "").strip()
        elif clean.startswith("```"):
            clean = clean.replace("```", "").strip()
        summary_json = json.loads(clean)
        print("✅ Ollama JSON parsed")
        return summary_json
    except json.JSONDecodeError as e:
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

def save_summary_output(summary_json: dict, filepath="summary_output_Ollama.json"):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(summary_json, f, indent=2)
    print(f"✅ Saved summary to {filepath}")

if __name__ == "__main__":
    data = load_patient_data()
    result = generate_summary(data)
    print("\n📋 Clinical Summary:")
    print("=" * 50)
    print(result.get("summary", "No summary generated"))
    print("=" * 50)
    save_summary_output(result)
    print("\n✅ Pipeline complete!")