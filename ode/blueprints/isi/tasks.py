from __future__ import absolute_import

from ode import cel, db, create_signer, mailer
from .model import Invitation, Recipient, Source
from flask import current_app, url_for, render_template_string

from flask_mail import Message

import datetime, vobject, flanker.addresslib.address


class NonStupidMessage(Message):
	"""Implements a workaround for stupid default behaviour:
		If the message contains a html part, the original Message class *always* 
		creates a multipart/alternative with a text/plain and a text/html part.
		Even if there is no plain part, which is left empty in that case.
		This class undoes this: If there is no plain part, the alternative part
		is replaced with the html part.
		Also it allows to remove the Content-Disposition header by setting the
		disposition to REMOVE."""
	def _message(self):
		retval = super(NonStupidMessage, self)._message()

		if self.html and not self.body:
			payload = retval.get_payload()
			for i, p in enumerate(payload):
				if p.get_content_type() == 'multipart/alternative':
					payload_inner = p.get_payload()
					for j, r in enumerate(payload_inner):
						if r.get_content_type() == 'text/plain':
							del payload_inner[i]
					if len(payload_inner) == 1:
						payload[i] = payload_inner[0]
					else:
						p.set_payload(payload_inner)
			retval.set_payload(payload)

		for part in retval.walk():
			d = part.get("Content-Disposition", "")
			if d.startswith("REMOVE"):
				del part["Content-Disposition"]

		return retval


@cel.task
def send_mails(invitation_id):
	invitation = Invitation.query.filter(Invitation.id==invitation_id).one()

	for recipient in invitation.recipients:
		if recipient.state is recipient.state.PENDING:
			send_one_mail.apply_async( (recipient.id,) )

@cel.task
def send_one_mail(recipient_id):
	try:
		recipient = Recipient.query.filter(Recipient.id==recipient_id).one()

		signer = create_signer(salt="rsvp_mail")

		param_yes = signer.sign("%s_%s" % (str(recipient.id), 1))
		param_no = signer.sign("%s_%s" % (str(recipient.id), 0))

		link_yes = url_for('isi.rsvp', param=param_yes, _external=True)
		link_no = url_for('isi.rsvp', param=param_no, _external=True)

		invitation = recipient.invitation

		template_params = dict( 
			invitation=invitation, event=invitation.event,
			link_yes=link_yes, link_no=link_no)

		sender_address = flanker.addresslib.address.parse(invitation.sender)
		recipient_address = flanker.addresslib.address.parse(recipient.pending_address)

		params = dict(sender=sender_address.full_spec(),
			subject=invitation.subject)

		params["html"] = render_template_string(invitation.text_html, **template_params)
		params["charset"] = "UTF-8"

		cal = vobject.newFromBehavior('vcalendar')
		cal.vevent=invitation.event._vevent
		cal.add('method').value="REQUEST"
		cal.vevent.add('ORGANIZER').value="MAILTO:"+sender_address.address
		cal.vevent.add('ATTENDEE').value="MAILTO:"+recipient_address.address
		cal.vevent.uid.value = str(recipient.id)
		cal.vevent.attendee.partstat_param="NEEDS-ACTION"
		cal.vevent.attendee.rsvp_param="TRUE"

		calstream = cal.serialize()

		msg = NonStupidMessage(recipients=[recipient_address.full_spec()], **params)
		msg.attach("invite.ics", "text/calendar; method=REQUEST", calstream,
			disposition="REMOVE",
		)
		retval = mailer.send(msg)

		recipient.state = recipient.state.SENT
		recipient.send_time = datetime.datetime.utcnow()
		db.session.commit()
	except:
		recipient.state = recipient.state.NEW
		db.session.commit()
		raise

	return retval

@cel.task
def refresh_1minute():
	for k,v in current_app.config["ISI_EVENT_SOURCES"].items():
		Source.refresh(k, v)
