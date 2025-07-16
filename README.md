# DyoPods

**DyoPods** is a modular AI agent framework where domain-specific agents work in coordinated pods. Each pod acts as a smart team, enabling contextual decision-making, automation, and collaboration across systems like MES, ERP, or CRM. Scalable, LLM-ready, and built for real-world operations.

---

## 🚀 Features

- Multi-agent orchestration via pods
- Domain-specific agents (RAG, MCP, MES, ERP, etc.)
- Built-in tracing, logging, and visualization
- Integration-ready with MongoDB, Ollama, LiteLLM
- Web-based UI for agent interaction

---

## 🧰 Prerequisites

Before you begin, ensure you have the following installed:

- [Docker](https://www.docker.com/)
- [Ollama](https://ollama.com/)
- [LiteLLM](https://docs.litellm.ai/docs/)
- [Node.js](https://nodejs.org/) (v18 or above)
- [Python](https://www.python.org/) (v3.10 or higher)
- [uv](https://github.com/astral-sh/uv) (Python package/dependency manager)

---

## 🗃️ MongoDB (Local)

Start MongoDB locally (Docker recommended):

```bash
docker run -d -p 27017:27017 --name dyopods-mongo mongo
```

---

## 🖥️ Backend Setup

```bash
cd backend
uv venv
source .venv/bin/activate
uv sync
playwright install --with-deps chromium

# Start the FastAPI backend
uvicorn main:app --reload
```

---

## 🌐 Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

---

## 🔁 MCP Server Setup

```bash
cd mcp
uv venv
source .venv/bin/activate
uv sync

# Rename .env file
cp sample.env .env

# Start the MCP FastAPI server
uvicorn main:app --reload
# OR
uv run fastapi dev main.py --port 8333
```

---

## 📦 Deployment Tips

- Use `tmux` or `pm2` to keep servers alive in production
- Configure `.env` with MongoDB connection, LLM endpoints
- Add `CORS_ALLOW_ORIGINS` if running UI remotely
- Expose MCP + backend + frontend via reverse proxy if hosting (e.g. nginx)

---

## 📄 License

MIT License © DyoPods Contributors