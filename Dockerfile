FROM python:3.9-slim-buster
WORKDIR /backups

COPY Pipfile /backups
COPY Pipfile.lock /backups

RUN groupadd -r backups && useradd -r -g backups backups
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
		gcc \
		libpq-dev \
		python-dev \
		nano \
		wget \
		gnupg2 \
	&& sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt buster-pgdg main" > /etc/apt/sources.list.d/pgdg.list' \
	&& wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - \
	&& apt-get update \
	&& apt-get install -y postgresql-client-12 \
	&& pip install pipenv==2021.5.29 \
	&& pipenv install --system \
	&& apt-get purge -y --auto-remove gcc python-dev \
	&& apt-get -y autoremove \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

COPY src ./src
RUN mkdir ./backups
VOLUME ./backups
RUN chown -R backups:backups /backups
