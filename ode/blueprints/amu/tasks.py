from __future__ import absolute_import

from ode import cel

from .mailman_integration import execute_sync

@cel.task
def sync_mailing_lists():
	execute_sync()