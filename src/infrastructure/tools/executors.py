from src.domain.models import ToolResult, FxAnalysisResult
from src.config.settings import settings
# Import your existing logic (we'll move them in migration)
from src.analysis.fx import analyze_fx
from src.infrastructure.llm.calc import safe_eval
from src.application.services.fx_service import run_fx_analysis


def calculate_expression(expression: str) -> dict:
    try:
        result = safe_eval(expression)
        return {"status": "success", "result": result, "expression": expression}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# src/infrastructure/tools/executors.py

def run_fx_analysis_tool(base_currency: str = None, target_currency: str = None):
    return run_fx_analysis(base_currency, target_currency)

# Registry — auto-used by orchestrator
TOOL_EXECUTORS = {
    "calculate_expression": calculate_expression,
    "run_fx_analysis": run_fx_analysis,
    # New tool? Just add here → automatically available
}