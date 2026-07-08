# 🏥 HL7 FHIR CAPSTONE PROJECT — HEALTHCARE DATA INTEGRATION & AI PIPELINE

This project demonstrates my ability to work with healthcare data standards (HL7 FHIR) and apply engineering skills to real-world healthcare problems. It shows I can build integrations, work with APIs, handle sensitive healthcare data, and leverage AI for clinical summarization.

HL7 FHIR is the global standard for exchanging healthcare data. It enables hospitals, clinics, and health systems to share patient data securely. This project demonstrates how to query FHIR APIs, structure healthcare data, and prepare it for analysis—skills critical for building modern healthcare technology.

---

## 📋 Table of Contents

- [✨ Features](#-features)
- [📅 Timeline](#-timeline)
- [🛠️ Tech Stack](#️-tech-stack)
- [📂 Project Structure](#-project-structure)
- [🔮 Future Work](#-future-work)
- [📜 License](#-license)
- [👨‍💻 Credits](#-credits)

---

## ✨ Features

- ✅ Set up FHIR sandbox server environment for healthcare data testing and exploration
- ✅ Connected to publicly available FHIR test servers to query real-world healthcare data (e.g., HAPI, Synthea)
- ✅ Ingested and parsed FHIR resources (Patient, Condition, Observation, MedicationRequest)
- ✅ Learned and applied FHIR resource structures, data types, and search parameters
- ✅ Created data preprocessing pipeline to normalize and structure FHIR data for analysis
- ✅ Implemented data queries to extract meaningful insights from healthcare datasets
- ✅ Documented FHIR API integration patterns and best practices
- ✅ Built repeatable code modules for fetching and parsing FHIR resources
- ✅ Gained hands-on experience with healthcare interoperability standards
- ✅ Demonstrated understanding of FHIR profiles and extensions
- ✅ Integrated AI (Ollama Llama3.2 + Azure GPT-5-mini) for clinical summarization
- ✅ Implemented FHIR DocumentReference writeback to EHR
- ✅ Automated email delivery of clinical summaries via Gmail API OAuth 2.0
- ✅ Implemented OAuth 2.0 + JWT + JWKS for Epic FHIR sandbox authentication

---

## 📅 Timeline

| Phase | Status | Description |
| :--- | :--- | :--- |
| Phase 1 | ✅ Completed – May 2026 | Project Planning & FHIR Fundamentals |
| Phase 2 | ✅ Completed – June 2026 | FHIR Server Connection & Data Ingestion |
| Phase 3 | ✅ Completed – June 2026 | Data Preprocessing & Structuring |
| Phase 4 | ✅ Completed – June 2026 | API Integration & Query Optimization |
| Phase 5 | ✅ Completed – July 2026 | AI Integration & EHR Writeback |
| Phase 6 | 🔄 In Progress – July 2026 | Documentation & Portfolio Presentation |

---

## 🛠️ Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **FHIR** | HL7 FHIR R4, HAPI FHIR Server, Epic FHIR Sandbox (OAuth 2.0 + JWT) |
| **AI/LLM** | LangChain, Ollama (Llama 3.2), Azure AI Foundry (GPT-5-mini) |
| **Authentication** | OAuth 2.0, JWT, JWKS, SMART on FHIR, Gmail API OAuth 2.0 |
| **Data Formats** | JSON, XML (legacy) |
| **Language** | Python 3.13 |
| **Libraries** | Requests, Pandas, NumPy, fhirclient, PyJWT, cryptography |
| **Cloud** | Azure AI Foundry, Azure OpenAI |
| **Version Control** | Git, GitHub |
| **Environment** | Visual Studio Code |
| **Future** | FastAPI, Docker, Microsoft Healthcare Agent Orchestrator |

---

## 📂 Project Structure

hl7-fhir-capstone/
├── 01_fhir_explorer.py          # Basic FHIR queries
├── 02_fhir_explorer.py          # Search patients
├── 03_fhir_explorer.py          # Full patient, conditions, medications
├── ai_summarizer.py             # Ollama (local) summarization
├── 05_azure_summarizer.py       # Azure GPT-5-mini summarization
├── 06_fhir_writeback.py         # POST DocumentReference to FHIR
├── patient_summary.json         # Output from FHIR pull
├── summary_output.json          # Structured JSON from LLM
├── credentials.json             # OAuth 2.0 client credentials
├── token.json                   # OAuth 2.0 access token
├── private_key.pem              # RSA private key (never commit!)
├── public_key.pem               # RSA public key
└── README.md                    # This file

---

## 🔮 Future Work
. FastAPI Wrapper — Deploy the pipeline as a REST API

. Docker Containerization — One-click deployment

. Microsoft Healthcare Agent Orchestrator — Register as a reusable healthcare AI agent and working with agents

. DeepSeek V3.2 Support — Add another parallel LLM option as option for client on cost-affective

. Real-time Dashboard — Monitor pipeline health and performance

. Multi-patient Batch Processing — Scale to thousands of patients

---

## 📜 License
This project is licensed under the MIT License — see the LICENSE file for details.

---

## 👨‍💻 Credits
Built with guidance from Clown Buddy (the best AI tutor). 😉

Built with ❤️ as part of the Microsoft AI/ML Engineering certification journey.

---