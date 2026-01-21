FROM python:3.11-slim

# Install system dependencies (ffmpeg for yt-dlp, deno for YouTube)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    git \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install deno
RUN curl -fsSL https://deno.land/install.sh | sh
ENV PATH="/root/.deno/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create temp directory for video downloads
RUN mkdir -p /tmp/recipe-keeper

# Expose port (Render sets PORT env variable)
ENV PORT=8000
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:$PORT/api/health || exit 1

# Start uvicorn server
CMD uvicorn main:app --host 0.0.0.0 --port $PORT --log-level info
