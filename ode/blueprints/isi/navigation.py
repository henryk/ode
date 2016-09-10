from __future__ import absolute_import

from flask import g, session

from flask_nav.elements import Navbar, View, Subgroup

from ode import nav
from ode.navigation import ODENavbar

from flask_babel import _

@nav.navigation("isi")
def isi_navbar():
	e = [
		View( _('Event list'), '.event_list')
	]
	return ODENavbar(*e)
