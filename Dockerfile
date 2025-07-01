# Stock Advisor Application Dockerfile
# Optimized for Azure Container Apps

# Stage 1: Frontend build
FROM node:18-alpine AS frontend-builder

# Set working directory for frontend build
WORKDIR /app/frontend

# Copy package files and install dependencies
COPY package*.json ./
RUN npm ci

# Copy frontend source code
COPY app/ ./app/
COPY src/ ./src/
COPY index.html ./
COPY vite.config.ts ./
COPY tailwind.config.js ./
COPY postcss.config.js ./
COPY tsconfig*.json ./

# Build frontend
RUN npm run build && echo "Frontend build completed successfully"

# Stage 2: Python application
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PORT=8000
# Will be overridden by Azure App Service settings if configured there
ENV APP_ENV=production

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create main.py entry point first to ensure it exists
COPY main.py ./

# Copy application code
COPY api/ ./api/
COPY agents/ ./agents/
COPY mcp_servers/ ./mcp_servers/
COPY data/ ./data/
COPY langgraph.json ./

# Copy built frontend from previous stage
COPY --from=frontend-builder /app/frontend/dist ./static/

# Create startup script
COPY --chown=root:root docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

# Create non-root user for better security
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app

# Expose only the main application port used by Azure
EXPOSE 8000

# Add a more robust health check
# Use the health endpoint, with longer timeout for slow startup
HEALTHCHECK --interval=30s --timeout=60s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Switch to non-root user
USER appuser

# Use an explicit CMD instead of ENTRYPOINT for better Azure compatibility
CMD ["/app/docker-entrypoint.sh"]