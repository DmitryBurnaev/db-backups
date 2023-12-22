<h2 align="center">Simple backup databases to local directory and upload S3-storage (optional)</h2>

Allows to back up PG and Mysql databases through their client or docker docker-container.

## Installation and usage
### Installation
*db-backups* requires pipenv
```shell script
sudo pip install pipenv
```

```shell script
git clone [repository_url] <path_to_project>
cd <path_to_project>
pipenv install

cp .env.template .env
nano .env # modify needed variables
```

### Usage

### Run manually 
To get started right away (from docker container and upload to YandexDisc):
```shell script
cd <path_to_project>
pipenv run python -m src.run <DB_NAME> --handler docker_postgres --container postgres --s3
```

### Run postgres backup via docker (local backup only)
To store backup on host's directory
```shell script
docker-compose up --build
docker-compose run --volume <YOUR_DIR>:/app/backups backup python -m src.run <DB_NAME> --handler postgres --local /app/backups 
```

### Run postgres backup via docker (s3 backup)
To run backup process from docker with db-backup service
```shell script
docker-compose up --build
docker-compose run backup python -m src.run <DB_NAME> --handler postgres --s3
```

### Run postgres backup via docker (s3 backup) + encrypt
To run backup process from docker with db-backup service
```shell
echo "ENCRYPT_PASS=<YOUR_SECRET_KEY>" > .env
docker-compose up --build
docker-compose run backup python -m src.run <DB_NAME> --handler postgres --s3 --encrypt --encrypt-pass env:ENCRYPT_PASS
```

### Command line options
```text
usage: run.py [-h] --handler BACKUP_HANDLER [--docker-container CONTAINER_NAME] [--s3] [--local LOCAL] [--encrypt] [--encrypt-pass ENCRYPT_PASS] DB_NAME

positional arguments:
  DB_NAME               Database's name for backup

options:
  -h, --help            show this help message and exit
  --handler BACKUP_HANDLER
                        Handler, which will be used for backup ('mysql', 'postgres', 'docker_postgres')
  --docker-container CONTAINER_NAME
                        Name of docker container which should be used for getting dump. Required for using docker_* handler
  --s3                  Send backup to S3-like storage (required additional env variables)
  --local LOCAL         Local directory for saving backups
  --encrypt             Turn ON backup's encryption (with openssl)
  --encrypt-pass ENCRYPT_PASS
                        Openssl config to provide source of encryption pass: ('env:var_name', 'file:path_name', 'fd:number') | short-details: {'env:var_name': 'get the password from an environment
                        variable', 'file:path_name': 'get the password from the first line of the file at location', 'fd:number': 'get the password from the file descriptor number'}
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
pipenv run python -m src.run --help
```


### Environments

Environment variables can be set manually or by updating `<path_to_project>/.env` file. 
Note, variables from this file can't rewrite variables which are set manually 


| ARGUMENT             |                DESCRIPTION                |         EXAMPLE         |           DEFAULT          |
|:---------------------|:-----------------------------------------:|:-----------------------:|:--------------------------:|
| LOG_LEVEL            |           Current logging level           |          DEBUG          |            INFO            |    
| LOG_DIR              |      Default directory for log files      |     /home/user/logs     |  <path_to_project>/logs/   |
| SENTRY_DSN           |     Sentry DSN (exception streaming)      | 123:456@setry.site.ru/1 |                            |
| MYSQL_HOST           | It is used for connecting to MySQL server |        localhost        |         localhost          |
| MYSQL_PORT           | It is used for connecting to MySQL server |          3306           |            3306            |
| MYSQL_USER           | It is used for connecting to MySQL server |          user           |            root            |
| MYSQL_PASSWORD       | It is used for connecting to MySQL server |        password         |          password          |
| PG_HOST              |  It is used for connecting to PG server   |        localhost        |         localhost          |
| PG_PORT              |  It is used for connecting to PG server   |          5432           |            5432            |
| PG_DUMP_BIN          |   'pg_dump' or link to pg_dump's binary   |         pg_dump         |          pg_dump           |
| PG_USER              |  It is used for connecting to PG server   |          user           |          postgres          |
| PG_PASSWORD          |  It is used for connecting to PG server   |        password         |          password          |
| S3_STORAGE_URL       |        URL to S3-like file storage        | https://storage.s3.net/ |                            |
| S3_ACCESS_KEY_ID     |         Public key to S3 storage          |                         |                            |
| S3_SECRET_ACCESS_KEY |         Secret key to S3 storage          |                         |                            |
| S3_BUCKET_NAME       |                 S3 bucket                 |                         |                            |
| S3_DST_PATH          |      S3 dir for generated RSS feeds       |          files          |                            |

* * *

## License

This product is released under the MIT license. See LICENSE for details.
