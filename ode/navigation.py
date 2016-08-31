from __future__ import absolute_import

from flask import current_app, g, session, request

from flask_bootstrap.nav import BootstrapRenderer
from flask_nav.elements import Navbar, View, Subgroup, Text, NavigationItem
from dominate import tags
from hashlib import sha1

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

class ActiveView(View):
	@property
	def active(self):
		return True

class InactiveView(View):
	@property
	def active(self):
		return False
	

class ActiveModuleBrand(Subgroup):
	def __init__(self):
		super(ActiveModuleBrand, self).__init__('ODE', 
			*[InactiveView(*_) for _ in current_app.config["ODE_MODULES"]]
		)

		# Find active module by longest prefix match
		active = None
		longest = ""
		url = request.path
		for item in self.items:
			module_url = item.get_url()
			if url.startswith(module_url) and len(module_url) > len(longest):
				active = item
				longest = module_url

		if active:
			self.title = active.text
			active.__class__ = ActiveView


class ODENavbar(Navbar):
	def __init__(self, *args):
		super(ODENavbar, self).__init__(None, *args)
		self.items = (ActiveModuleBrand(),) + self.items + (UserMenu(),)

class ODENavbarRenderer(BootstrapRenderer):

	# This is a copy of BootstrapRenderer.visit_Navbar, but not as stupid
	#  * Allow Brand customization
	#  * Make dropdown of registered modules
	#  * Fix to top
	#  * Put UserMenu into a right-aligned menu
	#  * De-bogonify: Remove all href="#" from a
	def visit_Navbar(self, node):

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

		if node.title:
			header.add(self.visit(node.title))

		bar = cont.add(tags.div(
			_class='navbar-collapse collapse',
			id=node_id,
		))
		bar_list = bar.add(tags.ul(_class='nav navbar-nav'))

		right_items = []

		for item in node.items:
			if isinstance(item, UserMenu):
				right_items.append(item)
			elif isinstance(item, ActiveModuleBrand):
				brand = self.visit(item)
				brand.__class__ = tags.div
				brand['class'] += ' navbar-brand'
				header.add( brand )
			else:
				bar_list.add(self.visit(item))

		if right_items:
			right_list = bar.add(tags.ul(_class='nav navbar-nav navbar-right'))

			for item in right_items:
				right_list.add(self.visit(item))

		for a in root.get("a"):
			if a["href"] == "#":
				del a["href"]

		return root

