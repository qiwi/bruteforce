# Bruteforce

A tool used to test the vulnerability of database passwords. [Hashcat](https://hashcat.net/hashcat/) is used as a password guessing program.

## Requirements
* Python 3.7.x
* PostgreSQL 11.x
* RabbitMQ
* Hashcat

## Can grab from
* PostgreSQL
* MSSQL
* Oracle

## Usage
### 1. Install and configure
**1.1** Clone repo, create virtual environment, install requirements, create log dir
```shell
cd BASE_DIR
git clone https://github.com/qiwi/bruteforce.git
cd bruteforce
python3.7 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
mkdir /var/log/bruteforce
```
**1.2** Create file BASE_DIR/bruteforce/bruteforce/settings/prod.py based on BASE_DIR/bruteforce/bruteforce/settings/prod_template.py

Fill empty fields

**1.3** Migrate
```shell
python3.7 manage.py migrate
```
**1.4** Collect static files
```shell
python3.7 manage.py collectstatic 
```
**1.5** Start django
```shell
python3.7 manage.py runserver
```
### 2. Run celery and flower
**2.1** Run worker and beat
```shell
celery -A bruteforce beat --scheduler django_celery_beat.schedulers:DatabaseScheduler
```
```shell
celery -A bruteforce worker
```
**2.2** Run flower for monitoring tasks
```shell
flower -A bruteforce
```

### 3. Install hashcat (macOS)
**3.1** Clone, build and install hashcat
```shell
git clone https://github.com/hashcat/hashcat.git
cd hashcat
make
sudo make install
```

**3.2** Make sure hashcat path is correct in crypto/hashcat.py
```shell
: which hashcat
/usr/bin/hashcat
```
```python
class Hashcat:
    def __init__(self):
        self.hashcat = '/usr/bin/hashcat'
```


### 4. Create and grant user accounts

Create local user accounts in databases and add credentials to prod.py CONN_CREDENTIALS. If you have unique credentials for specific database, add it to prod.py CUSTOM_CREDENTIALS like in examle from prod_template.py.

Permissions:

* PostgreSQL
```sql
select for pg_authid
```
* Oracle
```sql
select for sys.user$, dba_users
``` 
* MSSQL
```sql
select for sys.sql_logins/sys.syslogins
CONTROL SERVER
```

### 5. Create first tasks
**5.1** Open project's browser page

**5.2** Click "Dictionaries" and add dictionary record with name and path

**5.3** Click "Databases" and add database record with host and db type

**5.4** Click "Periodic tasks: ⁣⁣⁣Dictionary" and add task with new dictionary (5.2) and database (5.3) arguments

**5.5** Run new task

### 6. Results
You can see results in "Checked hashes" page

### Other tasks
Magnifier - counts errors and words in dictionaries

Change checker - check hash relevance in databases

## License
Distributed under the [MIT License](./LICENCE).
