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
	object_classes = ['inetOrgPerson', 'CC-person']
	entry_rdn = ['uid', 'base_dn']

	name = ldap.Attribute('cn')
	userid = ldap.Attribute('uid')
	surname = ldap.Attribute('sn')
	givenname = ldap.Attribute('givenName')
	password = LDAPSSHAPasswordAttribute('userPassword')

	mail = ldap.Attribute('CC-preferredMail')
	_aliases = ldap.Attribute('CC-mailAlias')
	groups = ldap.Attribute('memberOf')

	def save_groups(self, new_groups, group_list):
		add_list = [group for group in group_list if group.dn in new_groups and self.dn not in group.members]
		del_list = [group for group in group_list if group.dn not in new_groups and self.dn in group.members]

		## Since flask_ldapconn sucks with respect to these kinds of modifications
		## we do them ourselves through ldap3

		result = True
		for group in add_list:
			result = group.add_member(self.dn) and result
		for group in del_list:
			result = group.remove_member(self.dn) and result
		return result

	@property
	def aliases(self):
		try:
			return ",".join(self._aliases or [])
		except TypeError:
			return ""
	

	def set_aliases(self, new_aliases):
		self._aliases = [_.strip() for _ in new_aliases.split(",")]

class Group(ldap.Entry):
	object_classes = ['groupOfNames']
	entry_rdn = ['cn', 'base_dn']

	name = ldap.Attribute('cn')
	members = ldap.Attribute('member')

	def remove_member(self, dn):
		return self.connection.connection.modify(self.dn, {
			"member": [
				("MODIFY_DELETE", [dn])
			]
		})

	def add_member(self, dn):
		return self.connection.connection.modify(self.dn, {
			"member": [
				("MODIFY_ADD", [dn])
			]
		})

	def set_members(self, dnlist):
		add_list = [dn for dn in dnlist if dn not in self.members]
		del_list = [dn for dn in self.members if dn not in dnlist]

		changes = []
		if add_list: changes.append( ("MODIFY_ADD", add_list) )
		if del_list: changes.append( ("MODIFY_DELETE", del_list) )

		if not changes: 
			return True

		return self.connection.connection.modify(self.dn, {
			"member": changes
		})

class MailingList(ldap.Entry):
	object_classes = ['CC-mailingList']
	entry_rdn = ['cn', 'base_dn']

	name = ldap.Attribute('cn')
	members = ldap.Attribute('member')
	additional_addresses = ldap.Attribute('CC-fullMailAddress')
	member_urls = ldap.Attribute('CC-memberURL')

	@property
	def member_urls_group(self):
		return [_ for _ in self.member_urls if "memberOf=" in _] # FIXME: Can this be more elegant?

	@property
	def member_urls_user(self):
		return [_ for _ in self.member_urls if "memberOf=" not in _] # FIXME: Can this be more elegant?
	

def initialize(app):
	User.base_dn = config_get("AMU_USER_BASE", config=app.config)
	Group.base_dn = config_get("AMU_GROUP_BASE", config=app.config)
	MailingList.base_dn = config_get("AMU_MAILING_LIST_BASE", config=app.config)
