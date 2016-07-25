from functools import wraps
from flask import Blueprint, current_app, render_template, request, redirect, url_for, session, g, flash
from flask_nav.elements import Navbar, View, Subgroup
from flask_bootstrap.nav import BootstrapRenderer
from amu import forms, config_get, nav
from ldap3 import LDAPBindError

from amu.model import User, Group

views = Blueprint('views', __name__)

def connect_and_load_ldap():
	userdn = config_get("AMU_BIND_DN", username=session["username"])
	g.ldap_conn = current_app.extensions.get('ldap_conn').connect(userdn, session['password'])
	g.ldap_user = User.query.filter("userid: %s" % session["username"]).first()

def login_required(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if "username" in session and "password" in session:
			try:
				connect_and_load_ldap()
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

@views.route("/user/<string:uid>")
@login_required
def user(uid):
	user = User.query.filter("userid: %s" % uid).first()
	group_list = Group.query.all()
	form = forms.get_EditUserForm(group_list)(obj=user)
	return render_template('user.html', user=user, form=form)

@views.route("/user/_new", methods=['GET','POST'])
@login_required
def new_user():
	group_list = Group.query.all()
	form = forms.get_NewUserForm(group_list)()
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
		session['password'] = request.form['password']
		session.modified = True
		return redirect(request.args.get("next", url_for('.root')))
	return render_template("login.html", form=form)

@views.route("/logout")
def logout():
	if "password" in session:
		del session["password"]
	session.modified = True
	return redirect(url_for(".root"))

