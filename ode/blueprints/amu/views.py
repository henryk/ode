from flask import current_app, render_template, request, redirect, url_for, session, g, flash, abort

from ode import config_get, session_box, login_required
from ode.model import User, Group, MailingList
from . import blueprint, forms, mail, tasks

from flask_babel import _

@blueprint.app_template_filter()
def force_str(s):
	return unicode(s)

def mail_user_password(user, form):
	if form.send_password.data:
		try:
			mail.send_user_mail("%s <%s>" % (user.name, user.mail), user=user, form=form)
			flash(_("User confirmation mail sent"))
		except Exception:
			current_app.logger.debug("Exception while sending mail", exc_info=True)
			flash(_("Couldn't send mail to user"), category="danger")



@blueprint.route("/")
@login_required(False)
def root():
	if session["is_admin"]:
		return redirect(url_for('.users'))
	else:
		return redirect(url_for('.self'))

@blueprint.route("/self", methods=['GET','POST'])
@login_required(False)
def self():
	form = forms.EditSelfForm(obj=g.ldap_user)

	if request.method == 'POST' and form.validate_on_submit():
		if form.update.data:
			changed = save_ldap_attributes(form, g.ldap_user)

			if not changed or g.ldap_user.save():
				flash(_("Successfully saved"), category="success")
				mail_user_password(g.ldap_user, form)

				if form.password.data:
					# Need to update the session
					session_box.store_boxed("password", form.password.data)
					session.modified = True

				return redirect(url_for('.self'))
			else:
				flash(_("Saving was unsuccessful"), category="danger")

	form.password.data = '' # Must manually delete this, since the password is not returned
	return render_template("amu/self.html", form=form)

@blueprint.route("/user/")
@login_required
def users():
	users = User.query.all()
	groups = Group.query.all()
	return render_template('amu/users.html', users=users, groups=groups)

def save_ldap_attributes(form, obj):
	"""Only stores existing LDAP attributes.
	Does not store empty attributes named 'password'.
	Does not change existing attributes named 'userid'.
	Does not change attributes named 'groups'.
	Does not change attributes named 'members'.
	For the following attributes a set_* method is called: aliases, list_members"""

	from ldap3 import LDAPEntryError

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
				if name in ["aliases", "list_members"]:
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

@blueprint.route("/user/<string:uid>", methods=['GET','POST'])
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
				flash(_("Successfully saved"), category="success")
				if not user.save_groups(form.groups.data, group_list):
					flash(_("Some or all of the group changes were not successful"), category="danger")

				mail_user_password(user, form)

				return redirect(url_for('.user', uid=user.userid))
			else:
				flash(_("Saving was unsuccessful"), category="danger")
		elif form.delete.data:
			if form.delete_confirm.data:
				## Warning: flask_ldapconn doesn't give any status, so we implement this from scratch here
				if user.connection.connection.delete(user.dn):
					flash(_("User deleted"), category="success")
					return redirect(url_for('.users'))
				else:
					flash(_("Deletion was unsuccessful"), category="danger")
			else:
				flash(_("Please confirm user deletion"), category="danger")

	form.password.data = '' # Must manually delete this, since the password is not returned
	form.delete_confirm.data = False # Always reset this
	return render_template('amu/user.html', user=user, form=form)

@blueprint.route("/user/_new", methods=['GET','POST'])
@login_required
def new_user():
	group_list = Group.query.all()
	form = forms.get_NewUserForm(group_list)()
	if request.method == 'POST' and form.validate_on_submit():
		if form.submit.data:
			user = User()
			save_ldap_attributes(form, user)

			if user.save():
				flash(_("User created"), category="success")
				if not user.save_groups(form.groups.data, group_list):
					flash(_("Some or all of the groups could not be assigned"), category="danger")

				mail_user_password(user, form)

				return redirect(url_for('.user', uid=user.userid))
			else:
				flash(_("Error while creating user"), category="danger")
	return render_template('amu/new_user.html', form=form)


@blueprint.route("/group/")
@login_required
def groups():
	users = User.query.all()
	groups = Group.query.all()
	return render_template('amu/groups.html', users=users, groups=groups)

