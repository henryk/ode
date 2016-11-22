from __future__ import absolute_import

import uuid, requests, datetime, vobject, enum, json, flanker.addresslib.address

from ode import db
from ode.model import MailingList, User as LDAPUser
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

class RecipientState(enum.Enum):
	NEW = "new"
	DESELECTED = "deselected"
	PENDING = "pending"
	SENT = "sent"

class AcceptState(enum.Enum):
	UNKNOWN = "unknown"
	YES = "yes"
	NO = "no"

class AcceptType(enum.Enum):
	UNKNOWN = "unknown"
	MANUAL = "manual"
	EMAIL = "email"
	LINK = "link"

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
	recipients = relationship('Recipient', backref=backref('invitation'), cascade='all, delete-orphan')
	owners = db.Column(Json(), nullable=False, default=[])

	state = db.Column(EnumType(InvitationState, name="invitation_state"), default=InvitationState.PREPARING)

	def expand_recipients(self):
		recipient_users = set()
		recipient_extras = []

		for recipient in self.recipients_raw:
			mlist = MailingList.query.get(recipient)
			if mlist:
				recipient_users.update(mlist.members)
				recipient_extras.extend(mlist.additional_addresses)
			elif recipient:
				recipient_extras.append(recipient)

		recipients = []
		for dn in recipient_users:
			user = LDAPUser.query.get(dn)
			if user:
				parsed = flanker.addresslib.address.parse(user.mail_form)
				had_one = False

				for u in self.recipients:
					if u.value == user.dn:
						had_one = True

						if not parsed: # Remove invalid address entries (shouldn't happen)
							self.recipients.remove(u)
						else:
							break

				if not had_one:
					if parsed:
						self.recipients.append(
							Recipient(value=user.dn)
						)

			else:
				recipient_extras.append(dn)

		for address in recipient_extras:
			parsed = flanker.addresslib.address.parse(address)

			if not parsed:
				continue

			had_one = False

			for r in self.recipients:
				if parsed.address == r.address:
					had_one = True
					break

			if not had_one:
				self.recipients.append(
					Recipient(value=parsed.to_unicode())
				)

	@property
	def relevant_recipients(self):
		return [r for r in self.recipients if r.state is r.state.SENT or r.parent]

	@property
	def rsvp_yes(self):
		return [r for r in self.relevant_recipients if r.accept is r.accept.YES]

	@property
	def rsvp_unknown(self):
		return [r for r in self.relevant_recipients if r.accept is r.accept.UNKNOWN]

	@property
	def rsvp_no(self):
		return [r for r in self.relevant_recipients if r.accept is r.accept.NO]




class Recipient(db.Model):
	id = db.Column('id', UUIDType, default=uuid.uuid4, primary_key=True)

	parent_id = db.Column(db.ForeignKey('recipient.id'))
	children = relationship("Recipient", backref=backref('parent', remote_side=[id]))

	invitation_id = db.Column(db.ForeignKey('invitation.id'))

	value = db.Column(db.String)

	state = db.Column(EnumType(RecipientState, name="recipient_state"), default=RecipientState.NEW)
	pending_address = db.Column(db.String)

	send_time = db.Column(db.DateTime)

	accept = db.Column(EnumType(AcceptState, name="accept_state"), default=AcceptState.UNKNOWN)
	accept_time = db.Column(db.DateTime)
	accept_type = db.Column(EnumType(AcceptType, name="accept_type"), default=AcceptType.UNKNOWN)

	def _mail_form(self):
		user = LDAPUser.query.get(self.value)
		if user:
			return user.mail_form
		else:
			return self.value

	def _parse_address(self):
		return flanker.addresslib.address.parse(self._mail_form())

	@property
	def to_unicode(self):
		a = self._parse_address()
		if not a and self.parent:
			return self.value
		return a.to_unicode()

	@property
	def full_spec(self):
		return self._parse_address().full_spec()

	@property
	def address(self):
		return self._parse_address().address	

def re_set_timezone(dt):
	if hasattr(dt, "tzinfo"):
		return dt.tzinfo.localize(dt.replace(tzinfo=None))
	else:
		return dt

class Event(db.Model):
	id = db.Column('id', UUIDType, default=uuid.uuid4, primary_key=True)

	source_id = db.Column(db.ForeignKey('source.id'))

	uid = db.Column(db.String, unique=False)

	upstream_event_id = db.Column(db.ForeignKey('event.id'), nullable=True)
	
	children = relationship('Event', backref=backref('upstream_event', remote_side=[id]))
	invitations = relationship('Invitation', backref=backref('event'), cascade='all, delete-orphan')

	updated = db.Column(db.DateTime)

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
			retval.updated = datetime.datetime.utcnow()
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
	def start(self): return re_set_timezone(self._vevent.dtstart.value)

	@property
	def end(self): return re_set_timezone(self._vevent.dtend.value)

	@property
	def categories(self): return map(vobject_unicode, self._vevent.categories.value)

	@property
	def child_invitations(self):
		return [i for e in self.children for i in e.invitations]

	@property
	def relevant_recipients(self):
		return [r for i in self.child_invitations for r in i.relevant_recipients]

	@property
	def rsvp_yes(self):
		return [r for r in self.relevant_recipients if r.accept is r.accept.YES]

	@property
	def rsvp_unknown(self):
		return [r for r in self.relevant_recipients if r.accept is r.accept.UNKNOWN]

	@property
	def rsvp_no(self):
		return [r for r in self.relevant_recipients if r.accept is r.accept.NO]
	
	
CURRENT_DELTA=datetime.timedelta(seconds=10)
class Source(db.Model):
	id = db.Column('id', UUIDType, default=uuid.uuid4, primary_key=True)

	name = db.Column(db.String, unique=True)
	updated = db.Column(db.DateTime)

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
		self.updated = datetime.datetime.utcnow()

		for vevent in vobject.readOne(self.contents).vevent_list:
			event = Event.refresh(vevent)

			if not event.source:
				event.source = self

	@property
	def current_events(self):
		return [e for e in self.events if self.updated - e.updated < CURRENT_DELTA]
