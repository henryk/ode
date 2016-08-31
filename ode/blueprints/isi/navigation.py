from __future__ import absolute_import

from flask import g, session

from flask_nav.elements import Navbar, View, Subgroup

from ode import nav
from ode.navigation import UserMenu

@nav.navigation("isi")
def isi_navbar():
	e = [
		'ISI',
	]
	e.append(UserMenu())
	return Navbar(*e)
