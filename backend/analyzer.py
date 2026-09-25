from fastapi import responses
import json
import os
from groq import Groq
from dotenv import load_dotenv

try:
    from backend.schemas import QAComplianceAudit
except ImportError:
    from schemas import QAComplianceAudit

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY .env file me missing hai!")

client = Groq(api_key=api_key)

def analyze_call_transcript(transcript: str, call_id: str) -> QAComplianceAudit:
    """
    Transcript ko evaluate karta hai against BPO Quality metrics
    aur validated Pydantic schema return karta hai.
    """

    system_prompt = """
    You are an expert BPO Quality Assurance (QA) Compliance Auditor.
    Evaluate the provided customer service call transcript thoroughly against these strict rules:
    
    1. Greeting Protocol: Did the agent greet with brand identity politely?
    2. Verification & Information Capture: Did the agent capture necessary contact/delivery details?
    3. Professionalism: Rate agent tone, patience, and clarity (Scale 1 to 10).
    4. Issue Resolution: Identify the customer's request and the resolution provided.
    5. Overall Compliance Score: Calculate percentage (0.0 to 100.0) based on process adherence.
    
    CRITICAL: Output must be purely raw valid JSON strictly matching these keys:
    {
      "customer_sentiment": "Positive" | "Neutral" | "Negative",
      "primary_issue": string,
      "agent_professionalism_score": int (1-10),
      "mandatory_greeting_done": bool,
      "solution_provided": string,
      "compliance_score_percentage": float (0-100),
      "audit_notes": [list of strings detailing positive points or violations]
    }
    Do not include markdown blocks or any conversational text.
    """

    responses = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Call Transcript to Audit:\n{transcript}"}
        ],
        response_format={"type": "json_object"},
        temperature =0.1
    )

    raw_response = responses.choices[0].message.content
    audit_dict = json.loads(raw_response)

    # Injection of system fields
    audit_dict["call_id"] = call_id

    # Deterministic Rule: Human-in-the-loop fallback trigger
    # Agar compliance 75% se kam ho, toh code forcefully human review flag karega

    score = audit_dict.get("compliance_score_percentage", 100.0)
    if score < 75.0:
        audit_dict["requires_human_review"] = True
    else:
        audit_dict["requires_human_review"] = False

    # Pydantic parsing ensures strict data validation
    return QAComplianceAudit(**audit_dict)

