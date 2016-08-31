from __future__ import absolute_import

from flask import Blueprint
from flask_nav import Nav, register_renderer

nav = Nav()

blueprint = Blueprint('amu', __name__, static_folder='static', template_folder='templates')


@blueprint.record
def setup_amu(state):
	nav.init_app(state.app)

	from .views import CustomRenderer
	register_renderer(state.app, 'amu_custom', CustomRenderer)

	from .mail import mailer
	mailer.init_app(state.app)


from . import views, forms, mail
