FROM python:3.11-slim

WORKDIR /app

# Install required tools including Node.js
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install claude-code globally via npm
RUN npm install -g @anthropic-ai/claude-code

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and configuration
COPY claude_code_server /app/claude_code_server
COPY litellm_config.yaml .flake8 /app/


# Set environment variables
ENV PORT=4000
ENV LITELLM_MASTER_KEY=sk-1234
ENV PATH="/usr/local/bin:${PATH}"

# Expose port for LiteLLM proxy
EXPOSE 4000

# Health check - check if the service is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:4000 || exit 1

# Run the LiteLLM server directly
CMD ["litellm", "--config", "litellm_config.yaml", "--port", "4000"]