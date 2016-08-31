from __future__ import absolute_import

import uuid, requests, time

from ode import db
from sqlalchemy_utils.types.uuid import UUIDType
from sqlalchemy.sql.sqltypes import Unicode


# class Event(db.Model):
# 	id = db.Column('id', UUIDType, default=uuid.uuid4, primary_key=True)

# 	source = db.Column(db.String)
# 	source_id = db.Column(db.String)
# 	updated = db.Column(db.Float)

# 	event_contents = db.Column(db.LargeBinary)

class Source(db.Model):
	id = db.Column('id', UUIDType, default=uuid.uuid4, primary_key=True)

	name = db.Column(db.String, unique=True)
	updated = db.Column(db.Float)

	contents = db.Column(Unicode)

	@classmethod
	def refresh(cls, name, url):
		retval = cls.query.filter(cls.name == name).first()
		if not retval:
			retval = cls(name=name)
			db.session.add(retval)

		retval.load_data(url)
		db.session.commit()

		return retval

	def load_data(self, url):
		self.contents = requests.get(url).text
		self.updates = time.time()