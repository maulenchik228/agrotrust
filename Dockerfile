# Container image for agrotrust-metrics.
#   docker build -t agrotrust-metrics .
#   docker run --rm agrotrust-metrics --help                  # use the CLI
#   docker run --rm -p 8000:8000 agrotrust-metrics serve      # demo report on http://localhost:8000

ARG PYTHON_IMAGE=python:3.12-slim

# ---- stage 1: build a wheel from the sources ---------------------------------------
FROM ${PYTHON_IMAGE} AS build
WORKDIR /src
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir --upgrade pip build \
 && python -m build --wheel --outdir /dist

# ---- stage 2: small runtime image ----------------------------------------------------
FROM ${PYTHON_IMAGE} AS runtime
LABEL org.opencontainers.image.title="agrotrust-metrics" \
      org.opencontainers.image.description="Reliability metrics for IoT agricultural monitoring data" \
      org.opencontainers.image.source="https://github.com/maulenchik228/agrotrust" \
      org.opencontainers.image.licenses="MIT"
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg \
    MPLCONFIGDIR=/tmp/matplotlib
COPY --from=build /dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm /tmp/*.whl \
 && useradd --create-home --uid 10001 app
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod 0755 /usr/local/bin/entrypoint.sh
USER app
WORKDIR /home/app
EXPOSE 8000
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["--help"]
