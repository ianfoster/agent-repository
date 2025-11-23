from fastapi import FastAPI

app = FastAPI(
    title="Academy Agent Repository Backend",
    version="0.1.0",
    description="Core API for the Academy Agent Repository.",
)

@app.get("/health")
def health():
    return {"status": "ok", "service": "backend"}
