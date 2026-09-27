FROM python:3.12-slim
WORKDIR /app
COPY tablekeeper /app/tablekeeper
COPY static /app/static
ENV PORT=8080 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
USER 65534:65534
EXPOSE 8080
CMD ["python", "-m", "tablekeeper.server"]
