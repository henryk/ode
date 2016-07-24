from functools import wraps
from flask import Blueprint, current_app, render_template, request, redirect, url_for, session, g, flash
from amu import forms, config_get
from ldap3 import LDAPBindError

from amu.model import User

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
				return redirect(url_for('.login', next=request.url))
			return f(*args, **kwargs)
		else:
			return redirect(url_for('.login', next=request.url))
	return decorated_function

@views.route("/")
@login_required
def root():
	users = User.query.all()
	return render_template('index.html', users=users)

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

