FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends nginx-light && rm -rf /var/lib/apt/lists/*
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --require-hashes -r requirements.txt
COPY tablekeeper /app/tablekeeper
COPY static /app/static
COPY deploy /app/deploy
RUN mkdir /data && chown 65534:65534 /data
ENV PORT=8080 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 TABLEKEEPER_DB=/data/tablekeeper.sqlite3
USER 65534:65534
EXPOSE 8080
CMD ["python", "-m", "tablekeeper.launch"]
