import os
import shutil
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Direct absolute imports from backend package
from backend.schemas import AuditRequestResponse
from backend.transcriber import transcribe_audio
from backend.analyzer import analyze_call_transcript
# import os
# import shutil
# import uuid
# from fastapi import FastAPI, UploadFile, File, HTTPException
# from fastapi.middleware.cors import CORSMiddleware

# try:
#     from backend.schemas import AuditRequestResponse
#     from backend.transcriber import transcribe_audio
#     from backend.analyzer import analyze_call_transcript
# except ImportError:
#     from schemas import AuditRequestResponse
#     from transcriber import transcribe_audio
#     from analyzer import analyze_call_transcript

app = FastAPI(
    title="BPO AI QA & Compliance Engine",
    description="Automated Speech-to-Text & Quality Audit microservice for customer support calls.",
    version="1.0.0"
)

# Frontend communication ke liye CORS enable
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_DIR = "temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "BPO AI QA Engine"}

@app.post("/api/v1/audit-call", response_model=AuditRequestResponse)
async def audit_call(file: UploadFile = File(...)):
    """
    Audio file upload endpoint:
    1. Whisper transcription
    2. LLM Compliance Audit
    3. Structured Pydantic payload response
    """
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
        audit_data = analyze_call_transcript(transcript=transcript, call_id=call_id)

        return AuditRequestResponse(
            status="success",
            message="Call audited successfully.",
            data=audit_data
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)