# main.py
from src.application.orchestrator import orchestrator
from src.domain.models import AgentState
from src.utils.pricing import summarize_costs  # used only when requested

def run_cli():
    # Initialize state with keyword arguments only (fixes Pydantic validation)
    state = AgentState(
        conversation_history=[],
        last_fx_result=None,
        total_cost=0.0,
        eval_feedback=[]
    )

    print("FX Agent (type 'exit' or 'quit' to exit)")
    print("Type 'cost', 'costs', 'summary' or 'cost summary' to see usage summary")
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
                print(f"  Total cost:          ${summary['total_cost_usd']:.4f}")
                print(f"  Average per query:   ${summary['average_cost_per_query_usd']:.6f}")
                print(f"  Total queries:       {summary['total_queries']}")
                print(f"  Log file:            {summary['log_file']}")
                print(f"  Last updated:        {summary['last_updated']}")
                print("-" * 60)
            except Exception as e:
                print(f"Error reading cost summary: {e}")
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