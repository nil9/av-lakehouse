# Base image: Python compatible with Waymo SDK
FROM python:3.10-bookworm

# ---- System dependencies (Java for Spark + network fixes) ----
# Do NOT write to /etc/resolv.conf (read-only under BuildKit)
# Switch Debian mirrors to HTTPS to avoid proxy/MITM issues
RUN sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list || true

# Update with IPv4 and retries, then install deps
RUN apt-get -o Acquire::ForceIPv4=true -o Acquire::Retries=10 update \
 && apt-get install -y --no-install-recommends \
      ca-certificates \
      curl \
      wget \
      gnupg \
      lsb-release \
      default-jdk \
      git \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# ---- Python tooling ----
RUN pip install --upgrade pip --no-cache-dir

# ---- AV + Spark dependencies ----
# Waymo SDK is tightly coupled to TensorFlow versions
RUN pip install --no-cache-dir \
    tensorflow==2.11.0 \
    waymo-open-dataset-tf-2-11-0==1.6.1

RUN pip install --no-cache-dir \
    pyspark==3.4.0 \
    pandas \
    numpy

# ---- Spark environment ----
# On Debian bookworm, default-jdk installs OpenJDK 17; set JAVA_HOME accordingly
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PYSPARK_PYTHON=python
ENV PYTHONPATH=/usr/local/lib/python3.10/site-packages

# Set the working directory for your ingestion engine
WORKDIR /app

# The final command is left to devcontainer.json or spark-submit
CMD ["python3"]