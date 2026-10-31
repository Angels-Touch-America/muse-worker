FROM python:3.10-slim

WORKDIR /app

# Flush prints/tracebacks immediately so RunPod's container log shows why a worker exits.
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y ffmpeg

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "worker.py"]