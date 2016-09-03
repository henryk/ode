from __future__ import absolute_import

from ode import create_app
from celery import Celery

def make_celery(app):
	celery = Celery(app.import_name)
	celery.conf.update(app.config)
	TaskBase = celery.Task
	class ContextTask(TaskBase):
		abstract = True
		def __call__(self, *args, **kwargs):
			with app.app_context():
				return TaskBase.__call__(self, *args, **kwargs)
	celery.Task = ContextTask
	return celery

celery = make_celery(create_app())

if __name__ == '__main__':
	celery.start()
