from fastapi import FastAPI

app = FastAPI(title= "BPO AI QA Engine")

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Backend engine is up and running"}