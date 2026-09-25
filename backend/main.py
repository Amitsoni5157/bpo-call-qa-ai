import os
import json
import shutil
import uuid
import traceback
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.schemas import QAComplianceAudit, AuditRequestResponse
from backend.transcriber import transcribe_audio
from backend.analyzer import analyze_call_transcript
from backend.database import init_db, get_db, CallAuditRecord

init_db()

app = FastAPI(
    title="BPO AI QA & Compliance Engine",
    description="Automated Speech-to-Text & Quality Audit microservice for customer support calls.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ReviewOverrideRequest(BaseModel):
    requires_human_review: bool
    supervisor_feedback: str

TEMP_DIR = "temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "BPO AI QA Engine"}

@app.patch("/api/v1/audits/{call_id}/review")
def update_call_review(
    call_id: str,
    payload: ReviewOverrideRequest,
    db: Session = Depends(get_db)
):
    record = db.query(CallAuditRecord).filter(CallAuditRecord.call_id == call_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Call record not found.")

    record.requires_human_review = payload.requires_human_review
    
    # Existing notes me supervisor override append karein
    notes = json.loads(record.audit_notes) if record.audit_notes else []
    notes.append(f"[SUPERVISOR REVIEW]: {payload.supervisor_feedback}")
    record.audit_notes = json.dumps(notes)

    db.commit()
    return {"status": "success", "message": f"Audit record {call_id} updated successfully."}

@app.post("/api/v1/audit-call", response_model=AuditRequestResponse)
async def audit_call(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    valid_extensions = [".mp3", ".wav", ".m4a", ".ogg"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in valid_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format '{file_ext}'. Allowed formats: {valid_extensions}"
        )

    call_id = f"CALL-{uuid.uuid4().hex[:8].upper()}"
    temp_file_path = os.path.join(TEMP_DIR, f"{call_id}_{file.filename}")

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 1. Transcribe speech
        transcript = transcribe_audio(temp_file_path)
        if not transcript:
            raise HTTPException(status_code=422, detail="Audio could not be transcribed.")

        # 2. Analyze & Audit
        audit_data: QAComplianceAudit = analyze_call_transcript(transcript=transcript, call_id=call_id)

        # 3. Save to Database
        try:
            db_record = CallAuditRecord(
                call_id=audit_data.call_id,
                customer_sentiment=audit_data.customer_sentiment,
                primary_issue=audit_data.primary_issue,
                agent_professionalism_score=int(audit_data.agent_professionalism_score),
                mandatory_greeting_done=bool(audit_data.mandatory_greeting_done),
                solution_provided=audit_data.solution_provided,
                compliance_score_percentage=float(audit_data.compliance_score_percentage),
                requires_human_review=bool(audit_data.requires_human_review),
                audit_notes=json.dumps(audit_data.audit_notes)
            )
            db.add(db_record)
            db.commit()
            db.refresh(db_record)
        except Exception as db_err:
            db.rollback()
            print("Database Insert Error:", str(db_err))
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Database persistence error: {str(db_err)}")

        return AuditRequestResponse(
            status="success",
            message="Call audited and saved successfully.",
            data=audit_data
        )

    except HTTPException:
        raise
    except Exception as e:
        print("General Processing Error:", str(e))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.get("/api/v1/audits")
def get_all_audits(db: Session = Depends(get_db)):
    records = db.query(CallAuditRecord).order_by(CallAuditRecord.id.desc()).all()
    
    results = []
    for r in records:
        results.append({
            "id": r.id,
            "call_id": r.call_id,
            "customer_sentiment": r.customer_sentiment,
            "primary_issue": r.primary_issue,
            "agent_professionalism_score": r.agent_professionalism_score,
            "mandatory_greeting_done": r.mandatory_greeting_done,
            "solution_provided": r.solution_provided,
            "compliance_score_percentage": r.compliance_score_percentage,
            "requires_human_review": r.requires_human_review,
            "audit_notes": json.loads(r.audit_notes) if r.audit_notes else [],
            "created_at": str(r.created_at) if r.created_at else None
        })
    return {"status": "success", "total_records": len(results), "records": results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)