from __future__ import absolute_import

from functools import wraps

from flask import Flask, g, current_app, session, redirect, url_for, request, render_template

from flask_bootstrap import Bootstrap
from flask_session import Session
from flask_ldapconn import LDAPConn

bs = Bootstrap()
_s = Session()
ldap = LDAPConn()


def create_app(configuration="ode.config.Config", **kwargs):
	app = Flask(__name__)

	app.config.from_object(configuration)
	app.config.from_envvar('ODE_SETTINGS', silent=True)
	app.config.update(kwargs)

	bs.init_app(app)
	_s.init_app(app)
	ldap.init_app(app)

	app.add_url_rule('/', 'root', root)
	app.add_url_rule('/login', 'login', login, methods=['GET', 'POST'])
	app.add_url_rule('/logout', 'logout', logout)

	from ode.model import initialize as model_init
	model_init(app)

	from ode.blueprints import amu
	app.register_blueprint(amu.blueprint, url_prefix='/amu')

	import ode.session_box
	ode.session_box.init_box(app)

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
				flash("Invalid credentials", category="danger")
				logout()
				return redirect(url_for('.login', next=request.url))  ## FIXME: Validate or remove, don't want open redirects
			determine_admin_status()
			if needs_admin and not session["is_admin"]:
				abort(404)
			return f(*args, **kwargs)
		else:
			return redirect(url_for('.login', next=request.url))
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
	if session["is_admin"]:
		return redirect(url_for('amu.users'))
	else:
		return redirect(url_for('amu.self'))

def login():
	from ode.forms import LoginForm
	form = LoginForm()
	if request.method == 'POST' and form.validate_on_submit():
		session['username'] = form.username.data
		session_box.store_boxed("password", form.password.data)
		session.modified = True
		return redirect(request.args.get("next", url_for('.root')))
	return render_template("login.html", form=form)

def logout():
	session.pop("password", None)
	session.pop("is_admin", None)
	session.modified = True
	return redirect(url_for(".root"))



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