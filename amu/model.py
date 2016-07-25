from amu import config_get, ldap
from flask import current_app
from ldap3 import STRING_TYPES

# Hashes the password value into an {SSHA} password upon setting
class LDAPSSHAPasswordAttribute(ldap.Attribute):
	def __setattr__(self, key, value):
		if key in ['value', '_init']:
			if isinstance(value, STRING_TYPES) and not value.startswith("{"):
				import sha, os
				from base64 import b64encode
				salt = os.urandom(16)
				ctx = sha.new( value )
				ctx.update( salt )
				value = "{SSHA}" + b64encode( ctx.digest() + salt )

		super(LDAPSSHAPasswordAttribute, self).__setattr__(key, value)

class User(ldap.Entry):
	object_classes = ['inetOrgPerson']
	entry_rdn = ['uid', 'base_dn']

	name = ldap.Attribute('cn')
	userid = ldap.Attribute('uid')
	surname = ldap.Attribute('sn')
	givenname = ldap.Attribute('givenName')
	password = LDAPSSHAPasswordAttribute('userPassword')

	groups = ldap.Attribute('memberOf')

class Group(ldap.Entry):
	object_classes = ['groupOfNames']

	name = ldap.Attribute('cn')
	members = ldap.Attribute('member')

def initialize(app):
	User.base_dn = config_get("AMU_USER_BASE", config=app.config)
	Group.base_dn = config_get("AMU_GROUP_BASE", config=app.config)
