from __future__ import absolute_import

from ode import cel, db, create_serializer
from .model import Invitation, Recipient
from flask import current_app, url_for

@cel.task
def send_mails(invitation_id):
	invitation = Invitation.query.filter(Invitation.id==invitation_id).one()

	for recipient in invitation.recipients:
		if recipient.state is recipient.state.PENDING:
			send_one_mail.apply_async( (recipient.id,) )

@cel.task
def send_one_mail(recipient_id):
	recipient = Recipient.query.filter(Recipient.id==recipient_id).one()

	serializer = create_serializer(salt="rsvp_mail")

	param_yes = serializer.dumps([str(recipient.id), 1])
	param_no = serializer.dumps([str(recipient.id), 0])

	link_yes = url_for('isi.rsvp', param=param_yes, _external=True)
	link_no = url_for('isi.rsvp', param=param_no, _external=True)

	current_app.logger.debug("Yes: %s,  No: %s", link_yes, link_no)

	recipient.state = recipient.state.SENT
	db.session.commit()
