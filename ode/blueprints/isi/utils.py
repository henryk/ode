from flask_mail import Message

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

