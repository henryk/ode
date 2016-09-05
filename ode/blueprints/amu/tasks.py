from __future__ import absolute_import

from ode import cel, db
from ode.model import MailingList
from flask import current_app

import requests

BLACKLIST_LIST_NAMES = ["mailman"]

def api_url(s):
	base = current_app.config["AMU_MAILMAN_API_URL"]
	if base.endswith("/"):
		base = base[:-1]
	if s.startswith("/"):
		s = s [1:]

	return base + "/" + s

def do_create_ldap_list(list_name):
	# HACK For some reason a new object has the properties of the last object created
	#  Work around that
	ml = MailingList(name = list_name, additional_addresses = [], member_urls = [], members = [])
	users = requests.get(api_url("/" + list_name + "?name=1")).json()

	user_list = [ (u"%s <%s>" % (u[1], u[0])) if u[1] else u[0]  for u in users ]

	ml.import_list_members(user_list)

	current_app.logger.debug("List now %s", ml.to_json())
	ml.save()


@cel.task
def sync_mailing_lists():
	ldap_lists = dict( (unicode(ml.name).lower(), ml) for ml in  MailingList.query.all() )
	mm_lists = requests.get(api_url("/")).json()

	# 1. Never create lists in mailman
	# 2. Don't change members on existing lists for now (needs to keep last state)

	for ln in [ln for ln in mm_lists if not ln.lower() in ldap_lists.keys() and not ln.lower() in BLACKLIST_LIST_NAMES]:
		do_create_ldap_list(ln)

