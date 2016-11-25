from __future__ import absolute_import

from ode import mailer
from .utils import NonStupidMessage
from flask import render_template

import flanker.addresslib.address, datetime

from flask_babel import _


def send_update_notification(invitation, now):
	# Go through all the recipients of invitation, and see if 
	# a status change has happened in the last day (24*60*60 + 15 seconds)
	cutoff_time = now - datetime.timedelta(seconds=24*60*60 + 15)

	have_change = any(recipient.accept_time and (recipient.accept_time >= cutoff_time) for recipient in invitation.recipients)
	if have_change:
		sender_address = flanker.addresslib.address.parse(invitation.sender)
		recipients = [flanker.addresslib.address.parse(r).full_spec() for r in invitation.owners]

		template_params = dict(invitation=invitation, event=invitation.event)
		params = dict(sender=sender_address.full_spec(),
			subject=_("Updates for '%s'") % invitation.subject)

		params["html"] = render_template("isi/update_notification_mail.html", **template_params)
		params["charset"] = "UTF-8"

		msg = NonStupidMessage(recipients=recipients, **params)
		retval = mailer.send(msg)
