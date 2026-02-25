# app.py
'''
Fast API Endpoint and API Info
'''
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import Optional, Dict
import uuid

from src.application.orchestrator import orchestrator
from src.domain.models import AgentState
from src.application.services.evaluation_service import run_evaluation
from src.utils.pricing import summarize_costs

app = FastAPI(
    title="FX Agent API",
    description="Autonomous FX + math agent with tool calling and backtesting",
    version="0.1.0"
)

# In-memory session storage (replace with Redis/SQLite later)
sessions: Dict[str, AgentState] = {}


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest = Body(...)):
    """
    Send a message to the agent.
    - Provide session_id to continue conversation
    - Omit session_id to start a new one
    """
    session_id = request.session_id or str(uuid.uuid4())

    if session_id not in sessions:
        sessions[session_id] = AgentState(
            conversation_history=[],
            last_fx_result=None,
            total_cost=0.0,
            eval_feedback=[]
        )

    state = sessions[session_id]

    try:
        response_text = orchestrator(
            user_input=request.message,
            conversation_history=state.conversation_history,
            state=state
        )
        return ChatResponse(
            response=response_text,
            session_id=session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cost-summary")
async def get_cost_summary():
    """Get current cost usage summary from logs."""
    return summarize_costs()


@app.get("/eval")
async def get_evaluation(backtest: bool = True):
    """Run evaluation (backtest by default)."""
    return run_evaluation(backtest=backtest)


@app.get("/health")
async def health_check():
    """Simple health check."""
    return {"status": "healthy", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
