# E-Commerce T2 Lab - Boundary Values & Data Formats
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

RUN useradd -m -u 1000 labuser && chown -R labuser:labuser /app
USER labuser

ENV PORT=8080
ENV MISSION_ID=ecom-t2-lab
ENV DEBUG_MODE=true
ENV ENV=prod

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
