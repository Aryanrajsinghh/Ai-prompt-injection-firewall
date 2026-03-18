"""
FastAPI prediction service for the ML Detection Module.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from inference.predictor import PromptPredictor
from utils.config import API_HOST, API_PORT

app = FastAPI(
    title="AI Prompt ML Detection API",
    description="Semantic analysis API for detecting malicious AI prompts",
    version="1.0.0"
)

# Initialize predictor
predictor = None


class PromptRequest(BaseModel):
    prompt: str


class PredictionResponse(BaseModel):
    attack_type: str
    risk_score: float


@app.on_event("startup")
async def load_model():
    """Load the trained model on startup."""
    global predictor
    predictor = PromptPredictor()
    predictor.load()


@app.post("/ai_detect", response_model=PredictionResponse)
async def ai_detect(request: PromptRequest):
    """
    Analyze a prompt and return attack classification.
    
    Args:
        request: PromptRequest containing the prompt text
        
    Returns:
        PredictionResponse with attack_type and risk_score
    """
    if predictor is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        prediction = predictor.predict(request.prompt)
        return PredictionResponse(**prediction)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "model_loaded": predictor is not None}


if __name__ == "__main__":
    uvicorn.run(app, host=API_HOST, port=API_PORT)
