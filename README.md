<h2 align="center">Simple backup databases to local directory and upload S3-storage (optional)</h2>

Allows to back up PG and Mysql databases through their client or docker docker-container.

## Installation and usage
### Installation
*db-backups* requires pipenv
```shell script
sudo pip install poetry
```

```shell script
export DB_BACKUP_TOOL_PATH="/opt/db-backups"

git clone [repository_url] "${DB_BACKUP_TOOL_PATH}"
cd "${DB_BACKUP_TOOL_PATH}"
poetry install

cp .env.template .env
nano .env # modify required variables
```

### Usage

### Run manually (backup)
To get started right away (from docker container, encrypt and upload to S3):
```shell script
cd "${DB_BACKUP_TOOL_PATH}"
DB_NAME="podcast_service"
CONTAINER_NAME="postgres-12"
poetry run backup ${DB_NAME} --from PG-CONTAINER -c ${CONTAINER_NAME} --to LOCAL --encrypt
```
### Run manually (restore)
To run backup (from file in local directory, decrypt and apply to postgres (as a service)):
```shell script
cd "${DB_BACKUP_TOOL_PATH}"
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


| ARGUMENT                       |                DESCRIPTION                |         EXAMPLE         |          DEFAULT           |
|:-------------------------------|:-----------------------------------------:|:-----------------------:|:--------------------------:|
| DB_BACKUP_LOG_LEVEL            |           Current logging level           |          DEBUG          |            INFO            |    
| DB_BACKUP_LOG_DIR              |      Default directory for log files      |     /home/user/logs     |  <path_to_project>/logs/   |
| DB_BACKUP_SENTRY_DSN           |     Sentry DSN (exception streaming)      | 123:456@setry.site.ru/1 |                            |
| DB_BACKUP_MYSQL_HOST           | It is used for connecting to MySQL server |        localhost        |         localhost          |
| DB_BACKUP_MYSQL_PORT           | It is used for connecting to MySQL server |          3306           |            3306            |
| DB_BACKUP_MYSQL_USER           | It is used for connecting to MySQL server |          user           |            root            |
| DB_BACKUP_MYSQL_PASSWORD       | It is used for connecting to MySQL server |        password         |          password          |
| DB_BACKUP_PG_HOST              |  It is used for connecting to PG server   |        localhost        |         localhost          |
| DB_BACKUP_PG_PORT              |  It is used for connecting to PG server   |          5432           |            5432            |
| DB_BACKUP_PG_DUMP_BIN          |   'pg_dump' or link to pg_dump's binary   |         pg_dump         |          pg_dump           |
| DB_BACKUP_PG_USER              |  It is used for connecting to PG server   |          user           |          postgres          |
| DB_BACKUP_PG_PASSWORD          |  It is used for connecting to PG server   |        password         |          password          |
| DB_BACKUP_S3_STORAGE_URL       |        URL to S3-like file storage        | https://storage.s3.net/ |                            |
| DB_BACKUP_S3_ACCESS_KEY_ID     |         Public key to S3 storage          |                         |                            |
| DB_BACKUP_S3_SECRET_ACCESS_KEY |         Secret key to S3 storage          |                         |                            |
| DB_BACKUP_S3_BUCKET_NAME       |                 S3 bucket                 |                         |                            |
| DB_BACKUP_S3_PATH              |         S3 dir for created backup         |                         |                            |
| DB_BACKUP_LOCAL_PATH           |          local dir saving backup          |                         |                            |

* * *

## License

This product is released under the MIT license. See LICENSE for details.
