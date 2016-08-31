from __future__ import absolute_import

from flask import g, session

from flask_bootstrap.nav import BootstrapRenderer
from flask_nav.elements import Navbar, View, Subgroup, Text

from ode import nav

@nav.navigation("top")
def top_navbar():
	return ODENavbar()

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

class ODENavbar(Navbar):
	def __init__(self, title=None, *args):
		if title is not None:
			title = 'ODE > %s' % title
		else:
			title = 'ODE'
		super(ODENavbar, self).__init__(title, *args)
		self.items = self.items + (UserMenu(),)

class ODENavbarRenderer(BootstrapRenderer):

	# This is a copy of BootstrapRenderer.visit_Navbar, but not as stupid
	#  + Customize Brand (make dropdown of modules)
	#  * Fix to top
	#  * Put UserMenu into a right-aligned menu
	def visit_Navbar(self, node):
		from dominate import tags
		from hashlib import sha1
		
		# create a navbar id that is somewhat fixed, but do not leak any
		# information about memory contents to the outside
		node_id = self.id or sha1(str(id(node)).encode()).hexdigest()

		root = tags.nav() if self.html5 else tags.div(role='navigation')
		root['class'] = 'navbar navbar-default navbar-fixed-top'

		cont = root.add(tags.div(_class='container-fluid'))

		# collapse button
		header = cont.add(tags.div(_class='navbar-header'))
		btn = header.add(tags.button())
		btn['type'] = 'button'
		btn['class'] = 'navbar-toggle collapsed'
		btn['data-toggle'] = 'collapse'
		btn['data-target'] = '#' + node_id
		btn['aria-expanded'] = 'false'
		btn['aria-controls'] = 'navbar'

		btn.add(tags.span('Toggle navigation', _class='sr-only'))
		btn.add(tags.span(_class='icon-bar'))
		btn.add(tags.span(_class='icon-bar'))
		btn.add(tags.span(_class='icon-bar'))

		header.add(tags.span(node.title, _class='navbar-brand'))
				

		bar = cont.add(tags.div(
			_class='navbar-collapse collapse',
			id=node_id,
		))
		bar_list = bar.add(tags.ul(_class='nav navbar-nav'))

		right_items = []

		for item in node.items:
			if isinstance(item, UserMenu):
				right_items.append(item)
			else:
				bar_list.add(self.visit(item))

		if right_items:
			right_list = bar.add(tags.ul(_class='nav navbar-nav navbar-right'))

			for item in right_items:
				right_list.add(self.visit(item))

		return root
