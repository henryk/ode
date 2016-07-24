from amu import config_get, ldap

class User(ldap.Entry):
    object_classes = ['inetOrgPerson']

    name = ldap.Attribute('cn')
    userid = ldap.Attribute('uid')
    surname = ldap.Attribute('sn')
    givenname = ldap.Attribute('givenName')

    groups = ldap.Attribute('memberOf')

class Group(ldap.Entry):
	object_classes = ['groupOfNames']

	name = ldap.Attribute('cn')
	members = ldap.Attribute('member')

def initialize(app):
	User.base_dn = config_get("AMU_USER_BASE", config=app.config)
	Group.base_dn = config_get("AMU_GROUP_BASE", config=app.config)
