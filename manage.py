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

if __name__ == "__main__":
	manager.run()
