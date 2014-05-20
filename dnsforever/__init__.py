from flask import Flask, g

from dnsforever.models import Session
from dnsforever.tools.session import get_user


blueprints = ['index', 'account', 'domain',
              'domain_a', 'domain_aaaa', 'domain_cname', 'domain_mx',
              'domain_txt']


def create_app():
    app = Flask(__name__)
    app.secret_key = 'SECRET_KEY'

    for name in blueprints:
        app.register_blueprint(load_blueprint(name))

    @app.before_request
    def define_session():
        g.session = Session()

        # TODO: load user info
        g.user = get_user()
        # TODO: load domain list
        if g.user:
            g.domain_list = [domain.domain for domain in g.user.domain]
        else:
            g.domain_list = []

    return app


def load_blueprint(name):
    module = __import__('dnsforever.' + name, None, None, ['app'])
    blueprint = getattr(module, 'app')
    return blueprint
