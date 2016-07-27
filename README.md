# amu manages users

## Quickstart

```
# Download and install Python 2.7 >= 2.7.9
# e.g. using http://stackoverflow.com/a/11301911/899574
virtualenv -p /path/to/python2.7 venv
. venv/bin/activate
pip install -r requirements.txt
cp settings.example.py settings.py
# Edit and change settings.py
export AMU_SETTINGS=$(pwd)/settings.py
```

For usage with gunicorn do

```
pip install gunicorn
gunicorn -w 4 --preload run_amu:app
```
