#!/usr/bin/env python

from amu import create_app

app = create_app()

if __name__ == "__main__":
	app.run(threaded=True)

