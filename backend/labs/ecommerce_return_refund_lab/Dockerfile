# E-Commerce Return & Refund Lab
# Docker image for QA Training Platform

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
# Copy products catalog for T1 mission (GET /api/v1/products/{id})
COPY products_1_1000.txt ./

# Create non-root user for security
RUN useradd -m -u 1000 labuser && chown -R labuser:labuser /app
USER labuser

# Environment variables (defaults)
ENV PORT=8080
ENV SESSION_ID=default
ENV USER_ID=default
ENV MISSION_ID=ecom-return-refund
ENV FLAGS_SEED=default_seed
ENV DEBUG_MODE=true
ENV ENV=prod

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8080/health')" || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
