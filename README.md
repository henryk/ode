# ode does everything

## Quickstart

```
# Download and install Python 2.7 >= 2.7.9
# e.g. using http://stackoverflow.com/a/11301911/899574
virtualenv -p /path/to/python2.7 venv
. venv/bin/activate
pip install -r requirements.txt
cp settings.example.py settings.py
# Edit and change instance/settings.py
mkdir instance
cp settings.example.py instance/settings.py
# Now change the file with your favourite editor
```

For usage with gunicorn do

```
pip install gunicorn
gunicorn -w 4 --preload run_ode:app
```

isi needs a rabbitmq instance and running celery workers

```
sudo apt-get install rabbitmq-server
celery -A ode worker -l info
```

## Quicker start

A supervisor configuration file is provided, so starting gunicorn and celery is as simple as

```
supervisord
```

## Contents

### amu manages users

### isi sends invitations