FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SPARK_LOCAL_IP=127.0.0.1 \
    SPARK_LOCAL_HOSTNAME=localhost \
    PYTHONPATH=/app \
    JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

RUN apt-get update \
    && apt-get install -y --no-install-recommends openjdk-17-jre-headless bash tini \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements-docker.txt /app/requirements-docker.txt

RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements-docker.txt

COPY . /app

RUN chmod +x /app/scripts/run_pipeline.sh \
    && mkdir -p /app/logs /app/data

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["bash", "-lc", "./scripts/run_pipeline.sh"]

