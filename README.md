# ode does everything

## Quickstart

```
# Download and install Python 2.7 >= 2.7.9
# e.g. using http://stackoverflow.com/a/11301911/899574
virtualenv -p /path/to/python2.7 venv
. venv/bin/activate
pip install -r requirements.txt
cp settings.example.py settings.py
# Edit and change settings.py
export ODE_SETTINGS=$(pwd)/settings.py
```

For usage with gunicorn do

```
pip install gunicorn
gunicorn -w 4 --preload run_ode:app
```

isi needs a rabbitmq instance and running celery workers

```
sudo apt-get install rabbitmq-server
export ODE_SETTINGS=$(pwd)/settings.py
celery -A ode worker -l info
```

## Quicker start

A supervisor configuration file is provided, so starting gunicorn and celery is as simple as

```
export ODE_SETTINGS=$(pwd)/settings.py
supervisord
```

## Contents

### amu manages users

### isi sends invitations