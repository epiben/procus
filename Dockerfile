FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    curl

WORKDIR /app
COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .
