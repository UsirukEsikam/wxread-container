FROM debian:bookworm-slim AS supercronic

ARG SUPERCRONIC_VERSION=v0.2.49
ARG SUPERCRONIC_SHA1SUM=0b6c5bb743e0b0dafed1132198c81807927ac413

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl \
    && curl -fsSL \
        "https://github.com/aptible/supercronic/releases/download/${SUPERCRONIC_VERSION}/supercronic-linux-arm64" \
        -o /supercronic \
    && echo "${SUPERCRONIC_SHA1SUM}  /supercronic" | sha1sum -c - \
    && chmod 0755 /supercronic \
    && rm -rf /var/lib/apt/lists/*

FROM python:3.12-slim-bookworm

ARG UPSTREAM_SHA=unknown

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Shanghai \
    CRON_SCHEDULE="0 1 * * *" \
    WXREAD_UPSTREAM_SHA=${UPSTREAM_SHA}

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir "requests>=2.32.3,<3"

RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin app

WORKDIR /app

COPY --from=supercronic /supercronic /usr/local/bin/supercronic
COPY --chown=app:app upstream/ /app/upstream/
COPY --chown=app:app runner.py /app/runner.py

RUN test -f /app/upstream/main.py \
    && test -f /app/upstream/config.py \
    && test -f /app/upstream/push.py \
    && test -f /app/upstream/log_utils.py \
    && python -m compileall -q /app/upstream /app/runner.py

USER app

CMD ["sh", "-c", "printf '%s %s\\n' \"$CRON_SCHEDULE\" 'python /app/runner.py' > /tmp/wxread.crontab && exec supercronic -split-logs /tmp/wxread.crontab"]
