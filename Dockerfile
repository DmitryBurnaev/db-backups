FROM python:3.12-slim-bookworm
ARG POETRY_VERSION="1.7.1"
ARG PIP_DEFAULT_TIMEOUT=300
WORKDIR /app
RUN mkdir /app/backups

COPY pyproject.toml /app
COPY poetry.lock /app

RUN groupadd -r bkp-group && useradd -r -g bkp-group bkp-user
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
		python3-dev \
        openssl \
		postgresql-client-15 \
    && pip install poetry==${POETRY_VERSION} \
    && PIP_DEFAULT_TIMEOUT=${PIP_DEFAULT_TIMEOUT} poetry install --only=main --no-cache --no-ansi --no-interaction  \
	&& apt-get purge -y --auto-remove python3-dev \
	&& apt-get -y autoremove \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

COPY src ./src
VOLUME ./backups
RUN chown -R bkp-user:bkp-group ./backups
ENTRYPOINT ["poetry", "run"]
