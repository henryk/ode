from __future__ import absolute_import

from flask import g, session

from flask_nav.elements import Navbar, View, Subgroup

from ode import nav
from ode.navigation import ODENavbar, ODENavbarRenderer

from flask_babel import _

@nav.navigation("amu")
def amu_navbar():
	e = []
	if hasattr(g, "ldap_user"):
		if session.get("is_admin", False):
			e.extend( [
				View(_('Users'), '.users'),
				View(_('New user'), '.new_user'),
				View(_('Groups'), '.groups'),
				View(_('New group'), '.new_group'),
				View(_('Mailing Lists'), '.mailing_lists'),
				View(_('New mailing list'), '.new_mailing_list'),
			] )
	return ODENavbar(*e)

class AMUNavbarRenderer(ODENavbarRenderer):
	# Change links to .../_new to + icons
	def visit_Navbar(self, node):
		import dominate

		result = super(AMUNavbarRenderer, self).visit_Navbar(node)
		div = None
		child = None
		for O in result.get("div"):
			if "navbar-collapse" in O['class']:
				div = O
				break

		if div:
			for O in div.get("ul"):
				ul = O
				break
			for li in ul.get("li"):
				a = None
				for a in li.get("a"):
					pass
				if a is not None:
					if a['href'].endswith("/_new"):
						old_text = a[0]
						del a[0]
						a += dominate.tags.span(_class="glyphicon glyphicon-plus-sign")
						a += dominate.tags.span(old_text, _class="sr-only")
						a.parentNode['class'] = getattr(a.parentNode,'class', '') + " navigation-add-object"

		return result
