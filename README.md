<h2 align="center">Simple backup databases to local directory and upload S3-storage (optional)</h2>

Allows to back up PG and Mysql databases through their client or docker docker-container.

## Installation and usage
### Installation
*db-backups* requires pipenv
```shell script
sudo pip install poetry
```

```shell script
git clone [repository_url] <path_to_project>
cd <path_to_project>
poetry install

cp .env.template .env
nano .env # modify needed variables
```

### Usage

### Run manually 
To get started right away (from docker container and upload to YandexDisc):
```shell script
cd <path_to_project>
poetry run backup <DB_NAME> --handler docker_postgres --container postgres --s3
```

### Run postgres backup via docker (local backup only)
To store backup on host's directory
```shell script
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
Usage: python -m src.run backup [OPTIONS] DB_NAME

  Shows file changes in the current working directory.

Options:
  -h, --handler BACKUP_HANDLER    Handler, that will be used for backup
                                  ('mysql', 'postgres', 'docker-postgres')
                                  [required]
  -dc, --docker-container CONTAINER_NAME
                                  Name of docker container which should be
                                  used for getting dump. Required for using
                                  docker_* handler
  -e, --encrypt                   Turn ON backup's encryption (with openssl)
  --encrypt-pass DB_BACKUP_ENCRYPT_PASS
                                  Openssl config to provide source of
                                  encryption pass: ('env:var_name',
                                  'file:path_name', 'fd:number') | see details
                                  in README.md  [default:
                                  env:DB_BACKUP_ENCRYPT_PASS]
  -s3, --copy-s3                  Send backup to S3-like storage (requires
                                  DB_BACKUP_S3_* env vars)
  -l, --copy-local                Store backup locally (requires
                                  DB_BACKUP_LOCAL_PATH env)
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
