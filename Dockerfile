FROM python:3.12-slim-bookworm
ARG POETRY_VERSION="1.7.1"
ARG PIP_DEFAULT_TIMEOUT=300
WORKDIR /app

COPY pyproject.toml /app
COPY poetry.lock /app

RUN groupadd -r bkp-group && useradd -r -g bkp-user bkp-group
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
		gcc \
		libpq-dev \
		python-dev \
		wget \
		gnupg2 \
        openssl \
	&& sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt buster-pgdg main" > /etc/apt/sources.list.d/pgdg.list' \
	&& wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - \
	&& apt-get update \
	&& apt-get install -y postgresql-client-15 \
    && pip install poetry==${POETRY_VERSION} \
    && poetry config --local virtualenvs.create false \
    && PIP_DEFAULT_TIMEOUT=${PIP_DEFAULT_TIMEOUT} poetry install --only=main --no-root --no-cache --no-ansi --no-interaction  \
    && pip uninstall -y poetry poetry-core \
	&& apt-get purge -y --auto-remove gcc python-dev wget \
	&& apt-get -y autoremove \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

COPY src ./src
RUN mkdir ./backups
VOLUME ./backups
RUN chown -R bkp-user:bkp-group /backups
