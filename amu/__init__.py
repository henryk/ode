from flask import Flask, g, current_app

from flask_bootstrap import Bootstrap
from flask_session import Session
from flask_ldapconn import LDAPConn

from flask_nav import Nav, register_renderer


bs = Bootstrap()
_s = Session()
ldap = LDAPConn()

nav = Nav()

def create_app(configuration="amu.config.DevelopmentConfig", **kwargs):
    app = Flask(__name__)

    app.config.from_object(configuration)
    app.config.from_envvar('AMU_SETTINGS', silent=True)
    app.config.update(kwargs)

    bs.init_app(app)
    _s.init_app(app)
    ldap.init_app(app)
    nav.init_app(app)

    from amu.views import views, CustomRenderer
    app.register_blueprint(views)
    register_renderer(app, 'custom', CustomRenderer)

    from amu.model import initialize as model_init
    model_init(app)

    import amu.session_box
    amu.session_box.init_box(app)

    from amu.mail import mailer
    mailer.init_app(app)

    app.wsgi_app = ReverseProxied(app.wsgi_app)

    return app

def config_get(key, default=Ellipsis, config=None, **kwargs):
	if config is None:
		config = current_app.config
	d = dict(config.items())
	d.update(kwargs)
	if default is Ellipsis:
		return d[key] % d
	else:
		return d.get(key, default) % d

import amu.views, amu.forms, amu.model, amu.mail

# From http://flask.pocoo.org/snippets/35/
class ReverseProxied(object):
	'''Wrap the application in this middleware and configure the 
	front-end server to add these headers, to let you quietly bind 
	this to a URL other than / and to an HTTP scheme that is 
	different than what is used locally.

	In nginx:
	location /myprefix {
		proxy_pass http://192.168.0.1:5001;
		proxy_set_header Host $host;
		proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
		proxy_set_header X-Scheme $scheme;
		proxy_set_header X-Script-Name /myprefix;
		}

	:param app: the WSGI application
	'''
	def __init__(self, app):
		self.app = app

	def __call__(self, environ, start_response):
		script_name = environ.get('HTTP_X_SCRIPT_NAME', '')
		if script_name:
			environ['SCRIPT_NAME'] = script_name
			path_info = environ['PATH_INFO']
			if path_info.startswith(script_name):
				environ['PATH_INFO'] = path_info[len(script_name):]

		scheme = environ.get('HTTP_X_SCHEME', '')
		if scheme:
			environ['wsgi.url_scheme'] = scheme
		return self.app(environ, start_response)
