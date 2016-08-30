class Config(object):
	DEBUG = False
	TESTING = False
	BOOTSTRAP_SERVE_LOCAL = True
	SECRET_KEY = '60Tfy+Oa35oorZ5XpI6+dTwinCgTRupSzYdqZjIj/JE='
	PERMANENT_SESSION_LIFETIME = 60*60*24*365*10
	SESSION_TYPE = 'filesystem'
	SESSION_FILE_DIR = './sessions'
	SESSION_COOKIE_NAME = 'amu_session'
	SESSION_COOKIE_HTTPONLY = True
	SESSION_USE_SIGNER = True

	MAILING_LIST_MEMBER_USER_TEMPLATE = r'^ldap:///(?P<user_dn>[^?]*?)$'
	MAILING_LIST_MEMBER_GROUP_TEMPLATE = r'^ldap:///%(user_base)s\?\?one\?\(&\(objectClass=inetOrgPerson\)\(memberOf=(?P<group_dn>.*?)\)\)$'

class DevelopmentConfig(Config):
	DEBUG = True

class TestingConfig(Config):
	TESTING = True
