from __future__ import absolute_import

from ode import create_app
from celery import Celery

import pytz

from flask import g, current_app

def make_celery(app):
	celery = Celery(app.import_name)
	celery.conf.update(app.config)
	TaskBase = celery.Task
	class ContextTask(TaskBase):
		abstract = True
		def __call__(self, *args, **kwargs):
			with app.app_context():
				ldc = current_app.extensions.get('ldap_conn')
				g.ldap_conn = ldc.connect(current_app.config["ODE_BIND_DN"], current_app.config["ODE_BIND_PW"])
				current_app.extensions.get('babel').locale_selector_func = lambda : None
				current_app.extensions.get('babel').timezone_selector_func = lambda : None
				g.timezone = pytz.timezone(current_app.config.get("DISPLAY_TIMEZONE", "UTC"))
				return TaskBase.__call__(self, *args, **kwargs)
	celery.Task = ContextTask
	return celery

celery = make_celery(create_app())

if __name__ == '__main__':
	celery.start()
