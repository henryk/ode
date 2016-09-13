from __future__ import absolute_import

from functools import wraps

from flask import Flask, g, current_app, session, redirect, url_for, request, render_template, abort, Markup

from flask_bootstrap import Bootstrap
from flask_session import Session
from flask_ldapconn import LDAPConn
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from celery import Celery
from flask_migrate import Migrate, MigrateCommand
from itsdangerous import Signer
from flask_mail import Mail
from flask_babel import Babel
from flask_babel import _, format_datetime

import pytz, os, os.path

try: 
	from flask_debugtoolbar import DebugToolbarExtension
	debug_toolbar = DebugToolbarExtension()
except ImportError:
	debug_toolbar = None

from flask_nav import Nav, register_renderer

bs = Bootstrap()
_s = Session()
ldap = LDAPConn()
nav = Nav()
migrate = Migrate()
db = SQLAlchemy(metadata=MetaData(naming_convention={
	"ix": 'ix_%(column_0_label)s',
	"uq": "uq_%(table_name)s_%(column_0_name)s",
	"ck": "ck_%(table_name)s_%(constraint_name)s",
	"fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
	"pk": "pk_%(table_name)s"
}))
cel = Celery(__name__)
mailer = Mail()
babel = Babel()


def create_app(configuration="ode.config.Config", **kwargs):
	app = Flask(__name__)

	app.config.from_object(configuration)
	app.instance_path = os.environ.get("ODE_INSTANCE", app.instance_path)
	app.config.from_pyfile( os.path.join(app.instance_path, "settings.py"), silent=True )
	app.config.from_envvar('ODE_SETTINGS', silent=True)
	app.config.update(kwargs)

	if debug_toolbar:
		debug_toolbar.init_app(app)

	bs.init_app(app)
	_s.init_app(app)
	ldap.init_app(app)
	nav.init_app(app)
	db.init_app(app)
	migrate.init_app(app, db)
	mailer.init_app(app)
	babel.init_app(app)

	cel.conf.update(app.config)

	app.add_url_rule('/', 'root', root)
	app.add_url_rule('/login', 'login', login, methods=['GET', 'POST'])
	app.add_url_rule('/logout', 'logout', logout)

	app.add_url_rule('/<lang_code>/', 'root', root)
	app.add_url_rule('/<lang_code>/login', 'login', login, methods=['GET', 'POST'])
	app.add_url_rule('/<lang_code>/logout', 'logout', logout)

	@app.before_request
	def set_tz():
		g.timezone = pytz.timezone(current_app.config.get("DISPLAY_TIMEZONE", "UTF"))

	@app.template_filter()
	def strfdatetime(value, format="%Y-%m-%d %H:%M %Z"):
		if not value:
			return ""
		
		return pytz.utc.localize(value).astimezone(g.timezone).strftime(format)

	@app.context_processor
	def add_js_i18n():
		def get_js_locale_data():
			try:
				with current_app.open_resource('static/translations/' + get_locale() + '.js') as f:
					return Markup(f.read().decode("utf-8"))
			except IOError:
				return Markup("{}")
		return dict(get_js_locale_data=get_js_locale_data)


	# Based on http://damyanon.net/flask-series-internationalization/
	@app.url_defaults
	def set_language_code(endpoint, values):
		if 'lang_code' in values or not g.get('lang_code', None):
			return
		if current_app.url_map.is_endpoint_expecting(endpoint, 'lang_code'):
			values['lang_code'] = g.lang_code

	@app.url_value_preprocessor
	def get_lang_code(endpoint, values):
		if values is not None:
			g.lang_code = values.pop('lang_code', None)

	@app.before_request
	def ensure_lang_support():
		lang_code = g.get('lang_code', None)
		if lang_code and lang_code not in current_app.config['SUPPORTED_LANGUAGES'].keys():
			return abort(404)

	from ode.navigation import ODENavbarRenderer
	register_renderer(app, 'ode_navbar', ODENavbarRenderer)

	from ode.model import initialize as model_init
	model_init(app)

	from ode.blueprints import amu
	app.register_blueprint(amu.blueprint, url_prefix='/amu')
	app.register_blueprint(amu.blueprint, url_prefix='/<lang_code>/amu')

	from ode.blueprints import isi
	app.register_blueprint(isi.blueprint, url_prefix='/isi')
	app.register_blueprint(isi.blueprint, url_prefix='/<lang_code>/isi')

	app.config["ODE_MODULES"] = [
		('ODE', '', 'root'),
		('AMU', 'AMU Manages Users', 'amu.root'),
		('ISI', 'ISI Sends Invitations', 'isi.root'),
	]

	import ode.session_box
	ode.session_box.init_box(app)

	app.wsgi_app = ReverseProxied(app.wsgi_app)

	return app

