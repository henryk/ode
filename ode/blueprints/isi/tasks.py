from __future__ import absolute_import

from ode import cel, db, create_signer
from .model import Invitation, Recipient, Source
from .imip_integration import send_imip_invitation
from flask import current_app, url_for, render_template_string

import datetime, vobject, flanker.addresslib.address


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

		retval = send_imip_invitation(invitation.event._vevent, recipient_address, recipient.id, **params)

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
