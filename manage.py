#!/usr/bin/env python
from __future__ import absolute_import

from flask_script import Manager
from flask_migrate import MigrateCommand

from ode import create_app

manager = Manager(create_app)

manager.add_command('db', MigrateCommand)

if __name__ == "__main__":
	manager.run()
