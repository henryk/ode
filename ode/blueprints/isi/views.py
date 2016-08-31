from flask import current_app, render_template, request, redirect, url_for, session, g, flash, abort

from ode import config_get, session_box, login_required
from . import blueprint


@blueprint.route("/")
@login_required(False)
def root():
	return render_template("isi/root.html")
