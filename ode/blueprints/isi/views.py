from flask import current_app, render_template, request, redirect, url_for, session, g, flash, abort

from ode import config_get, session_box, login_required
from . import blueprint, forms
from .model import Source

import vobject


@blueprint.route("/")
@login_required(False)
def root():
	refresh_form = forms.RefreshForm()

	sources = Source.query.all()

	calendars = [vobject.readOne(s.contents) for s in sources]

	# vobject loses the unicode property somewhere along the way so that properties are 'str' object
	# I *think* they are all UTF-8 encoded, since this is the iCalendar default, so for simple printing
	# do this:
	calendars_strings = [unicode(str(c), "UTF-8") for c in calendars]

	return render_template("isi/root.html", calendars=calendars_strings, refresh_form=refresh_form)

@blueprint.route("/refresh", methods=["POST"])
def refresh():
	form = forms.RefreshForm()

	if request.method == 'POST' and form.validate_on_submit():
		if form.refresh.data:

			for k,v in current_app.config["ISI_EVENT_SOURCES"].items():
				Source.refresh(k, v)



	return redirect(url_for('.root'))
