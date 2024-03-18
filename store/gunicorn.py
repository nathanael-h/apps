#!/usr/bin/env python3

from pathlib import Path

install_dir = Path(__file__).resolve().parent
command = f"{install_dir}/venv/bin/gunicorn"
pythonpath = str(install_dir)
workers = 4
user = "appstore"
bind = f"unix:{install_dir}/sock"
pid = "/run/gunicorn/appstore-pid"
errorlog = "/var/log/appstore/error.log"
accesslog = "/var/log/appstore/access.log"
access_log_format = \
    '%({X-Real-IP}i)s %({X-Forwarded-For}i)s %(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
loglevel = "warning"
capture_output = True
