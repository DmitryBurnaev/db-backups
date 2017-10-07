# Simple backup db to yandex-disk

Project for backup databases (MySQL and PostgresSQL) on Yandex disk 

### how to install
```bash
git clone [repository_url]
cd <project_dir>
python3 -m venv venv
pip install -r requiriments.txt
cp src/settings_local.py.template src/settings_local.py
nano src/settings_local.py # modify needed variables
```

### how to run 
```bash
<path_to_project>/venv/python  <path_to_project>/src/run.py
```

### periodic runner:
```bash
crontab -e
0 0 * * * admin <path_to_project>/venv/python  <path_to_project>/src/run.py
```
