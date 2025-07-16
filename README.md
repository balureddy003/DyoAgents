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
- [Jaeger](https://www.jaegertracing.io/docs/latest/getting-started/) (for distributed tracing)

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

## 📈 Jaeger Tracing Setup

Jaeger is used to trace agent interactions and backend operations.

### 🔧 Local Setup with Docker

Run the Jaeger all-in-one image:

```bash
docker run -d --name jaeger \
  -e COLLECTOR_ZIPKIN_HTTP_PORT=9411 \
  -p 5775:5775/udp \
  -p 6831:6831/udp \
  -p 6832:6832/udp \
  -p 5778:5778 \
  -p 16686:16686 \
  -p 14268:14268 \
  -p 14250:14250 \
  -p 9411:9411 \
  jaegertracing/all-in-one:1.54
```

Access the UI at: [http://localhost:16686](http://localhost:16686)

### 🧪 Verify Integration

Ensure the backend and MCP services export traces to Jaeger by setting the following in `.env` or FastAPI settings:

```env
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_SERVICE_NAME=dyo-backend
```

Also configure OpenTelemetry in your FastAPI app to initialize tracing with Jaeger exporter.

---

## 📄 License

MIT License © DyoPods Contributors