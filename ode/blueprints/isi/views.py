from flask import current_app, render_template, request, redirect, url_for, session, g, flash, abort, render_template_string

from ode import config_get, session_box, login_required, db
from . import blueprint, forms
from .model import Event, Source, Invitation, Template
from ode.model import MailingList, User as LDAPUser

import pprint

@blueprint.app_template_filter("pprint")
def pprint_string(s):
	return pprint.pformat(s)

@blueprint.route("/")
def root():
	return redirect(url_for('.event_list'))

@blueprint.route("/event/")
@login_required
def event_list():
	refresh_form = forms.RefreshForm()

	sources = Source.query.all()

	events = []

	for s in sources:
		for e in s.events:
			if e.upstream_event:
				continue

			events.append( e )

	return render_template("isi/event_list.html", events=events, refresh_form=refresh_form)

@blueprint.route("/event/<uuid:event_id>")
@login_required
def event_view(event_id):
	event = Event.query.filter(Event.id==event_id).first()
	if not event:
		abort(404)

	return render_template("isi/event_view.html", event=event)

@blueprint.route("/event/_refresh", methods=["POST"])
@login_required
def refresh():
	form = forms.RefreshForm()

	if request.method == 'POST' and form.validate_on_submit():
		if form.refresh.data:

			for k,v in current_app.config["ISI_EVENT_SOURCES"].items():
				Source.refresh(k, v)

	return redirect(url_for('.event_list'))

@blueprint.route("/invitation/<uuid:invitation_id>", methods=["GET", "POST"])
@login_required
def invitation_view(invitation_id):
	invitation = Invitation.query.filter(Invitation.id==invitation_id).first()
	if not invitation:
		abort(404)

	mlists = MailingList.query.all()

	form = forms.EditInvitationForm(obj=invitation)
	if request.method == 'POST' and form.validate_on_submit():
		form.populate_obj(invitation)
		db.session.commit()

		if form.send.data:
			return redirect(url_for('.invitation_send', invitation_id=invitation_id))

	return render_template("isi/invitation_view.html", invitation=invitation, form=form, mailing_lists=mlists)

@blueprint.route("/invitation/<uuid:invitation_id>/send", methods=["GET", "POST"])
@login_required
def invitation_send(invitation_id):
	invitation = Invitation.query.filter(Invitation.id==invitation_id).first()
	if not invitation:
		abort(404)

	recipient_users = set()
	recipient_extras = []

	for recipient in invitation.recipients_raw:
		mlist = MailingList.query.get(recipient)
		if mlist:
			recipient_users.update(mlist.members)
			recipient_extras.extend(mlist.additional_addresses)
		elif recipient:
			recipient_extras.append(recipient)

	recipients = []
	for dn in recipient_users:
		u = LDAPUser.query.get(dn)
		if u:
			recipients.append(u)
		else:
			recipients.append(dn)
	recipients.extend(recipient_extras)

	return render_template("isi/invitation_send.html", invitation=invitation, recipients=recipients)

@blueprint.route("/invitation/_new", methods=["POST"])
@login_required
def create_invitation():
	form = forms.CreateInvitationForm()

	if request.method == 'POST' and form.validate_on_submit():
		if form.create.data:
			event = Event.query.filter(Event.id==form.event_id.data).first()
			if not event:
				abort(404)

			e = event.linked_copy()
			i = Invitation(event=e)

			tmpl = Template.query.filter(Template.category.in_(e.categories)).first()
			if tmpl:
				for a in ["sender", "recipients_raw"]:
					setattr(i, a, getattr(tmpl, a))
				for a in ["subject", "text_html"]:
					setattr(i, a, 
						render_template_string(getattr(tmpl, a), event=e)
					)

			else:
				i.text_html = "<h1>Invitation to '%s'</h1><p>Please come all</p>" % e.summary

			db.session.add(e)
			db.session.add(i)
			db.session.commit()

			return redirect(url_for('.invitation_view', invitation_id=i.id))
			

	return redirect(url_for('.event_list'))

