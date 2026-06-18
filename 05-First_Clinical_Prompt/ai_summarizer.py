import json
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
#from langchain.prompts import PromptTemplate

# ── 1. LOAD YOUR PATIENT DATA ────────────────────────────
with open("patient_summary.json", "r") as f:
    patient = json.load(f)

# ── 2. BUILD THE CLINICAL PROMPT ─────────────────────────
template = """
You are a clinical documentation assistant.

Given the following patient data, write a 3-sentence structured 
summary covering:
- Primary diagnosis
- Current medications
- Key comorbidities

Be concise and clinical in tone.

Patient Date of Birth: {dob}
Conditions: {conditions}
Medications: {medications}

Clinical Summary:
"""

prompt = PromptTemplate(
    input_variables=["dob", "conditions", "medications"],
    template=template
)

# ── 3. CONNECT TO OLLAMA AND RUN ─────────────────────────
llm = OllamaLLM(model="llama3.2")
chain = prompt | llm

summary = chain.invoke({
    "dob": patient["patient"]["dob"],
    "conditions": ", ".join(patient["conditions"]),
    "medications": ", ".join(patient["medications"])
})

print("\n📋 Clinical Summary:")
print(summary)