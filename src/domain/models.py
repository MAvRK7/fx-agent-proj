# All pydantic models

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class FxAnalysisResult(BaseModel):
    pair: str = "AUD/INR"
    current_rate: float
    prob_up: float
    decision: str
    confidence: float = Field(..., ge=0, le=1)
    volatility: float
    expected_7d: float
    scenario: Dict[str, float]
    forecast7d: List[float]

class ToolResult(BaseModel):
    status: str = "success"
    data: Any
    error: Optional[str] = None

class AgentState(BaseModel):
    conversation_history: List[Dict] = Field(default_factory=list)
    last_fx_result: Optional[FxAnalysisResult] = None
    total_cost: float = 0.0
    eval_feedback: List[Dict] = Field(default_factory=list)  # for future feedback loop