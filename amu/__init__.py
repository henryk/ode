from flask import Flask

from flask_bootstrap import Bootstrap
from flask_session import Session

bs = Bootstrap()
_s = Session()

def create_app(configuration="amu.config.DevelopmentConfig", **kwargs):
    app = Flask(__name__)

    app.config.from_object(configuration)
    app.config.from_envvar('AMU_SETTINGS', silent=True)
    app.config.update(kwargs)

    bs.init_app(app)
    _s.init_app(app)

    from amu.views import views
    app.register_blueprint(views)

    return app

import amu.views
