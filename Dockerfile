FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 MPLBACKEND=Agg
WORKDIR /app
COPY requirements-v5.txt requirements-platform.txt requirements-platform-lock.txt ./
RUN pip install --no-cache-dir -r requirements-platform-lock.txt
COPY . .
RUN mkdir -p /app/models /app/data /app/outputs && useradd --uid 10001 --create-home platform && chown -R platform:platform /app
USER 10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/ready')"
CMD ["python","-m","uvicorn","credit_platform.api:app","--host","0.0.0.0","--port","8000","--no-access-log","--log-config","deployment/logging.json"]
