from flask import current_app, render_template, request, redirect, url_for, session, g, flash, abort

from ode import config_get, session_box, login_required
from . import blueprint, forms
from .model import Event, Source

import pprint

@blueprint.app_template_filter("pprint")
def pprint_string(s):
	return pprint.pformat(s)

@blueprint.route("/")
@login_required
def root():
	refresh_form = forms.RefreshForm()

	sources = Source.query.all()

	events = []

	for s in sources:
		for e in s.events:
			events.append(e)

	return render_template("isi/root.html", events=events, refresh_form=refresh_form)

@blueprint.route("/refresh", methods=["POST"])
@login_required
def refresh():
	form = forms.RefreshForm()

	if request.method == 'POST' and form.validate_on_submit():
		if form.refresh.data:

			for k,v in current_app.config["ISI_EVENT_SOURCES"].items():
				Source.refresh(k, v)



	return redirect(url_for('.root'))

@blueprint.route("/event/<uuid:event_id>")
@login_required
def event_view(event_id):
	event = Event.query.filter(Event.id==event_id).first()
	if not event:
		abort(404)

	return render_template("isi/event_view.html", event=event)