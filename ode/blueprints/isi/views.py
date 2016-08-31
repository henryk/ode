from flask import current_app, render_template, request, redirect, url_for, session, g, flash, abort

from ode import config_get, session_box, login_required
from . import blueprint, forms


@blueprint.route("/")
@login_required(False)
def root():
	refresh_form = forms.RefreshForm()
	return render_template("isi/root.html", refresh_form=refresh_form)

@blueprint.route("/refresh", methods=["POST"])
def refresh():
	form = forms.RefreshForm()

	if request.method == 'POST' and form.validate_on_submit():
		if form.refresh.data:

			current_app.logger.debug("Yolo!")


	return redirect(url_for('.root'))
