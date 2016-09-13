from __future__ import absolute_import

from ode.model import MailingList
from flask import current_app

from contextlib import contextmanager

import requests, filelock, os.path, shelve, time, flanker.addresslib.address, enum

BLACKLIST_LIST_NAMES = ["mailman"]

class SyncMessage(enum.Enum):
	CONFLICT = "conflict"
	ON_LDAP_NOT_ON_MM = "on-ldap-not-on-mm"

def api_url(s):
	base = current_app.config["AMU_MAILMAN_API_URL"]
	if base.endswith("/"):
		base = base[:-1]
	if s.startswith("/"):
		s = s [1:]

	return base + "/" + s

def get_mailman_members(ln):
	users = requests.get(api_url("/" + ln + "?name=1")).json()

	user_list = [ (u"%s <%s>" % (u[1], u[0])) if u[1] else u[0]  for u in users ]

	return user_list
	

@contextmanager
def sync_state(writeback=False):
	lock = filelock.FileLock( os.path.join(current_app.instance_path, "sync_mailing_lists_lock") )

	with lock:
		sync_state = shelve.open( os.path.join(current_app.instance_path, "sync_mailing_lists_state"),  writeback=writeback )
		try:
			yield sync_state
		finally:
			sync_state.close()


def normalize_list(l):
	n = set()

	for a in l:
		if not isinstance(a, flanker.addresslib.address.EmailAddress):
			a = flanker.addresslib.address.parse(a)
		if a:
			n.add(a.address.lower())
		else:
			current_app.logger.warning("Skipped processing of %s because of invalid format", a)

	return n

def compare_lists(a, b):
	a = normalize_list(a)
	b = normalize_list(b)

	return a.difference(b), b.difference(a)

def remove_list_from_ldap(ml):
	current_app.logger.info("Delete %s on LDAP", ml)
	ml.delete()
	return True

def remove_list_from_mailman(ln, existing_members):
	current_app.logger.info("Delete %s on Mailman", ln)
	for address in normalize_list(existing_members):
		data = {"address": address }
		requests.delete( api_url("/" + ln), data=data )
	return True

def copy_list_to_mailman(ln, new_users):
	current_app.logger.info("Creating %s on Mailman: %s", ln, new_users)

	added = []
	for address in new_users:
		data = {"address": address.address}
		if address.display_name:
			data["fullname"] = address.display_name
		requests.put( api_url("/" + ln), data=data )
		added.append( address.address.lower() )

	return normalize_list(added)
	

def copy_list_to_ldap(ln, new_users):
	current_app.logger.info("Creating %s on LDAP: %s", ln, new_users)
	# HACK For some reason a new object has the properties of the last object created
	#  Work around that
	ml = MailingList(name = ln, additional_addresses = [], member_urls = [], members = [])

	ml.import_list_members(new_users)

	current_app.logger.debug("List now %s", ml.to_json())
	ml.save()

	return normalize_list(new_users)

def sync_lists(ln, ld, mm, st):
	current_app.logger.info("Would sync list: %s", ln)

	ld_m = normalize_list(ld.as_addresses)
	mm_m = normalize_list(mm)
	st_m = normalize_list(st)

	codes = {}
	for i in range(8):
		codes[i] = set()

	for m in ld_m.union(mm_m).union(st_m):
		code = 0
		code |=  1 if  m in st_m  else 0
		code |=  2 if  m in mm_m  else 0
		code |=  4 if  m in ld_m  else 0
		codes[code].add(m)

	# 001  1: in neither, but in state: remove from state
	# 010  2: in mm, not in ldap or state: add to state and ldap
	# 011  3: in mm, and in state: remove from state and mm
	# 100  4: in ldap, not in mm or state: add to state and mm
	# 101  5: in ldap, and in state: remove from state and ldap
	# 110  6: in ldap and in mm, not in state: add to state
	# 111  7: everywhere, don't do anything

	add_to_ldap = codes[2]
	add_to_mm =   codes[4]
	remove_ldap = codes[5]
	remove_mm =   codes[3]

	add_to_state = codes[2].union(codes[4]).union(codes[6])
	remove_state = codes[1].union(codes[3]).union(codes[5])

	current_app.logger.info("Proposed changes: add to state %s, remove from state %s, add ldap %s, remove ldap %s, add mm %s, remove mm %s", 
		add_to_state, remove_state, add_to_ldap, remove_ldap, add_to_mm, remove_mm)

	after_st = st_m.union(add_to_state).difference(remove_state)
	after_ld = ld_m.union(add_to_ldap).difference(remove_ldap)
	after_mm = mm_m.union(add_to_mm).difference(remove_mm)

	current_app.logger.info("State after: state: %s, ldap: %s, mm %s", after_st, after_ld, after_mm)

	assert after_st == after_mm
	assert after_st == after_ld

	return list(after_st)


