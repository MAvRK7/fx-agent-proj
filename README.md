# agent-proj

[![Tests](https://github.com/MAvRK7/agent-proj/actions/workflows/ci.yml/badge.svg)](https://github.com/MAvRK7/agent-proj/actions)
[![codecov](https://codecov.io/gh/MAvRK7/agent-proj/graph/badge.svg)](https://codecov.io/gh/YOUR_USERNAME/YOUR_REPO)

# 🤖 Multi-Currency FX Analysis Agent

An autonomous, AI-powered financial assistant designed to analyze exchange rates, perform Monte Carlo simulations, and provide actionable "buy/sell" recommendations for **any currency pair**.

The system combines statistical rigor (volatility, drift, risk bands) with LLM-powered reasoning to help users time their currency exchanges effectively.

---

## 🚀 Key Features

- **Any Currency Pair**: Supports dynamic analysis for any valid forex pair (e.g., USD/INR, EUR/AUD, BTC/USD).
- **FastAPI Integration**: A production-ready REST API with session management for continuous conversations.
- **Monte Carlo Simulations**: Runs 1,000+ simulations to calculate the probability of rate improvements over a 7-day window.
- **Clean Architecture**: Modular design separating domain models, infrastructure (LLM clients), and application logic.
- **Dual-Layer AI**: Primary reasoning via OpenRouter with automated fallback to Mistral.
- **Cost & Performance Tracking**: Built-in tools to summarize API costs and log agent events.

---

## 📂 Project Structure

```text
└── mavrk7-fx-agent-proj/
    ├── app.py                # FastAPI Web Server & Endpoints
    ├── agent-project.py      # Core CLI logic and Orchestrator entry
    ├── eval.py               # Evaluation and backtesting suite
    ├── src/
    │   ├── application/      # Orchestrators and Services (FX, Eval)
    │   ├── domain/           # Core models (AgentState, FXResult)
    │   ├── infrastructure/   # LLM Clients (OpenRouter/Mistral) & Tools
    │   └── analysis/         # Math logic (Monte Carlo, Risk, Stats)
    ├── tests/                # Unit tests & coverage
    └── .github/workflows/    # CI/CD (GitHub Actions)
```

## 🛠️ Installation

### 1️⃣ Clone the repository

```
git clone https://github.com/MAvRK7/agent-proj.git
cd agent-proj
```

### 2️⃣ Install dependencies

```
pip install -r requirements.txt
```
### 3️⃣ Set up environment variables

Create a .env file in the project root:

- OPENROUTER_API_KEY=your_key_here
- MISTRAL_API_KEY=your_key_here

## 🖥️ Usage

▶ Running the API (FastAPI)

Start the web server:

```
python app.py
```
or 

```
uvicorn app:app --reload --port 8000
```

* Interactive Docs: Visit http://localhost:8000/docs to test the API via Swagger UI.
* Chat Endpoint:

### Chat Endpoint

**POST** `/chat`

**Example request body:**

```json
{
  "message": "Should I send USD to INR today?"
}
```

## 💻 Running the CLI

For direct terminal-based interaction:
```
python main.py
```

## 📊 Running Backtests

Evaluate predictive accuracy against historical data:
```
python eval.py --backtest
```
## 📡 API Endpoints

Method	Endpoint	Description

| Method | Endpoint        | Description                                      |
| ------ | --------------- | ------------------------------------------------ |
| POST   | `/chat`         | Send a message to the agent (supports sessions). |
| GET    | `/eval`         | Run backtesting and get accuracy metrics.        |
| GET    | `/cost-summary` | View total LLM token usage and costs.            |
| GET    | `/health`       | Check API status.                                |

## 🧪 Testing

The project uses pytest and includes CI/CD via GitHub Actions.
```
pytest --cov=src tests/
```

## ⚖️ License

This project is licensed under the LICENSE file included in this repository.

## 🤝 Contributions
Contributions welcome. Feel free to reach me out or use this repo.
