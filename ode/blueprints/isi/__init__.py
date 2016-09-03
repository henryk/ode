from __future__ import absolute_import

from flask import Blueprint, current_app

blueprint = Blueprint('isi', __name__, static_folder='static', template_folder='templates')

from ode import db

@blueprint.record
def setup_isi(state):
	pass

@blueprint.before_app_first_request
def setup_db():
	db.create_all()

	## Add default templates if defined
	from .model import Template
	if not Template.query.first() and "ISI_DEFAULT_TEMPLATES" in current_app.config:
		for tpl in current_app.config["ISI_DEFAULT_TEMPLATES"]:
			template = Template(**tpl)
			db.session.add(template)
			db.session.commit()


from . import views, navigation, model, forms, tasks
