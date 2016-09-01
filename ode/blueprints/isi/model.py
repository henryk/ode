from __future__ import absolute_import

import uuid, requests, time, vobject

from ode import db
from sqlalchemy_utils.types.uuid import UUIDType
from sqlalchemy.sql.sqltypes import Unicode
from sqlalchemy.orm import relationship, backref, reconstructor
from sqlalchemy.sql.expression import and_

# vobject loses the unicode property somewhere along the way so that properties are 'str' object
# I *think* they are all UTF-8 encoded, since this is the iCalendar default, so for simple printing
# do this:
def vobject_unicode(s):
	return s if isinstance(s, unicode) else unicode(s, "UTF-8")

class Invitation(db.Model):
	id = db.Column('id', UUIDType, default=uuid.uuid4, primary_key=True)

	event_id = db.Column(db.ForeignKey('event.id'))
	event = relationship('Event', backref=backref('invitations', cascade='all, delete-orphan'))

	text_html = db.Column(db.String)


class Event(db.Model):
	id = db.Column('id', UUIDType, default=uuid.uuid4, primary_key=True)

	source = relationship('Source', uselist=False, backref=backref('events', cascade='all, delete-orphan'))
	source_id = db.Column(db.ForeignKey('source.id'))

	uid = db.Column(db.String, unique=False)

	upstream_event = relationship('Event', uselist=False)
	upstream_event_id = db.Column(db.ForeignKey('event.id'), nullable=True)

	updated = db.Column(db.Float)

	contents = db.Column(Unicode)

	def __init__(self, *args, **kwargs):
		super(Event, self).__init__(*args, **kwargs)
		self.reinit()

	@reconstructor
	def reinit(self):
		if self.contents:
			self._vevent = vobject.readOne(self.contents)

	@classmethod
	def refresh(cls, vevent):
		if isinstance(vevent, cls):
			retval = vevent
			retval.contents = vevent.upstream_event.contents
			retval.updated = vevent.upstream_event.updated
			retval.reinit()
		else:
			retval = cls.query.filter(and_(cls.uid == vevent.uid.value, cls.upstream_event_id == None)).first()
			if not retval:
				retval = cls(uid = vevent.uid.value)

			retval.contents = vevent.serialize().decode("UTF-8")
			retval.updated = time.time()
			retval.reinit()

		return retval

	def linked_copy(self):
		retval = self.__class__()
		retval.upstream_event = self
		retval.source = self.source
		retval.contents = self.contents
		retval.update = self.updated
		retval.reinit()

		return retval


	@property
	def summary(self): return vobject_unicode(self._vevent.summary.value)

	@property
	def description(self): return vobject_unicode(self._vevent.description.value)

	@property
	def start(self): return self._vevent.dtstart.value

	@property
	def end(self): return self._vevent.dtend.value


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
		self.updated = time.time()

		for vevent in vobject.readOne(self.contents).vevent_list:
			event = Event.refresh(vevent)

			if not event.source:
				event.source = self
