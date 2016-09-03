from __future__ import absolute_import

from ode import cel, db
from .model import Invitation, Recipient
from flask import current_app

@cel.task
def send_mails(invitation_id):
	invitation = Invitation.query.filter(Invitation.id==invitation_id).one()

	for recipient in invitation.recipients:
		if recipient.state is recipient.state.PENDING:
			send_one_mail.apply_async( (recipient.id,) )

@cel.task
def send_one_mail(recipient_id):
	recipient = Recipient.query.filter(Recipient.id==recipient_id).one()

	recipient.state = recipient.state.SENT
	db.session.commit()
