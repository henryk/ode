from __future__ import absolute_import

from kombu import Exchange, Queue
from datetime import timedelta

class Config(object):
	DEBUG = False
	TESTING = False
	BOOTSTRAP_SERVE_LOCAL = True
	SECRET_KEY = '60Tfy+Oa35oorZ5XpI6+dTwinCgTRupSzYdqZjIj/JE='
	PERMANENT_SESSION_LIFETIME = 60*60*24*365*10
	SESSION_TYPE = 'filesystem'
	SESSION_FILE_DIR = './sessions'
	SESSION_COOKIE_NAME = 'ode_session'
	SESSION_COOKIE_HTTPONLY = True
	SESSION_USE_SIGNER = True

	MAILING_LIST_MEMBER_USER_TEMPLATE = r'^ldap:///(?P<user_dn>[^?]*?)$'
	MAILING_LIST_MEMBER_GROUP_TEMPLATE = r'^ldap:///%(user_base)s\?\?one\?\(&\(objectClass=inetOrgPerson\)\(memberOf=(?P<group_dn>.*?)\)\)$'

	SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
	SQLALCHEMY_TRACK_MODIFICATIONS = False

	CELERY_TASK_RESULT_EXPIRES=3600
	CELERY_TASK_SERIALIZER='pickle'
	CELERY_ACCEPT_CONTENT=['pickle']
	CELERY_RESULT_SERIALIZER='pickle'
	CELERY_ENABLE_UTC=True

	CELERY_DEFAULT_QUEUE = 'ode'
	CELERY_QUEUES = (
		Queue('ode', Exchange('ode'), routing_key='ode'),
	)

	CELERYBEAT_SCHEDULE = {
	'refresh-isi-1minute': {
		'task': 'ode.blueprints.isi.tasks.refresh_1minute',
		'schedule': timedelta(seconds=60),
		'args': (),
	},
}


class DevelopmentConfig(Config):
	DEBUG = True

class TestingConfig(Config):
	TESTING = True
