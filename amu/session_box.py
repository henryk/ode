import nacl.utils, nacl.secret, nacl.exceptions, nacl.hash, nacl.encoding
from flask import session, current_app

def init_box(app):
	if not "SESSION_BOX" in app.config:
		if app.config.get("DEBUG", False):
			key = nacl.hash.sha256("SESSION_BOX %s" % app.config.get("SECRET_KEY"), nacl.encoding.RawEncoder)
		else:
			key = nacl.utils.random(nacl.secret.SecretBox.KEY_SIZE)
		box = nacl.secret.SecretBox(key)
		app.config["SESSION_BOX"] = box

def store_boxed(key, value):
	assert isinstance(value, unicode)
	nonce = nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE)
	session[key] = current_app.config["SESSION_BOX"].encrypt(value.encode("UTF-8"), nonce)

def retrieve_unboxed(key, default=Ellipsis):
	if default is Ellipsis:
		value = session[key]
		value = current_app.config["SESSION_BOX"].decrypt(value)
	else:
		if key in session:
			value = session[key]
		else:
			return default

		try:
			value = current_app.config["SESSION_BOX"].decrypt(value)
		except (nacl.exceptions.CryptoError,ValueError):
			# Ignore exception, return default
			return default

	return value.decode("UTF-8")
