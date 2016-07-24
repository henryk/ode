from functools import wraps
from flask import Blueprint, current_app, render_template, request, redirect, url_for, session, g, flash
from amu import forms
from ldap3 import LDAPBindError

views = Blueprint('views', __name__)

def login_required(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if "username" in session and "password" in session:
			userdn = config_get("AMU_BIND_DN", username=session["username"])
			try:
				g.ldap_conn = current_app.extensions.get('ldap_conn').connect(userdn, session['password'])
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

def config_get(key, default=Ellipsis, **kwargs):
	d = dict(current_app.config.items())
	d.update(kwargs)
	if default is Ellipsis:
		return d[key] % d
	else:
		return d.get(key, default) % d


@views.route("/")
@login_required
def root():
	return render_template('index.html')

@views.route('/login', methods=['GET', 'POST'])
def login():
	form = forms.LoginForm()
	if request.method == 'POST' and form.validate_on_submit():
		session['username'] = request.form['username']
		session['password'] = request.form['password']
		session.modified = True
		return redirect(request.args.get("next", url_for('.root')))
	return render_template("login.html", form=form)
