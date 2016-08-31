from __future__ import absolute_import

from flask import g, session

from flask_nav.elements import Navbar, View, Subgroup

from ode import nav
from ode.navigation import ODENavbar, ODENavbarRenderer

@nav.navigation("amu")
def amu_navbar():
	e = [
		'AMU',
	]
	if hasattr(g, "ldap_user"):
		if session.get("is_admin", False):
			e.extend( [
				View('Users', '.users'),
				View('New user', '.new_user'),
				View('Groups', '.groups'),
				View('New group', '.new_group'),
				View('Mailing Lists', '.mailing_lists'),
				View('New mailing list', '.new_mailing_list'),
			] )
	return ODENavbar(*e)

class AMUNavbarRenderer(ODENavbarRenderer):
	# Change "New " to + icons
	def visit_Navbar(self, node):
		import dominate

		result = super(AMUNavbarRenderer, self).visit_Navbar(node)
		div = None
		child = None
		for _ in result.get("div"):
			if "navbar-collapse" in _['class']:
				div = _
				break

		if div:
			for _ in div.get("ul"):
				ul = _
				break
			for li in ul.get("li"):
				a = None
				for a in li.get("a"):
					pass
				if a is not None:
					if a[0].startswith("New "):
						old_text = a[0]
						del a[0]
						a += dominate.tags.span(_class="glyphicon glyphicon-plus-sign")
						a += dominate.tags.span(old_text, _class="sr-only")
						a.parentNode['class'] = getattr(a.parentNode,'class', '') + " navigation-add-object"

		return result
