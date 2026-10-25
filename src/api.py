"""
src/api.py

FastAPI REST Backend for:
- Mobile APK / Progressive Web App (PWA)
- Third-Party Clients & CLI Integrations

Endpoints:
- POST /api/analyze/text       : Analyze pasted conversation text
- POST /api/analyze/whatsapp   : Analyze uploaded WhatsApp export (.txt)
- GET  /api/health             : API health check and loaded model status
"""

import logging
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from fastapi.staticfiles import StaticFiles

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.predict import ConversationSentimentAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global analyzer instance (initialized during lifespan startup)
analyzer: Optional[ConversationSentimentAnalyzer] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern lifespan context manager replacing deprecated on_event handlers."""
    global analyzer
    try:
        analyzer = ConversationSentimentAnalyzer(default_model="baseline")
        logger.info("ConversationSentimentAnalyzer successfully initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize analyzer: {e}")
    yield


app = FastAPI(
    title="Conversation Sentiment Trajectory API",
    description="REST backend for conversation-level emotional trajectory modeling & WhatsApp chat analysis.",
    version="1.2.0",
    lifespan=lifespan
)

# Enable CORS for local web and mobile clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Mobile Web Client
mobile_assets = PROJECT_ROOT / "mobile" / "assets"
if mobile_assets.exists():
    app.mount("/mobile", StaticFiles(directory=str(mobile_assets), html=True), name="mobile")


class TextAnalysisRequest(BaseModel):
    conversation_text: str = Field(..., description="Multi-line conversation, e.g. 'Alice: Hi\nBob: Hello'")
    model_type: str = Field("baseline", description="One of: 'baseline', 'roberta_independent', 'roberta_context'")
    turning_point_threshold: float = Field(0.4, ge=0.1, le=1.0)
    context_window: int = Field(3, ge=0, le=5)


@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "active_model": analyzer.active_model_type if analyzer else "uninitialized",
        "supported_models": ["baseline", "roberta_independent", "roberta_context"]
    }


@app.post("/api/analyze/text")
def analyze_text(request: TextAnalysisRequest):
    if not analyzer:
        raise HTTPException(status_code=500, detail="Analyzer not initialized.")
    try:
        result = analyzer.analyze_conversation(
            input_data=request.conversation_text,
            input_type="text",
            model_type=request.model_type,
            context_window=request.context_window,
            turning_point_threshold=request.turning_point_threshold
        )
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Analysis failed."))

        # Format predictions dataframe into serializable dict
        preds_list = result["predictions_df"].to_dict(orient="records")
        return {
            "success": True,
            "model_used": result["model_used"],
            "trajectory_stats": result["trajectory_stats"],
            "explanation": result["explanation"],
            "predictions": preds_list
        }
    except Exception as e:
        logger.error(f"Error in analyze_text: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze/whatsapp")
async def analyze_whatsapp(
    file: UploadFile = File(...),
    model_type: str = Form("baseline"),
    turning_point_threshold: float = Form(0.4),
    inactivity_gap_minutes: int = Form(120),
    context_window: int = Form(3)
):
    if not analyzer:
        raise HTTPException(status_code=500, detail="Analyzer not initialized.")

    # Validate file extension
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only exported WhatsApp .txt files are accepted.")

    try:
        content_bytes = await file.read()
        try:
            content_str = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            content_str = content_bytes.decode("latin-1")

        result = analyzer.analyze_conversation(
            input_data=content_str,
            input_type="whatsapp",
            model_type=model_type,
            context_window=context_window,
            turning_point_threshold=turning_point_threshold,
            whatsapp_gap_minutes=inactivity_gap_minutes
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Analysis failed."))

        preds_list = result["predictions_df"].to_dict(orient="records")
        return {
            "success": True,
            "filename": file.filename,
            "model_used": result["model_used"],
            "trajectory_stats": result["trajectory_stats"],
            "explanation": result["explanation"],
            "predictions": preds_list
        }
    except Exception as e:
        logger.error(f"Error in analyze_whatsapp: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api:app", host="127.0.0.1", port=8000, reload=True)
