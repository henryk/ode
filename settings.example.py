AMU_BASE_DN = "dc=example,dc=com"
AMU_BIND_DN = "uid=%(username)s,ou=Users,%(base_dn)s"
LDAP_SERVER = 'localhost'
LDAP_PORT = 389
LDAP_TIMEOUT = 10
LDAP_USE_TLS = True  # default
LDAP_REQUIRE_CERT = ssl.CERT_NONE  # default: CERT_REQUIRED
LDAP_TLS_VERSION = ssl.PROTOCOL_TLSv1_2  # default: PROTOCOL_TLSv1
LDAP_CERT_PATH = '/etc/openldap/certs'
