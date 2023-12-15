<h2 align="center">Simple backup databases to local directory and Yandex disk (optional)</h2>

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
pipenv run python -m src.run <DB_NAME> --handler docker_postgres --container postgres --yandex
```

### Run postgres backup via docker (local backup only)
To store backup on host's directory
```shell script
docker-compose up --build
docker-compose run --volume <YOUR_DIR>:/backups/backups backup python -m src.run <DB_NAME> --handler postgres 
```

### Run postgres backup via docker (s3 backup)
To run backup process from docker with db-backup service
```shell script
docker-compose up --build
docker-compose run backup python -m src.run <DB_NAME> --handler postgres  --s3
```

### Command line options
```text
usage: run.py [-h] [--handler BACKUP_HANDLER] [--container CONTAINER]
              [--yandex] [--yandex_directory YANDEX_DIRECTORY]
              [--local_directory LOCAL_DIRECTORY]
              Database Name

positional arguments:
  Database Name         Database name for backup

optional arguments:
  -h, --help            show this help message and exit
  --handler BACKUP_HANDLER
                        Required handler for backup (['mysql', 'postgres',
                        'docker_postgres'])
  --container CONTAINER
                        If using docker_* handler. You should define db-source
                        container
  --yandex              Send backup to YandexDisk
  --yandex_directory YANDEX_DIRECTORY
                        If using --yandex, you can define this attribute
  --s3                  Send backup to S3 storage                        
  --local_directory LOCAL_DIRECTORY
                        Local directory for saving backups

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

#### Obtaining YANDEX_TOKEN
```shell script
# follow the link
https://oauth.yandex.ru/authorize?response_type=token&client_id=<client-id>
```

| ARGUMENT             |                DESCRIPTION                |         EXAMPLE         |           DEFAULT          |
|:---------------------|:-----------------------------------------:|:-----------------------:|:--------------------------:|
| LOG_LEVEL            |           Current logging level           |          DEBUG          |            INFO            |    
| YANDEX_TOKEN         | Token for uploading backup to YandexDisc  |  12312312312312312312   |                            |
| YANDEX_BACKUP_DIR    |   Default directory in your YandexDisc    |    /project_backups/    |         /backups/          |
| LOCAL_BACKUP_DIR     |    Default directory for local backup     |   /home/user/backups    | <path_to_project>/backups/ |
| LOG_DIR              |      Default directory for log files      |     /home/user/logs     |  <path_to_project>/logs/   |
| SENTRY_DSN           |     Sentry DSN (exception streaming)      | 123:456@setry.site.ru/1 |                            |
| MYSQL_HOST           | It is used for connecting to MySQL server |        localhost        |         localhost          |
| MYSQL_PORT           | It is used for connecting to MySQL server |          3306           |            3306            |
| MYSQL_USER           | It is used for connecting to MySQL server |          user           |            root            |
| MYSQL_PASSWORD       | It is used for connecting to MySQL server |        password         |          password          |
| PG_HOST              |  It is used for connecting to PG server   |        localhost        |         localhost          |
| PG_PORT              |  It is used for connecting to PG server   |          5432           |            5432            |
| PG_DUMP              |   'pg_dump' or link to pg_dump's binary   |         pg_dump         |          pg_dump           |
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
