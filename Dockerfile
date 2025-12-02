FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies if needed (optional)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     curl \
#     && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --disable-pip-version-check -r requirements.txt

# Copy application code (including src and config)
COPY src/ ./src/
COPY config/ ./config/

# Create a non-root user for running the app
RUN useradd -m appuser
USER appuser

# Entrypoint to run the CLI tool
ENTRYPOINT ["python", "src/s3_component_replacer.py"]

# Default argument when someone runs `docker run image`
CMD ["--help"]