from flask import current_app, render_template, request, redirect, url_for, session, g, flash, abort, render_template_string

from ode import config_get, session_box, login_required, db, create_signer
from . import blueprint, forms, tasks
from .model import Event, Source, Invitation, InvitationState, Template, Recipient
from ode.model import MailingList

import pprint, uuid, datetime
from itsdangerous import BadSignature

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

	if invitation.state is not invitation.state.PREPARING:
		from wtforms_components import read_only
		read_only(form.sender)
		read_only(form.text_html)
		read_only(form.subject)

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

	invitation.expand_recipients()
	db.session.commit()

	form = forms.get_SendInvitationForm(invitation.recipients)(obj=invitation)
	if request.method == 'GET':
		form.recipients.data = [str(r.id) for r in invitation.recipients if r.state is r.state.NEW]

	if request.method == 'POST' and form.validate_on_submit():
		if form.back.data:
			return redirect(url_for('.invitation_view', invitation_id=invitation_id))
		else:

			do_send = bool(form.send.data)
			have_at_least_one_recipient = False

			for recipient_id, mail_form in form.recipients.choices:
				recipient = None
				for r in invitation.recipients:
					if str(r.id) == recipient_id:
						recipient = r
						break
				if recipient is None:
					continue

				if recipient_id not in form.recipients.data:
					recipient.state = recipient.state.DESELECTED
				else:
					if do_send:
						recipient.state = recipient.state.PENDING
						recipient.pending_address = recipient.full_spec
				
						have_at_least_one_recipient = True

			if do_send and have_at_least_one_recipient:
				invitation.state = invitation.state.OPEN
				db.session.commit()
				tasks.send_mails.apply_async( (invitation_id,) )
				flash("Message away!")
				return redirect(url_for(".event_list"))
			else:
				db.session.commit()
	
	return render_template("isi/invitation_send.html", invitation=invitation, form=form)

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

@blueprint.route("/rsvp/<string:param>")
def rsvp(param):
	signer = create_signer(salt="rsvp_mail")

	try:
		param = signer.unsign(param)
	except BadSignature:
		abort(404)

	recipient_id, response = param.split("_")
	
	recipient = Recipient.query.filter(Recipient.id==uuid.UUID(recipient_id)).first()
	if not recipient:
		abort(404)

	if response == "0":
		recipient.accept = recipient.accept.NO
	else:
		recipient.accept = recipient.accept.YES
	recipient.accept_time = datetime.datetime.utcnow()

	db.session.commit()
	
	return "Thank you"