def execute_sync():
	with sync_state(writeback=True) as state:
		now = time.time()

		if "last_time" in state:
			# 1. Only do the synchronization once per 10s
			if now - state["last_time"] < 10:
				return

		state["last_time"] = now


		ldap_state = dict( (unicode(ml.name).lower(), ml) for ml in  MailingList.query.all() )
		mm_state = dict( (ln, get_mailman_members(ln)) for ln in  requests.get(api_url("/")).json()  if not ln.lower() in BLACKLIST_LIST_NAMES )
		state_state = state.setdefault("state", {})

		ldap_lists = ldap_state.keys()
		mm_lists = [ k for k in mm_state.keys() if mm_state[k] ]
		state_lists = state_state.keys()
		sync_problems = {}
		state["sync_problems"] = sync_problems


		# 2. Never create lists in mailman, but possibly populate existing list
		# 3. When deleting list from mailman: remove all members, do not actually delete list
		# 4. Treat mailman list without members as "does not exist" for list existence check, but as empty for member updates
		# 5. If list exists on both ldap and mm, but not in state:
		#  5a. If lists are identical: add to state
		#  5b. Else, emit error, do nothing (must manually resolve)
		# 6. If list exists on either ldap or mm, and in state: remove from other and state
		# 7. If list exists on either ldap or mm, and not in state: copy to other and state
		# 8. If list exists in neither ldap nor mm, but in state: remove from state
		# 9. If list exists on both ldap and mm and in state, update members (comparison: case insensitive e-mail address):
		#  9a. Member in either, not in state: copy to other and state
		#  9b. Member in either, and in state: remove from other and state
		#  9c. Member in both, not in state: add to state

		all_lists = set(ldap_lists).union(set(mm_lists)).union(set(state_lists))

		for ln in all_lists:
			if ln.lower() in BLACKLIST_LIST_NAMES:
				continue

			if   ln     in ldap_lists and ln     in mm_lists     and ln not in state_lists: # 5
				ldap_addresses = ldap_state[ln].as_addresses
				add_left, add_right = compare_lists( ldap_addresses, mm_state[ln] )

				if not add_left and not add_right: # 5a
					state_state[ln] = normalize_list(ldap_addresses)
				else: # 5b
					sync_problems.setdefault(ln, []).append(SyncMessage.CONFLICT)

			elif ln     in ldap_lists and ln not in mm_lists     and ln     in state_lists: # 6  (1)
				if remove_list_from_ldap(ldap_state[ln]):
					del state_state[ln]

			elif ln not in ldap_lists and ln     in mm_lists     and ln     in state_lists: # 6  (2)
				if remove_list_from_mailman(ln, mm_state[ln]):
					del state_state[ln]

			elif ln     in ldap_lists and ln not in mm_lists     and ln not in state_lists:  # 7  (1)
				if ln in mm_state.keys():
					ldap_addresses = ldap_state[ln].as_addresses
					state_state[ln] = copy_list_to_mailman(ln, ldap_addresses)
				else:
					sync_problems.setdefault(ln, []).append(SyncMessage.ON_LDAP_NOT_ON_MM)
			
			elif ln not in ldap_lists and ln in     mm_lists     and ln not in state_lists:  # 7  (2)
				state_state[ln] = copy_list_to_ldap(ln, mm_state[ln])

			elif ln not in ldap_lists and ln not in mm_lists     and ln     in state_lists:  # 8
				del state_state[ln]

			elif ln     in ldap_lists and ln     in state_lists  and ln     in state_lists:  # 9
				state_state[ln] = sync_lists(ln, ldap_state[ln], mm_state[ln], state_state[ln])

		for k, v in sync_problems.items():
			current_app.logger.error("Sync problems while processing %s: %s", k, v)

