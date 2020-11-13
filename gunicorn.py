loglevel = "info"
bind = ["127.0.0.1:8000"]
workers = 4
user = "www-data"
group = "www-data"
chdir = "/var/www/bruteforce"
errorlog = "/var/log/bruteforce/gunicorn.log"
