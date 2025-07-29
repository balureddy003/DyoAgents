# AutoGen accelerator

The following steps are for manual/local development:

Set up a virtual environment (Preferred)
uv venv
source .venv/bin/activate

uv sync
PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 pip install playwright
python -m playwright install chromium

python -m uvicorn main:app --reload

To see detailed agent logs during development, set `DEBUG_AGENT_LOGS=true` in
your `.env` file before starting the backend.

For Docker-based development, make sure your Dockerfile installs all dependencies and explicitly runs:

```bash
python -m playwright install chromium
python -m uvicorn main:app --host 0.0.0.0 --port 3100
```