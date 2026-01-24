# Anymaker - Graph-native agent platform
# Minimal image: bootstrap loads everything else from graph

FROM python:3.11-slim

WORKDIR /app

# Install core dependencies only
# (packages needed before graph code loads)
RUN pip install --no-cache-dir \
    falkordb \
    graphiti-core \
    flask \
    httpx \
    redis

# Install additional dependencies for A0 compatibility
# These are needed by tools/helpers loaded from graph
RUN pip install --no-cache-dir \
    langchain-core \
    langchain-community \
    langchain-openai \
    langchain-anthropic \
    openai \
    anthropic \
    pydantic \
    requests \
    beautifulsoup4 \
    duckduckgo-search \
    tiktoken \
    sentence-transformers \
    python-dotenv

# Copy only the anymaker package (bootstrap + loader)
COPY anymaker/ /app/anymaker/

# Copy A0 code for initial seeding
# (After first seed, code is loaded from graph)
COPY python/ /app/python/
COPY prompts/ /app/prompts/
COPY agents/ /app/agents/

# Environment defaults
ENV PYTHONUNBUFFERED=1
ENV FALKORDB_HOST=falkordb.railway.internal
ENV FALKORDB_PORT=6379
ENV GRAPH_NAME=anymaker
ENV PORT=8080
ENV A0_GUI_PORT=8081

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Run bootstrap
CMD ["python", "-m", "anymaker.bootstrap"]
