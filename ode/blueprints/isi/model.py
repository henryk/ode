from __future__ import absolute_import

import uuid

from ode import db
from sqlalchemy_utils.types.uuid import UUIDType

class Event(db.Model):
	id = db.Column('id', UUIDType, default=uuid.uuid4, primary_key=True)

	source = db.Column(db.String)
	source_id = db.Column(db.String)
	updated = db.Column(db.Float)

	event_contents = db.Column(db.LargeBinary)

