FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ curl \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxcomposite1 \
    libxrandr2 libxdamage1 libgbm1 libxshmfence1 libxfixes3 \
    libasound2 libpangocairo-1.0-0 libpangoft2-1.0-0 libgtk-3-0 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /code/src/mcp

ENV VIRTUAL_ENV=/code/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

ENV DEBUG_AGENT_LOGS=true

# Copy only dependency metadata first to leverage Docker cache
COPY src/mcp/pyproject.toml /code/pyproject.toml

# Install uv and all dependencies in one layer
RUN pip install uv \
    && uv venv .venv \
    && . .venv/bin/activate && uv sync


# Copy the rest of the source code
COPY . /code

# Expose API port
EXPOSE 3100

# Run app
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "4100"]