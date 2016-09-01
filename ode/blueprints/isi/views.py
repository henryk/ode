from flask import current_app, render_template, request, redirect, url_for, session, g, flash, abort

from ode import config_get, session_box, login_required, db
from . import blueprint, forms
from .model import Event, Source, Invitation

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

	form = forms.EditInvitationForm(obj=invitation)
	if request.method == 'POST' and form.validate_on_submit():
		form.populate_obj(invitation)
		db.session.commit()

	return render_template("isi/invitation_view.html", invitation=invitation, form=form)

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

			i.text_html = "<h1>Invitation to '%s'</h1><p>Please come all</p>" % e.summary

			db.session.add(e)
			db.session.add(i)
			db.session.commit()

			return redirect(url_for('.invitation_view', invitation_id=i.id))
			

	return redirect(url_for('.event_list'))

