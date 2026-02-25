# src/application/services/fx_service.py

"""
Business logic layer for FX-related operations.
Wraps raw analysis functions and handles defaults + errors.
"""

from typing import Optional, Dict, Any
from src.analysis.fx import analyze_fx


def run_fx_analysis(
    base_currency: Optional[str] = None,
    target_currency: Optional[str] = None
) -> Dict[str, Any]:

    base = (base_currency or "aud").lower()
    quote = (target_currency or "inr").lower()

    try:
        # Core analysis call
        result = analyze_fx(base=base, quote=quote)

        # Ensure pair formatting is consistent
        result["pair"] = f"{base.upper()}/{quote.upper()}"

        return result

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "pair": f"{base.upper()}/{quote.upper()} (failed)",
            "error_detail": repr(e),
        }