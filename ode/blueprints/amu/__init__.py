from __future__ import absolute_import

from flask import Blueprint
from flask_nav import register_renderer

blueprint = Blueprint('amu', __name__, static_folder='static', template_folder='templates')


@blueprint.record
def setup_amu(state):
	from .navigation import AMUNavbarRenderer
	register_renderer(state.app, 'amu_navbar', AMUNavbarRenderer)

	from .mail import mailer
	mailer.init_app(state.app)


from . import views, forms, mail, navigation
