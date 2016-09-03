from __future__ import absolute_import

from ode import cel

@cel.task
def foo(a):
	current_app.logger.debug("Doing foo")
	return a
