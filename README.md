# 🎧 BPO AI Quality Assurance & Compliance Engine

An end-to-end, automated Speech-to-Text and Compliance Auditing engine built for enterprise contact centers. This system replaces manual, low-coverage call sampling (typically 2-5% of total volume) with 100% automated call auditing, sentiment analysis, deterministic compliance scoring, and Human-in-the-Loop (HITL) supervisor workflows.

---

## 📌 Executive Summary & Business ROI

* **100% Audit Coverage:** Eliminates manual QA sampling bottlenecks by transcribing and auditing every customer interaction in real-time.
* **Deterministic Risk Flagging:** Enforces mandatory brand greetings, verification checkpoints, and SLA compliance metrics while minimizing false positives.
* **Human-in-the-Loop (HITL):** Provides supervisory review overrides and feedback loops for calls flagged below operational thresholds.
* **Cost & Latency Efficiency:** Utilizes ultra-fast open-weight LLM inference via Groq to reduce audit latency from hours to seconds per call.

---

## 🏗️ Architecture & Pipeline Flow

```text
       [ Customer Call Audio (.mp3/.wav) ]
                       │
                       ▼
         [ Streamlit Web Dashboard ]
                       │
               (HTTP POST / Multipart)
                       │
                       ▼
       [ FastAPI Gateway (backend/main.py) ]
          ├─ Extension Validation & Temp Ingestion
          ├─ Speech-to-Text (`whisper-large-v3`)
          ├─ Contextual Prompting & Phonetic Handling
          │
          ▼
   [ QA Audit Engine (openai/gpt-oss-120b) ]
          ├─ Pydantic Strict JSON Schema Extraction
          ├─ Protocol Adherence & Sentiment Tagging
          ├─ Agent Professionalism Scoring (1-10)
          │
          ▼
   [ Persistence Layer (SQLite + SQLAlchemy) ]
          ├─ Call Records, Scores & Observations
          │
          ▼
   [ Human-in-the-Loop (HITL) Supervisor Tab ]
          └─ Status Override, Feedback & Coaching Notes