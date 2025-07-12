# DyoPods
DyoPods is a modular AI agent framework where domain-specific agents work in coordinated pods. Each pod acts as a smart team, enabling contextual decision-making, automation, and collaboration across systems like MES, ERP, or CRM. Scalable, LLM-ready, and built for real-world operations.

#run mongodb

#Install backend
uv venv
source .venv/bin/activate
uv sync
playwright install --with-deps chromium

uvicorn main:app --reload

#install frontend
npm install
npm run dev

#install mcp
uv venv
source .venv/bin/activate
uv sync

rename the sample.env to .env

uvicorn main:app --reload

or 
uv run fastapi dev main.py --port 8333