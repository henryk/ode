from flask import current_app, render_template, request, redirect, url_for, session, g, flash, abort

from ode import config_get, session_box, login_required
from . import blueprint, forms
from .model import Source

import vobject, pprint

@blueprint.app_template_filter("pprint")
def pprint_string(s):
	return pprint.pformat(s)

@blueprint.route("/")
@login_required(False)
def root():
	refresh_form = forms.RefreshForm()

	sources = Source.query.all()

	events = []

	# vobject loses the unicode property somewhere along the way so that properties are 'str' object
	# I *think* they are all UTF-8 encoded, since this is the iCalendar default, so for simple printing
	# do this:
	def s_(s):
		return s if isinstance(s, unicode) else unicode(s, "UTF-8")

	for s in sources:
		calendar = vobject.readOne(s.contents)
		for event in calendar.vevent_list:
			events.append({
				"source": s.name,
				"summary": s_(event.summary.value),
				"description": s_(event.description.value),
				"start": event.dtstart.value,
				"end": event.dtend.value,
			})

	return render_template("isi/root.html", events=events, refresh_form=refresh_form)

@blueprint.route("/refresh", methods=["POST"])
def refresh():
	form = forms.RefreshForm()

	if request.method == 'POST' and form.validate_on_submit():
		if form.refresh.data:

			for k,v in current_app.config["ISI_EVENT_SOURCES"].items():
				Source.refresh(k, v)



	return redirect(url_for('.root'))
