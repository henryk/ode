#!/usr/bin/env python
from __future__ import absolute_import

from flask_script import Manager
from flask_migrate import MigrateCommand

from ode import create_app
from ode.blueprints.isi.imip_integration import receive_mails

manager = Manager(create_app)

manager.add_command('db', MigrateCommand)

@manager.command
def run_imip_receive():
	"Run the iMIP receiver"
	receive_mails()

@manager.command
def mm_sync():
	"Schedule synchronization of MailMan mailing lists with MailingList objects"
	from ode.blueprints.amu import tasks
	tasks.sync_mailing_lists.apply_async()

@manager.command
def run_isi_midnight():
	"Run the ISI midnight task"
	from ode.blueprints.isi import tasks
	tasks.refresh_midnight.apply_async()

if __name__ == "__main__":
	manager.run()
