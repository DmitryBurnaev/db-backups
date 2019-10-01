## Project for backup databases to local directory and to Yandex disk (optional)

### Preparing to install
```shell script
sudo pip install pipenv
```

### Installation
```shell script
git clone [repository_url] <path_to_project>
cd <project_dir>
pipenv install

cp src/settings_local.py.template src/settings_local.py
nano src/settings_local.py # modify needed variables
```

### ENV configuration
```shell script
cd <path_to_project>
cp .env.template .env
nano .env  # set requiered variables
```

### RUN configuration (periodical running) 
```shell script
cd <path_to_project>
cp run.sh.template run.sh
chmod a+x run.sh
nano run.sh  # add your custom runs
crontab -e
0 0 * * * admin <path_to_project>/.run.sh  # every night at 00:00
```

### RUN manually (from docker container and upload to YandexDisc)
```shell script
cd <path_to_project>
pipenv run python -m src.run <DB_NAME> --handler docker_postgres --container postgres --yandex
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

| ARGUMENT | DESCRIPTION | EXAMPLE | DEFAULT |
|:----------------- |:-----------------------------------------:|:-----------------------:|:-------------------------:|
| LOG_LEVEL         | Current logging level                     | DEBUG                   | INFO                      |    
| YANDEX_TOKEN      | Token for uploading backup to YandexDisc  | 12312312312312312312    |                           |
| YANDEX_BACKUP_DIR | Default directory in your YandexDisc      | /project_backups/       | /backups/                 |
| LOCAL_BACKUP_DIR  | Default directory for local backup        | /home/user/backups      | <path_to_project>/backups/|
| LOG_DIR           | Default directory for log files           | /home/user/logs         | <path_to_project>/logs/   |
| SENTRY_DSN        | Sentry DSN (exception streaming)          | 123:456@setry.site.ru/1 |                           |
| MYSQL_HOST        | It is used for connecting to MySQL server | localhost               | localhost                 |
| MYSQL_PORT        | It is used for connecting to MySQL server | 3306                    | 3306                      |
| MYSQL_USER        | It is used for connecting to MySQL server | user                    | root                      |
| MYSQL_PASSWORD    | It is used for connecting to MySQL server | password                | password                  |
| PG_HOST           | It is used for connecting to PG server    | localhost               | localhost                 |
| PG_PORT           | It is used for connecting to PG server    | 5432                    | 5432                      |
| PG_VERSION        | It is used for connecting to PG server    | 9.6.5                   | 9.6.5                     |
| PG_USER           | It is used for connecting to PG server    | user                    | postgres                  |
| PG_PASSWORD       | It is used for connecting to PG server    | password                | password                  |


* * *

## License

This product is released under the MIT license. See LICENSE for details.
