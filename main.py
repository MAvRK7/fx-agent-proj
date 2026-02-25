# main.py
from src.application.orchestrator import orchestrator
from src.domain.models import AgentState
from src.utils.pricing import summarize_costs  # used only when requested
from src.application.services.evaluation_service import run_evaluation

def run_cli():
    # Initialize state with keyword arguments only (fixes Pydantic validation)
    state = AgentState(
        conversation_history=[],
        last_fx_result=None,
        total_cost=0.0,
        eval_feedback=[]
    )

    print("FX Agent (type 'exit' or 'quit' to exit)")
    print("Type 'cost', 'costs', 'summary' or 'cost summary' to see usage summary !eval for eval")
    print("-" * 60)

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ('exit', 'quit'):
            print("Goodbye!")
            break

        if user_input.lower() in ('cost', 'costs', 'summary', 'cost summary'):
            try:
                summary = summarize_costs()
                print("\nCost Summary:")
                print(f"  Total cost:               ${summary['total_cost_usd']:.4f}")
                print(f"  Average per query:        ${summary['average_cost_per_query_usd']:.6f}")
                print(f"  Total queries so far:     {summary['total_queries']}")
                print(f"  Projected monthly cost:   ${summary['projected_monthly_cost_usd']:.4f}")
                print(f"    ({summary['assumption']})")
                print(f"  Log file:                 {summary['log_file']}")
                print(f"  Last updated:             {summary['last_updated']}")
                print("-" * 60)
            except Exception as e:
                print(f"Could not read cost summary: {e}")
            continue

        # In main.py – replace your !eval block with this

        if user_input.lower() in ('!eval', '!evaluation', '!backtest'):
            try:
                result = run_evaluation(backtest=True)  # always backtest for now
                print("\nEvaluation Summary (historical backtest):")
                print(f"  Evaluated: {result.get('total_predictions_evaluated', 0)}")
                print(f"  Accuracy:  {result.get('accuracy_pct', 0.0)}% "
                    f"({result.get('correct', 0)}/{result.get('total_predictions_evaluated', 0)})")
                print(f"  Avg conf correct: {result.get('avg_conf_correct', 0.0)}")
                print(f"  Avg conf wrong:   {result.get('avg_conf_wrong', 0.0)}")
                if "message" in result:
                    print(f"  Note: {result['message']}")
                if "backtest_period" in result:
                    print(f"  Period: {result['backtest_period']}")
                print("-" * 60)
            except Exception as e:
                print(f"Evaluation failed: {e}")
            continue

        # Normal query flow
        try:
            response = orchestrator(
                user_input=user_input,
                conversation_history=state.conversation_history,
                state=state
            )
            print("\nAgent:", response)
            print("-" * 60)
        except Exception as e:
            print(f"Error: {e}")
            print("-" * 60)


if __name__ == "__main__":
    run_cli()