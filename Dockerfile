FROM python:3.9-slim-buster
WORKDIR /backups
ARG DEV_DEPS

COPY Pipfile /backups
COPY Pipfile.lock /backups

RUN groupadd -r backups && useradd -r -g backups backups
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
		gcc \
		libpq-dev \
		python-dev \
		nano \
	&& pip install pipenv==2021.5.29 \
	&& pipenv install --system;
	&& apt-get purge -y --auto-remove gcc python-dev \
	&& apt-get -y autoremove \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

COPY src ./src
COPY etc/entrypoint.sh .
RUN chown -R backups:backups /backups

ENTRYPOINT ["/bin/sh", "/backups/entrypoint.sh"]