@blueprint.route("/group/<string:cn>", methods=['GET','POST'])
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
				flash(_("Successfully saved"), category="success")
				return redirect(url_for('.group', cn=group.name))
			else:
				flash(_("Saving was unsuccessful"), category="danger")

		elif form.delete.data:
			if form.delete_confirm.data:
				## Warning: flask_ldapconn doesn't give any status, so we implement this from scratch here
				if group.connection.connection.delete(group.dn):
					flash(_("Group deleted"), category="success")
					return redirect(url_for('.groups'))
				else:
					flash(_("Deletion was unsuccessful"), category="danger")
			else:
				flash(_("Please confirm group deletion"), category="danger")

	form.delete_confirm.data = False # Always reset this
	return render_template('amu/group.html', group=group, form=form)

@blueprint.route("/group/_new", methods=['GET','POST'])
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
				flash(_("Group created"), category="success")
				return redirect(url_for('.group', cn=group.name))
			else:
				flash(_("Error while creating group"), category="danger")
	return render_template('amu/new_group.html', form=form)


@blueprint.route("/mailing_list/")
@login_required
def mailing_lists():
	lists = MailingList.query.all()
	return render_template('amu/mailing_lists.html', lists=lists)


@blueprint.route("/mailing_list/<string:cn>", methods=['GET','POST'])
@login_required
def mailing_list(cn):
	mlist = MailingList.query.filter("name: %s" % cn).first()
	if not mlist:
		abort(404)
	group_list = Group.query.all()
	user_list = User.query.all()
	form = forms.get_EditMailingListForm(user_list, group_list)(obj=mlist)

	if request.method == 'POST' and form.validate_on_submit():
		if form.update.data:
			mlist.set_list_members(form.list_members.data)
			if form.import_file.data:
				import_existing, import_errors = mlist.import_list_members(form.import_file.data.readlines())

				for a in import_errors:
					flash(_("Invalid format, did not import: %s") % a, category="danger")

				for a in import_existing:
					flash(_("Already existing, did not import: %s") % a, category="warning")

			if mlist.save():
				flash(_("Successfully saved"), category="success")
				tasks.sync_mailing_lists.apply_async()  #  Immediately schedule a mailing list update
				return redirect(url_for('.mailing_list', cn=mlist.name))
			else:
				flash(_("Saving was unsuccessful"), category="danger")

		elif form.delete.data:
			if form.delete_confirm.data:
				## Warning: flask_ldapconn doesn't give any status, so we implement this from scratch here
				if mlist.connection.connection.delete(mlist.dn):
					flash(_("Mailing list deleted"), category="success")
					return redirect(url_for('.mailing_lists'))
				else:
					flash(_("Deletion was unsuccessful"), category="danger")
			else:
				flash(_("Please confirm mailing list deletion"), category="danger")

	form.delete_confirm.data = False # Always reset this
	return render_template('amu/mailing_list.html', list=mlist, group_list=group_list, user_list=user_list, form=form)

@blueprint.route("/mailing_list/_new", methods=['GET','POST'])
@login_required
def new_mailing_list():
	group_list = Group.query.all()
	user_list = User.query.all()
	form = forms.get_NewMailingListForm(user_list, group_list)()
	if request.method == 'POST' and form.validate_on_submit():
		if form.submit.data:
			mlist = MailingList()
			save_ldap_attributes(form, mlist)
			if form.import_file.data:
				import_existing, import_errors = mlist.import_list_members(form.import_file.data.readlines())

				for a in import_errors:
					flash(_("Invalid format, did not import: %s") % a, category="danger")

				for a in import_existing:
					flash(_("Already existing, did not import: %s") % a, category="warning")

			if mlist.save():
				flash(_("Mailing list created"), category="success")
				return redirect(url_for('.mailing_list', cn=mlist.name))
			else:
				flash(_("Error while creating mailing list"), category="danger")
	return render_template('amu/new_mailing_list.html', group_list=group_list, user_list=user_list, form=form)
