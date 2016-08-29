# -*- coding: utf-8 -*-

AMU_BASE_DN = "dc=example,dc=com"
AMU_USER_BASE = "ou=Users,%(AMU_BASE_DN)s"
AMU_GROUP_BASE = "ou=Groups,%(AMU_BASE_DN)s"
AMU_MAILING_LIST_BASE = "ou=Mailing Lists,%(AMU_BASE_DN)s"
AMU_USER_DN = "uid=%(username)s,ou=Users,%(AMU_BASE_DN)s"
AMU_ALLOW_DIRECT_DN = True
LDAP_SERVER = 'localhost'
LDAP_PORT = 389
LDAP_TIMEOUT = 10
LDAP_USE_TLS = True  # default
LDAP_REQUIRE_CERT = ssl.CERT_NONE  # default: CERT_REQUIRED
LDAP_TLS_VERSION = ssl.PROTOCOL_TLSv1_2  # default: PROTOCOL_TLSv1
LDAP_CERT_PATH = '/etc/openldap/certs'

MAIL_SERVER = 'mail.example.com'

AMU_USERMODMAIL = dict(
	sender = u"The Management <mgmt@example.com>",
	subject = u"Your account at example.com",
	body = u"""Your account at example.com has been created or changed:

 Benutzername: {{ user.userid }}
 Passwort:     {{ form.password.data }}

You can, and should, change your password at
  https://example.com/selfservice/

You can find more information at
  https://wiki.example.com/

Yours truly,
  {{ g.ldap_user.name }}
"""
)