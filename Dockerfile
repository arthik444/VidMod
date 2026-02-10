# VidMod Backend Dockerfile
# Multi-stage build: compile in stage 1, run in stage 2 (smaller image, faster deploys)

# ============= BUILD STAGE =============
FROM python:3.11-slim AS builder

# Install build tools (only needed for compilation)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python packages to /root/.local (will copy to runtime stage)
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --user -r requirements.txt

# ============= RUNTIME STAGE =============
FROM python:3.11-slim

# Install ONLY runtime dependencies (no gcc/g++, smaller image!)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Copy compiled packages from builder (no source code needed!)
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Create storage directories
RUN mkdir -p storage/uploads storage/frames storage/output

# Add local pip packages to PATH
ENV PATH=/root/.local/bin:$PATH

# Cloud Run uses port 8080 by default
EXPOSE 8080

# Run with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]
