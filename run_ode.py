#!/usr/bin/env python

from ode import create_app

app = create_app()

if __name__ == "__main__":
	app.run(threaded=True)

