FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    gcc \
    libssl-dev \
    ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/


RUN pip install --no-cache-dir requests

COPY catchmail_poll.py .

RUN useradd -m appuser
USER appuser

CMD ["python", "catchmail_poll.py"]
