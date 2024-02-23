<h2 align="center">Simple backup databases to a local directory or S3-storage</h2>

Allows to backup PG databases via native pgdump (connect to service) or pgdump inside specific docker-container.

## Installation and usage (docker)

### Pull last version
```shell
export DB_BACKUPS_TOOL_PATH="/opt/db-backups"
git clone [repository_url] "${DB_BACKUPS_TOOL_PATH}"
```

### ENV configuration
```shell
cd $DB_BACKUPS_TOOL_PATH
cp .env.template .env
nano .env  # set required variables
```

### Run backups
Preparations (build docker's image locally):
```shell
docker build . -t db-backups
```

Help info:
```shell
docker compose run --rm do backup --help
```

Run backup with copy result on local storage:
```shell
DB_BACKUPS_TOOL_PATH="/opt/db-backups"
DB_NAME="podcast_service"
CONTAINER_NAME="postgres-12"
LOCAL_PATH=$(pwd)/backups  # path on your host machine

cd $DB_BACKUPS_TOOL_PATH
echo "LOCAL_PATH=$LOCAL_PATH" >> .env

docker compose run --rm do backup ${DB_NAME} --from PG-SERVICE --to LOCAL
# or via docker run:
docker run \
  --volume ${LOCAL_PATH}:/db-backups/backups \
  --network "host" \
  --env-file $(pwd)/.env \
  --rm \
  db-backups \
  backup ${DB_NAME} --from PG-SERVICE --to LOCAL
```

Run backup with copy result to S3 storage (and encrypt result):
```shell
DB_BACKUPS_TOOL_PATH="/opt/db-backups"
DB_NAME="podcast_service"
CONTAINER_NAME="postgres-12"
ENCRYPT_PASS="<YOUR-ENCRYPT_PASSWORD>"  # replace with your real encrypt password

cd $DB_BACKUPS_TOOL_PATH
echo "ENCRYPT_PASS=$ENCRYPT_PASS" >> .env

# NOTE: you need to fill S3_* specific env in .env file before
docker compose run --rm do backup ${DB_NAME} --from PG-SERVICE --to S3 --encrypt

# or via docker run:
docker run \
  --volume ${LOCAL_PATH}:/db-backups/backups \
  --network "host" \
  --env-file $(pwd)/.env \
  --rm \
  db-backups \
  backup ${DB_NAME} --from PG-SERVICE --to S3 --encrypt
```

### Run restore
Preparations (build docker's image locally):
```shell
docker build . -t db-backups
```

Help info:
```shell
docker compose run --rm do restore --help
```

Run restore from local / s3 directory (find file for current day):
```shell
DB_BACKUPS_TOOL_PATH="/opt/db-backups"
DB_NAME="podcast_service"
CONTAINER_NAME="postgres-12"
LOCAL_PATH=$(pwd)/backups  # path on your host machine

cd $DB_BACKUPS_TOOL_PATH
echo "LOCAL_PATH=$LOCAL_PATH" >> .env

# find and restore backup file for current day (finding in directory $LOCAL_PATH)
docker compose run --rm do restore ${DB_NAME} --from LOCAL --to PG-SERVICE

# restore backup file placed on S3 bucket (fill S3_* specific env in .env file)
docker compose run --rm do restore ${DB_NAME} --from S3 --to PG-SERVICE

# or via docker run:
docker run \
  --volume ${LOCAL_PATH}:/db-backups/backups \
  --network "host" \
  --env-file $(pwd)/.env \
  --rm \
  db-backups \
  restore ${DB_NAME} --from LOCAL --to PG-SERVICE

# find for specific day (filename is formatted like: '2024-02-21-065213.${DB_NAME}.backup.tar.gz')
docker compose run --rm do restore ${DB_NAME} --from LOCAL --to PG-SERVICE --date 2024-02-21
```

Run restore from S3 directory (find file for current day):
```shell
DB_BACKUPS_TOOL_PATH="/opt/db-backups"
DB_NAME="podcast_service"
CONTAINER_NAME="postgres-12"

LOCAL_PATH=$(pwd)/backups  # path on your host machine

cd $DB_BACKUPS_TOOL_PATH
echo "LOCAL_PATH=$LOCAL_PATH" >> .env

# find and restore backup file for current day (finding in directory $LOCAL_PATH)
docker compose run --rm do restore ${DB_NAME} --from LOCAL --to PG-SERVICE

# or via docker run:
docker run \
  --volume ${LOCAL_PATH}:/db-backups/backups \
  --network "host" \
  --env-file $(pwd)/.env \
  --rm \
  db-backups \
  restore ${DB_NAME} --from LOCAL --to PG-SERVICE

# find for specific day (filename is formatted like: '2024-02-21-065213.${DB_NAME}.backup.tar.gz')
docker compose run --rm do restore ${DB_NAME} --from LOCAL --to PG-SERVICE --date 2024-02-21
```

## Installation and usage (native run)

### Pull last version
```shell
export DB_BACKUPS_TOOL_PATH="/opt/db-backups"
git clone [repository_url] "${DB_BACKUPS_TOOL_PATH}"
```

### ENV configuration
```shell
cd $DB_BACKUPS_TOOL_PATH
cp .env.template .env
nano .env  # set required variables
```



### Usage

### Run manually (backup)
To get started right away (from docker container, encrypt and upload to S3):
```shell script
cd "${DB_BACKUPS_TOOL_PATH}"
DB_NAME="podcast_service"
CONTAINER_NAME="postgres-12"
poetry run backup ${DB_NAME} --from PG-CONTAINER -c ${CONTAINER_NAME} --to LOCAL --encrypt
```
### Run manually (restore)
To run backup (from file in local directory, decrypt and apply to postgres (as a service)):
```shell script
cd "${DB_BACKUPS_TOOL_PATH}"
DB_NAME="podcast_service"
CONTAINER_NAME="postgres-12"
poetry run restore ${DB_NAME} --from LOCAL --to PG-SERVICE -c ${CONTAINER_NAME}
```

### Run backup via docker (local backup only)
To store backup on host's directory
```shell script
# TODO: fix commands
docker-compose up --build
docker-compose run --volume <YOUR_DIR>:/app/backups backup python -m src.run backup <DB_NAME> --handler postgres --local /app/backups 
```

### Run postgres backup via docker (s3 backup)
To run backup process from docker with db-backup service
```shell script
docker-compose up --build
docker-compose run backup python -m src.run backup <DB_NAME> --handler postgres --s3
```

### Run postgres backup via docker (s3 backup) + encrypt
To run backup process from docker with db-backup service
```shell
echo "ENCRYPT_PASS=<YOUR_SECRET_KEY>" > .env
docker-compose up --build
docker-compose run backup python -m src.run backup <DB_NAME> -h postgres -s3 --encrypt --encrypt-pass env:ENCRYPT_PASS
```

### Command line options (backup)
```text
Usage: backup [OPTIONS] DB_NAME

  Backups DB from specific container (or service) and uploads it to S3 and/or
  to the local storage.

Options:
  --from BACKUP_HANDLER           Handler, that will be used for backup
                                  ('MYSQL', 'PG-SERVICE', 'PG-CONTAINER')
                                  [required]
  -c, --container DOCKER_CONTAINER
                                  Name of docker container which should be
                                  used for getting dump.
  --to DESTINATION                Comma separated list of destination places
                                  (result backup file will be moved to).
                                  Possible values: ('S3', 'LOCAL')  [required]
  -e, --encrypt                   Turn ON backup's encryption (with openssl)
  -v, --verbose                   Enables verbose mode.
  --no-colors                     Disables colorized output.
  --help                          Show this message and exit.
```

### Command line options (restore)
```text
Usage: restore [OPTIONS] DB_NAME

  Prepares provided file (placed on S3 or local storage) and restore it to
  specified DB

Options:
  --from BACKUP_SOURCE            Source of backup file, that will be used for
                                  downloading/copying: ('S3', 'LOCAL')
                                  [required]
  --to RESTORE_HANDLER            Handler, that will be used for restore:
                                  ('MYSQL', 'PG-SERVICE', 'PG-CONTAINER')
                                  [required]
  -c, --docker-container CONTAINER_NAME
                                  Name of docker container which should be
                                  used for getting dump.
  --date BACKUP_DATE              Specific date (in ISO format: %Y-%m-%d) for
                                  restoring backup (default: 2024-02-11)
  -v, --verbose                   Enables verbose mode.
  --no-colors                     Disables colorized output.
  --help                          Show this message and exit.
```


### ENV configuration
```shell script
cd <path_to_project>
cp .env.template .env
nano .env  # set required variables
```

### RUN configuration (periodical running) 
```shell script
cd <path_to_project>
cp run.sh.template run.sh
chmod +x run.sh
nano run.sh  # add your custom runs
crontab -e
0 2 * * * cd <path_to_project> && /.run.sh >> /var/log/db_backups.cron.log 2>&1 # every night at 02:00
```

### Get help
```shell script
cd <path_to_project>
pipenv run python -m src.run backup --help
```


### Environments

Environment variables can be set manually or by updating `<path_to_project>/.env` file. 
Note, variables from this file can't rewrite variables which are set manually 


| ARGUMENT                |                DESCRIPTION                |         EXAMPLE         |          DEFAULT           |
|:------------------------|:-----------------------------------------:|:-----------------------:|:--------------------------:|
| LOG_LEVEL               |           Current logging level           |          DEBUG          |            INFO            |    
| LOG_DIR                 |      Default directory for log files      |     /home/user/logs     |  <path_to_project>/logs/   |
| SENTRY_DSN              |     Sentry DSN (exception streaming)      | 123:456@setry.site.ru/1 |                            |
| MYSQL_HOST              | It is used for connecting to MySQL server |        localhost        |         localhost          |
| MYSQL_PORT              | It is used for connecting to MySQL server |          3306           |            3306            |
| MYSQL_USER              | It is used for connecting to MySQL server |          user           |            root            |
| MYSQL_PASSWORD          | It is used for connecting to MySQL server |        password         |          password          |
| PG_HOST                 |  It is used for connecting to PG server   |        localhost        |         localhost          |
| PG_PORT                 |  It is used for connecting to PG server   |          5432           |            5432            |
| PG_DUMP_BIN             |   'pg_dump' or link to pg_dump's binary   |         pg_dump         |          pg_dump           |
| PG_USER                 |  It is used for connecting to PG server   |          user           |          postgres          |
| PG_PASSWORD             |  It is used for connecting to PG server   |        password         |          password          |
| S3_STORAGE_URL          |        URL to S3-like file storage        | https://storage.s3.net/ |                            |
| S3_ACCESS_KEY_ID        |         Public key to S3 storage          |                         |                            |
| S3_SECRET_ACCESS_KEY    |         Secret key to S3 storage          |                         |                            |
| S3_BUCKET_NAME          |                 S3 bucket                 |                         |                            |
| S3_PATH                 |         S3 dir for created backup         |                         |                            |
| LOCAL_PATH              |          local dir saving backup          |                         |                            |

* * *

## License

This product is released under the MIT license. See LICENSE for details.