def create_signer(secret_key=None, salt=None):
	if secret_key is None:
		secret_key = current_app.secret_key
	return Signer(secret_key, salt=salt)

def config_get(key, default=Ellipsis, config=None, **kwargs):
	if config is None:
		config = current_app.config
	d = dict(config.items())
	d.update(kwargs)
	if default is Ellipsis:
		return d[key] % d
	else:
		return d.get(key, default) % d

def _connect_and_load_ldap(password):
	done = False
	ldc = current_app.extensions.get('ldap_conn')

	from ldap3 import LDAPBindError
	from ode.model import User

	if "binddn" in session:
		try: 
			# First, try the stored bind dn
			g.ldap_conn = ldc.connect(session['binddn'], password)
			done = True
		except LDAPBindError:
			# If that didn't work, invalidate binddn cache and fall back to regular behaviour
			del session["binddn"]
			session.modified = True

	if not done:
		userdn = config_get("ODE_USER_DN", username=session["username"])
		try: 
			# First try the ODE_USER_DN format
			g.ldap_conn = ldc.connect(userdn, password)
			session["binddn"] = userdn
			session.modified = True
		except LDAPBindError as e:
			if current_app.config["ODE_ALLOW_DIRECT_DN"]:
				try: 
					# If that didn't work, try the "username" directly
					g.ldap_conn = ldc.connect(session["username"], password)
					session["binddn"] = session["username"]
					session.modified = True
				except LDAPBindError:
					# That didn't work either.
					current_app.logger.info("Couldn't login with either %s or %s", userdn, session["username"])
					raise
			else:
				# Retry not allowed by ODE_ALLOW_DIRECT_DN, re-raise directly
				raise

	g.ldap_user = User.query.filter("userid: %s" % session["username"]).first()
	if not g.ldap_user:
		# Fallback case
		g.ldap_user = User(name="Unknown user")

def determine_admin_status():
	"""Try to query a group. If that succeeds -> Admin, otherwise normal user. Cache the result in the session."""
	if "is_admin" in session:
		return
	else:
		from ode.model import Group

		group = Group.query.first()
		session["is_admin"] = not not group
		session.modified = True

def _login_required_int(needs_admin, f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		from ldap3 import LDAPBindError

		password = session_box.retrieve_unboxed("password", None)
		if "username" in session and password is not None:
			try:
				_connect_and_load_ldap(password)
			except LDAPBindError:
				flash( _("Invalid credentials"), category="danger")
				logout()
				return redirect(url_for('login', next=request.url))  ## FIXME: Validate or remove, don't want open redirects
			determine_admin_status()
			if needs_admin and not session["is_admin"]:
				abort(404)
			return f(*args, **kwargs)
		else:
			return redirect(url_for('login', next=request.url))
	return decorated_function

def login_required(argument):
	if hasattr(argument, "__call__"):
		return _login_required_int(True, argument)
	else:
		def decorator(f):
			return _login_required_int(argument, f)
		return decorator



@login_required(False)
def root():
	return redirect(url_for('amu.root'))

def login():
	from ode.forms import LoginForm
	form = LoginForm()
	if request.method == 'POST' and form.validate_on_submit():
		session['username'] = form.username.data
		session_box.store_boxed("password", form.password.data)
		session.modified = True
		return redirect(request.args.get("next", url_for('root')))
	return render_template("login.html", form=form)

def logout():
	session.pop("password", None)
	session.pop("is_admin", None)
	session.modified = True
	return redirect(url_for("root"))


@babel.localeselector
def get_locale():
	# Priority: URL, (User preferences), browser settings, default
	result = g.get('lang_code', None)

	if not result:
		result = request.accept_languages.best_match(current_app.config['SUPPORTED_LANGUAGES'].keys())

	if not result:
		result = current_app.config['BABEL_DEFAULT_LOCALE']

	return result

@babel.timezoneselector
def get_timezone():
	return current_app.config["DISPLAY_TIMEZONE"]

def this_page_in(lang_code):
	try:
		return url_for(request.url_rule.endpoint, lang_code=lang_code, **request.view_args)
	except:
		current_app.logger.exception("Something went wrong, defaulting")
	return "/" + lang_code + "/"


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
