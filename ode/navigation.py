from __future__ import absolute_import

from flask import g, session

from flask_bootstrap.nav import BootstrapRenderer
from flask_nav.elements import Navbar, View, Subgroup

from ode import nav

@nav.navigation("top")
def top_navbar():
	e = [
		'ODE',
	]
	if hasattr(g, "ldap_user"):
		e.extend( [
			Subgroup('Logged in as %s' % g.ldap_user.name,
				View('My profile', 'amu.self'),
				View('Log out', 'logout')
			)
		] )
	return Navbar(*e)

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
