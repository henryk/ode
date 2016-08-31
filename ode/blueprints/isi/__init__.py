from __future__ import absolute_import

from flask import Blueprint

blueprint = Blueprint('isi', __name__, static_folder='static', template_folder='templates')

from ode import db

@blueprint.record
def setup_isi(state):
	pass

@blueprint.before_app_first_request
def setup_db():
	db.create_all()


from . import views, navigation, model, forms
