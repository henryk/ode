from functools import wraps
from flask import Blueprint, current_app, render_template, request, redirect, url_for, session, g, flash, abort
from flask_nav.elements import Navbar, View, Subgroup
from flask_bootstrap.nav import BootstrapRenderer
from amu import forms, config_get, nav, session_box, mail
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

def determine_admin_status():
	"""Try to query a group. If that succeeds -> Admin, otherwise normal user. Cache the result in the session."""
	if "is_admin" in session:
		return
	else:
		group = Group.query.first()
		session["is_admin"] = not not group
		session.modified = True

def _login_required_int(needs_admin, f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		password = session_box.retrieve_unboxed("password", None)
		if "username" in session and password is not None:
			try:
				connect_and_load_ldap(password)
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
		if session.get("is_admin", False):
			e.extend( [
				View('Users', '.users'),
				View('New user', '.new_user'),
				View('Groups', '.groups'),
				View('New group', '.new_group'),
			] )
		e.extend( [
			Subgroup('Logged in as %s' % g.ldap_user.name,
				View('My profile', '.self'),
				View('Log out', '.logout')
			)
		] )
	return Navbar(*e)


@views.route("/")
@login_required(False)
def root():
	if session["is_admin"]:
		return redirect(url_for('.users'))
	else:
		return redirect(url_for('.self'))

def mail_user_password(user, form):
	if form.send_password.data:
		try:
			mail.send_user_mail("%s <%s>" % (user.name, user.mail), user=user, form=form)
			flash("User confirmation mail sent")
		except Exception:
			current_app.logger.debug("Exception while sending mail", exc_info=True)
			flash("Couldn't send mail to user", category="danger")


@views.route("/self", methods=['GET','POST'])
@login_required(False)
def self():
	form = forms.EditSelfForm(obj=g.ldap_user)

	if request.method == 'POST' and form.validate_on_submit():
		if form.update.data:
			changed = save_ldap_attributes(form, g.ldap_user)

			if not changed or g.ldap_user.save():
				flash("Successfully saved", category="success")
				mail_user_password(g.ldap_user, form)

				if form.password.data:
					# Need to update the session
					session_box.store_boxed("password", form.password.data)
					session.modified = True

				return redirect(url_for('.self'))
			else:
				flash("Saving was unsuccessful", category="danger")

	form.password.data = '' # Must manually delete this, since the password is not returned
	return render_template("self.html", form=form)

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
	Does not change attributes named 'groups'.
	Does not change attributes named 'members'.
	For the following attributes a set_* method is called: aliases"""

	changed = False

	for name, field in form._fields.items():
		if name == "password" and not field.data: continue
		if name == "userid" and getattr(obj, "userid", None): continue
		if name == "groups": continue
		if name == "members": continue

		try:
			old_value = getattr(getattr(obj, name), 'value', getattr(obj, name))
			if old_value != field.data:
				current_app.logger.debug("Setting %s because it was %r and should be %r", name, 
					old_value, field.data)
				setter = None
				if name in ["aliases"]:
					setter = getattr(obj, "set_%s" % name, None)
				if setter:
					setter(field.data)
				else:
					setattr(obj, name, field.data)
				changed = True

		except LDAPEntryError as e:
			continue

	current_app.logger.debug("Change status is %s", changed)
	return changed

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
			changed = save_ldap_attributes(form, user)

			if not changed or user.save():
				flash("Successfully saved", category="success")
				if not user.save_groups(form.groups.data, group_list):
					flash("Some or all of the group changes were not successful", category="danger")

				mail_user_password(user, form)

				return redirect(url_for('.user', uid=user.userid))
			else:
				flash("Saving was unsuccessful", category="danger")
		elif form.delete.data:
			if form.delete_confirm.data:
				## Warning: flask_ldapconn doesn't give any status, so we implement this from scratch here
				if user.connection.connection.delete(user.dn):
					flash("User deleted", category="success")
					return redirect(url_for('.users'))
				else:
					flash("Deletion was unsuccessful", category="danger")
			else:
				flash("Please confirm user deletion", category="danger")

	form.password.data = '' # Must manually delete this, since the password is not returned
	form.delete_confirm.data = False # Always reset this
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
				if not user.save_groups(form.groups.data, group_list):
					flash("Some or all of the groups could not be assigned", category="danger")

				mail_user_password(user, form)

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

@views.route("/group/<string:cn>", methods=['GET','POST'])
@login_required
def group(cn):
	group = Group.query.filter("name: %s" % cn).first()
	if not group:
		abort(404)
	user_list = User.query.all()
	form = forms.get_EditGroupForm(user_list)(obj=group)
	if request.method == 'POST' and form.validate_on_submit():
		if form.update.data:
			if group.set_members(form.members.data):
				flash("Successfully saved", category="success")
				return redirect(url_for('.group', cn=group.name))
			else:
				flash("Saving was unsuccessful", category="danger")

		elif form.delete.data:
			if form.delete_confirm.data:
				## Warning: flask_ldapconn doesn't give any status, so we implement this from scratch here
				if group.connection.connection.delete(group.dn):
					flash("Group deleted", category="success")
					return redirect(url_for('.groups'))
				else:
					flash("Deletion was unsuccessful", category="danger")
			else:
				flash("Please confirm group deletion", category="danger")

	form.delete_confirm.data = False # Always reset this
	return render_template('group.html', group=group, form=form)

@views.route("/group/_new", methods=['GET','POST'])
@login_required
def new_group():
	user_list = User.query.all()
	form = forms.get_NewGroupForm(user_list)()
	if request.method == 'POST' and form.validate_on_submit():
		if form.submit.data:
			group = Group()
			save_ldap_attributes(form, group)
			group.members = form.members.data

			if group.save():
				flash("Group created", category="success")
				return redirect(url_for('.group', cn=group.name))
			else:
				flash("Error while creating group", category="danger")
	return render_template('new_group.html', form=form)




@views.route('/login', methods=['GET', 'POST'])
def login():
	form = forms.LoginForm()
	if request.method == 'POST' and form.validate_on_submit():
		session['username'] = form.username.data
		session_box.store_boxed("password", form.password.data)
		session.modified = True
		return redirect(request.args.get("next", url_for('.root')))
	return render_template("login.html", form=form)

@views.route("/logout")
def logout():
	session.pop("password", None)
	session.pop("is_admin", None)
	session.modified = True
	return redirect(url_for(".root"))

