FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

RUN apt-get update && apt-get -y --no-install-recommends install \
    build-essential ca-certificates curl git tini \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN uv sync --frozen

EXPOSE 9177
ENTRYPOINT ["tini", "-g", "--"]
CMD ["uv", "run", "mneme-server"]
