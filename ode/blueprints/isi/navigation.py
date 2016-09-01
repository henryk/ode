from __future__ import absolute_import

from flask import g, session

from flask_nav.elements import Navbar, View, Subgroup

from ode import nav
from ode.navigation import ODENavbar

@nav.navigation("isi")
def isi_navbar():
	e = [
		View('Event list', '.event_list')
	]
	return ODENavbar(*e)
