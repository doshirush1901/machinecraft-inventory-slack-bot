FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements_slack.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements_slack.txt && \
    pip install --no-cache-dir flask gunicorn

# Copy application code
COPY deploy_slack_bot.py .
COPY slack_inventory_bot.py .

# Create logs directory
RUN mkdir -p logs

# Create non-root user
RUN useradd -m -u 1000 botuser && \
    chown -R botuser:botuser /app
USER botuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Start command
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "deploy_slack_bot:app"]
