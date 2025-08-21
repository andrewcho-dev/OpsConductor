"""
Job Execution Service
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="Job Execution Service", version="1.0.0")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(
        status_code=200,
        content={"status": "healthy", "service": "job-execution-service"}
    )

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Job Execution Service is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)