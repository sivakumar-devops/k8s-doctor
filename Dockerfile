FROM python:3.12-slim

WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY k8s_client.py .
COPY k8s_doctor.py .
COPY diagnosis_engine.py .
COPY error_detection.py .
COPY remediation_engine.py .
COPY notifications.py .
COPY rate_limiter.py .

EXPOSE 8080

# Run as non-root
RUN useradd -m -u 1000 doctor && chown -R doctor:doctor /app
USER doctor

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["python", "-u", "k8s_doctor.py"]
