from __future__ import absolute_import

from ode import mailer, db
from .model import Recipient, AcceptType, AcceptState

import vobject, imapclient, email, uuid, datetime

from flask_mail import Message

from flask import current_app



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

def send_imip_invitation(vevent, recipient_address, recipient_id, **kwargs):
		organizer = current_app.config["ISI_IMIP_ADDRESS"] % {"token": recipient_id}

		cal = vobject.newFromBehavior('vcalendar')
		cal.vevent=vevent
		cal.add('method').value="REQUEST"
		cal.vevent.add('ORGANIZER').value="MAILTO:"+organizer
		cal.vevent.add('ATTENDEE').value="MAILTO:"+recipient_address.address
		cal.vevent.uid.value = str(recipient_id)
		cal.vevent.attendee.partstat_param="NEEDS-ACTION"
		cal.vevent.attendee.rsvp_param="TRUE"

		calstream = cal.serialize()

		msg = NonStupidMessage(recipients=[recipient_address.full_spec()], **kwargs)
		msg.attach("invite.ics", "text/calendar; method=REQUEST", calstream,
			disposition="REMOVE",
		)
		retval = mailer.send(msg)


def receive_mails():
	server = imapclient.IMAPClient(current_app.config["ISI_IMAP_SERVER"], 
		ssl=current_app.config["ISI_IMAP_TLS"])
	server.login(current_app.config["ISI_IMAP_USER"], current_app.config["ISI_IMAP_PASSWORD"])

	server.debug=current_app.config.get("ISI_IMAP_DEBUG", False)

	if not server.folder_exists("handled"):
		server.create_folder("handled")
	if not server.folder_exists("unhandled"):
		server.create_folder("unhandled")
	if not server.folder_exists("errors"):
		server.create_folder("errors")

	while True:
		select_info = server.select_folder('INBOX')
		if select_info["EXISTS"]:
			messages = server.search(['NOT', 'DELETED'])
			response = server.fetch(messages, ['RFC822'])
			for msgid, data in response.iteritems():
				body = data['RFC822']
				target = 'errors'

				try:
					message = email.message_from_string(body)

					if handle_imip_response(message):
						target = 'handled'
					else:
						target = 'unhandled'

				except:
					current_app.logger.exception("Exception while processing message")
				finally:
					server.copy(msgid, target)
					server.delete_messages(msgid)
					server.expunge()





		server.idle()
		server.idle_check(timeout=300)  # Do a normal poll every 5 minutes, just in case
		server.idle_done()

def handle_imip_response(message):
	handled = False

	try:
		for part in message.walk():
			if part.get_content_type().lower() == "text/calendar":
				is_reply = False

				if part.get_param("method", "DUMMY").lower() == "reply":
					is_reply = True
				
				## Simplified logic for now: If there's a vevent in there and its UID matches a recipient
				##  accept that as a response

				cal = vobject.readOne(part.get_payload(None, True))

				if cal.method and cal.method.value.lower() == "reply":
					is_reply = True

				if not is_reply:
					continue

				uid = cal.vevent.uid.value

				recipient = Recipient.query.filter(Recipient.id==uuid.UUID(uid)).first()

				if recipient:
					handled = True

					## More simplifications: Use the first attendee
					partstat = cal.vevent.attendee.partstat_param
					if partstat.lower() == "accepted":
						recipient.accept = AcceptState.YES
					elif partstat.lower() == "declined":
						recipient.accept = AcceptState.NO
					else:
						current_app.logger.warn("Unknown partstat for %s, while handling %s: %s", cal.vevent.attendee, uid, partstat)
						return False

					current_app.logger.info("Setting %s for %s as %s", cal.vevent.attendee, uid, recipient.accept)

					recipient.accept_type = AcceptType.EMAIL
					recipient.accept_time = datetime.datetime.utcnow()
					db.session.commit()
	finally:
		db.session.rollback()


	return handled

