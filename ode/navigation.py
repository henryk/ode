from __future__ import absolute_import

from flask import g, session

from flask_bootstrap.nav import BootstrapRenderer
from flask_nav.elements import Navbar, View, Subgroup, Text

from ode import nav

@nav.navigation("top")
def top_navbar():
	e = [
		'ODE',
		UserMenu(),
	]
	return Navbar(*e)

class UserMenu(object):
	def __new__(cls, *args, **kwargs):
		result = object.__new__(cls)
		if hasattr(g, "ldap_user"):
			result.__class__ = UserMenuLoggedIn
		else:
			result.__class__ = UserMenuLoggedOut
		return result

class UserMenuLoggedIn(UserMenu, Subgroup):
	def __init__(self):
		super(UserMenuLoggedIn, self).__init__('Logged in as %s' % g.ldap_user.name,
			View('My profile', 'amu.self'),
			View('Log out', 'logout'))

class UserMenuLoggedOut(UserMenu, Text):
	def __init__(self):
		super(UserMenuLoggedOut, self).__init__('Not logged in')

class ODENavbarRenderer(BootstrapRenderer):
	# Right-aligns last item
	# Fix to top
	def visit_Navbar(self, node):
		import dominate

		result = super(ODENavbarRenderer, self).visit_Navbar(node)
		div = None
		child = None
		for _ in result.get("div"):
			if "navbar-collapse" in _['class']:
				div = _
				break
		if div:

			for bar in div:
				pass
			for child in bar:
				pass
			if child:
				bar.remove(child)
				rightbar = dominate.tags.ul()
				rightbar['class'] = "nav navbar-nav navbar-right"
				div.add(rightbar)
				rightbar.add(child)

		result['class'] += " navbar-fixed-top"

		return result
