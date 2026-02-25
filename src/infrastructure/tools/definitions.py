from typing import List, Dict

def get_all_tools() -> List[Dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": "calculate_expression",
                "description": """Evaluate ANY mathematical expression or currency conversion calculation.
        MANDATORY for:
        - Any math (2+2, 3800000 / 83.5, 38 lakh INR to USD)
        - Converting amounts using a known rate
        Never guess numbers yourself — always call this.""",
                "parameters": {
                    "type": "object",
                    "properties": {"expression": {"type": "string"}},
                    "required": ["expression"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "run_fx_analysis",
                "description": """Run full FX analysis and 7-day forecast for any currency pair.
        Use this tool for:
        - Current exchange rate
        - Buy/sell/hold/wait recommendations
        - Is it a good time to convert X to Y?
        - Expected direction (up/down)
        - Any question containing "rate", "convert", "exchange", "forecast", "good time", "should I"

        Parameters:
        - base_currency: source currency (e.g. INR, AUD). Default AUD if not specified.
        - target_currency: destination currency (e.g. USD, INR). Default INR if not specified.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "base_currency": {"type": "string", "description": "e.g. INR"},
                    "target_currency": {"type": "string", "description": "e.g. AUD"}
                    },
                    "required": []
                }
            }
        },
        # ← ADD NEW TOOLS HERE IN THE FUTURE
        # Example future tool:
        # {
        #     "type": "function",
        #     "function": {
        #         "name": "get_latest_news",
        #         "description": "Search latest financial news for a currency or stock",
        #         "parameters": { ... }
        #     }
        # }
    ]