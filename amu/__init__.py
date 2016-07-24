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

import amu.views, amu.forms, amu.model

