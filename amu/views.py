from functools import wraps
from flask import Blueprint, current_app, render_template, request, redirect, url_for, session, g, flash, abort
from flask_nav.elements import Navbar, View, Subgroup
from flask_bootstrap.nav import BootstrapRenderer
from amu import forms, config_get, nav, session_box
from ldap3 import LDAPBindError, LDAPEntryError

from amu.model import User, Group

views = Blueprint('views', __name__)

def connect_and_load_ldap(password):
	done = False
	ldc = current_app.extensions.get('ldap_conn')

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
		userdn = config_get("AMU_USER_DN", username=session["username"])
		try: 
			# First try the AMU_USER_DN format
			g.ldap_conn = ldc.connect(userdn, password)
			session["binddn"] = userdn
			session.modified = True
		except LDAPBindError as e:
			if current_app.config["AMU_ALLOW_DIRECT_DN"]:
				try: 
					# If that didn't work, try the "username" directly
					g.ldap_conn = ldc.connect(session["username"], password)
					session["binddn"] = session["username"]
					session.modified = True
				except LDAPBindError:
					# That didn't work either. For cosmetic purposes, re-raise the first exception
					current_app.logger.info("Couldn't login with either %s or %s", userdn, session["username"])
					raise e
			else:
				# Retry not allowed by AMU_ALLOW_DIRECT_DN, re-raise directly
				raise e

	g.ldap_user = User.query.filter("userid: %s" % session["username"]).first()
	if not g.ldap_user:
		# Fallback case
		g.ldap_user = User(name="Unknown user")

def login_required(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		password = session_box.retrieve_unboxed("password", None)
		if "username" in session and password is not None:
			try:
				connect_and_load_ldap(password)
			except LDAPBindError:
				flash("Invalid credentials", category="danger")
				if "password" in session:
					del session["password"]
				session.modified = True
				return redirect(url_for('.login', next=request.url))  ## FIXME: Validate or remove, don't want open redirects
			return f(*args, **kwargs)
		else:
			return redirect(url_for('.login', next=request.url))
	return decorated_function

class CustomRenderer(BootstrapRenderer):
	# Right-aligns last item
	# Fix to top
	def visit_Navbar(self, node):
		result = super(CustomRenderer, self).visit_Navbar(node)
		div = None
		child = None
		for _ in result.get("div"):
			if "navbar-collapse" in _['class']:
				div = _
				break
		if div:
			import dominate

			for bar in div:
				pass
			for child in bar:
				pass
			if child:
				bar.remove(child)
				rightbar = dominate.tags.ul()
				rightbar['class'] = "nav navbar-nav navbar-right"
				div.add(rightbar)
				rightbar.add(child)

		result['class'] += " navbar-fixed-top"

		return result

@nav.navigation()
def mynavbar():
	e = [
		'AMU',
	]
	if hasattr(g, "ldap_user"):
		e.extend( [
			View('Users', '.users'),
			View('New user', '.new_user'),
			View('Groups', '.groups'),
			Subgroup('Logged in as %s' % g.ldap_user.name,
				View('Log out', '.logout')
			)
		] )
	return Navbar(*e)


@views.route("/")
@login_required
def root():
	return redirect(url_for('.users'))

@views.route("/user/")
@login_required
def users():
	users = User.query.all()
	groups = Group.query.all()
	return render_template('users.html', users=users, groups=groups)

def save_ldap_attributes(form, obj):
	"""Only stores existing LDAP attributes.
	Does not store empty attributes named 'password'.
	Does not change existing attributes named 'userid'.
	Does not change attributes named 'groups'."""
	for name, field in form._fields.items():
		if name == "password" and not field.data: continue
		if name == "userid" and getattr(obj, "userid", None): continue
		if name == "groups": continue

		try:
			if(getattr(obj, name) != field.data):
				setattr(obj, name, field.data)
		except LDAPEntryError:
			continue

@views.route("/user/<string:uid>", methods=['GET','POST'])
@login_required
def user(uid):
	user = User.query.filter("userid: %s" % uid).first()
	if not user:
		abort(404)
	group_list = Group.query.all()
	form = forms.get_EditUserForm(group_list)(obj=user)
	if request.method == 'POST' and form.validate_on_submit():
		if form.userid.data != uid:
			abort(400)

		if form.update.data:
			save_ldap_attributes(form, user)

			if user.save():
				flash("Successfully saved", category="success")
				return redirect(url_for('.user', uid=user.userid))
			else:
				flash("Saving was unsuccessful", category="danger")

	form.password.data = '' # Must manually delete this, since the password is not returned
	return render_template('user.html', user=user, form=form)

@views.route("/user/_new", methods=['GET','POST'])
@login_required
def new_user():
	group_list = Group.query.all()
	form = forms.get_NewUserForm(group_list)()
	if request.method == 'POST' and form.validate_on_submit():
		if form.submit.data:
			user = User()
			save_ldap_attributes(form, user)

			if user.save():
				flash("User created", category="success")
				return redirect(url_for('.user', uid=user.userid))
			else:
				flash("Error while creating user", category="danger")
	return render_template('new_user.html', form=form)


@views.route("/group/")
@login_required
def groups():
	users = User.query.all()
	groups = Group.query.all()
	return render_template('groups.html', users=users, groups=groups)

@views.route('/login', methods=['GET', 'POST'])
def login():
	form = forms.LoginForm()
	if request.method == 'POST' and form.validate_on_submit():
		session['username'] = request.form['username']
		session_box.store_boxed("password", request.form['password'])
		session.modified = True
		return redirect(request.args.get("next", url_for('.root')))
	return render_template("login.html", form=form)

@views.route("/logout")
def logout():
	if "password" in session:
		del session["password"]
	session.modified = True
	return redirect(url_for(".root"))

