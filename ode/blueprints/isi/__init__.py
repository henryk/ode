from __future__ import absolute_import

from flask import Blueprint

blueprint = Blueprint('isi', __name__, static_folder='static', template_folder='templates')


@blueprint.record
def setup_isi(state):
	pass


from . import views, navigation
