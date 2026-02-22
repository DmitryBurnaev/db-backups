# copy source code
FROM alpine:3.18 AS code-layer
WORKDIR /db-backups

COPY src .

FROM python:3.13.12-slim-trixie
ARG POETRY_VERSION="1.7.1"
ARG PIP_DEFAULT_TIMEOUT=300
WORKDIR /db-backups
RUN groupadd -r db-backups && useradd -r -g db-backups db-backups

COPY pyproject.toml .
COPY poetry.lock .

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
		python3-dev \
        openssl \
		postgresql-client-17 \
    && pip install poetry==${POETRY_VERSION} \
    && poetry config --local virtualenvs.create false \
    && PIP_DEFAULT_TIMEOUT=${PIP_DEFAULT_TIMEOUT} poetry install --no-root --only=main --no-cache --no-ansi --no-interaction  \
    && pip uninstall -y poetry poetry-core \
	&& apt-get purge -y --auto-remove python3-dev \
	&& apt-get -y autoremove \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

RUN mkdir ./backups ./logs
RUN chown -R db-backups:db-backups ./backups
RUN chown -R db-backups:db-backups ./logs
VOLUME ./backups ./logs

COPY --from=code-layer --chown=db-backups:db-backups /db-backups ./src
ENV LOCAL_PATH_IN_CONTAINER=./backups \
    LOG_PATH=./logs

USER db-backups

ENTRYPOINT ["python", "-m", "src.run"]
