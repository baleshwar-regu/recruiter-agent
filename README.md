# 🤖 Recruiter Agent

AI-powered voice agent for conducting and evaluating technical interviews.  
Built with [Pydantic AI](https://github.com/pydantic/ai), [VAPI](https://vapi.ai), and [n8n](https://n8n.io) for automation and integrations.

## 🧰 Features

- Conducts voice-based technical screening calls
- Evaluates candidates and generates a scorecard
- Integrates with Google Calendar and Twilio via `n8n`
- Modular design with agents, tools, API, and database layers

## 📦 Project Structure

```
recruiter-agent/
├── src/
│   ├── api/                # FastAPI endpoints
│   ├── agent/              # Pydantic AI agents
│   ├── db/                 # Supabase DB logic
│   ├── models/             # Pydantic models
│   ├── services/           # Business logic (e.g. schedule, evaluation)
│   ├── tools/              # Custom tools used by agents
│   ├── utils/              # Shared utilities
│   └── config.py           # Centralized config via .env
├── run.py                  # Entry point
├── requirements.txt
└── .env                    # Environment variables
```

## ⚙️ Setup

Clone the repo:

```bash
git clone https://github.com/aiinrealworld/recruiter-agent.git
cd recruiter-agent
```

Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Set Python path (for module resolution):

```powershell
$env:PYTHONPATH = "src"
```

Run the app:

```bash
python .\run.py
```

## 🧪 Development

### 🧹 Code Quality

Run linters and formatters:

```bash
# Show issues
ruff check . --diff

# Fix safe issues
ruff check . --fix

# Fix aggressively (use with caution)
ruff check . --diff --unsafe-fixes

# Sort imports
isort .

# Format code
black .
```

---

## 📞 Voice Agent Architecture

- Voice: [VAPI](https://vapi.ai) custom LLM endpoint
- Orchestration: [Pydantic AI](https://github.com/pydantic/ai)
- Scheduling: n8n + Google Calendar
- Evaluation: AI agent generates scorecard from transcript
- Storage: Supabase

---

## 🔐 Secrets

Environment variables should be stored in a `.env` file. Rename `.env.example` to `.env` and provide all values.

---

