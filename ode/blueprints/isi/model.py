from __future__ import absolute_import

import uuid, requests, time, vobject, enum, json

from ode import db
from sqlalchemy_utils.types.uuid import UUIDType
from sqlalchemy.types import TypeDecorator
from sqlalchemy.sql.sqltypes import Unicode
from sqlalchemy.orm import relationship, backref, reconstructor
from sqlalchemy.sql.expression import and_
from sqlalchemy_enum34 import EnumType

# vobject loses the unicode property somewhere along the way so that properties are 'str' object
# I *think* they are all UTF-8 encoded, since this is the iCalendar default, so for simple printing
# do this:
def vobject_unicode(s):
	return s if isinstance(s, unicode) else unicode(s, "UTF-8")

# From http://stackoverflow.com/a/11915539
class Json(TypeDecorator):
	impl = db.String

	def process_bind_param(self, value, dialect):
		return json.dumps(value)

	def process_result_value(self, value, dialect):
		return json.loads(value)

class InvitationState(enum.Enum):
	PREPARING = "preparing"
	OPEN = "open"

class Template(db.Model):
	id = db.Column('id', UUIDType, default=uuid.uuid4, primary_key=True)

	category = db.Column(db.String)

	subject = db.Column(db.String)
	text_html = db.Column(db.String)
	sender = db.Column(db.String)
	recipients_raw = db.Column(Json())


class Invitation(db.Model):
	id = db.Column('id', UUIDType, default=uuid.uuid4, primary_key=True)

	event_id = db.Column(db.ForeignKey('event.id'))

	subject = db.Column(db.String)
	text_html = db.Column(db.String)
	sender = db.Column(db.String)
	recipients_raw = db.Column(Json())

	state = db.Column(EnumType(InvitationState, name="invitation_state"), default=InvitationState.PREPARING)


class Event(db.Model):
	id = db.Column('id', UUIDType, default=uuid.uuid4, primary_key=True)

	source_id = db.Column(db.ForeignKey('source.id'))

	uid = db.Column(db.String, unique=False)

	upstream_event_id = db.Column(db.ForeignKey('event.id'), nullable=True)
	
	children = relationship('Event', backref=backref('upstream_event', remote_side=[id]))
	invitations = relationship('Invitation', backref=backref('event'), cascade='all, delete-orphan')

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
		retval.updated = self.updated
		retval.uid = self.uid
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

	@property
	def categories(self): return map(vobject_unicode, self._vevent.categories.value)

	@property
	def child_invitations(self):
		return [i for e in self.children for i in e.invitations]

class Source(db.Model):
	id = db.Column('id', UUIDType, default=uuid.uuid4, primary_key=True)

	name = db.Column(db.String, unique=True)
	updated = db.Column(db.Float)

	contents = db.Column(Unicode)

	events = relationship('Event', backref=backref('source'), cascade='all, delete-orphan')

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
