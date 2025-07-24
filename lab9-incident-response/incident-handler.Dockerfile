# incident-handler.Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY incident-handler.py .
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "incident-handler.py"]
