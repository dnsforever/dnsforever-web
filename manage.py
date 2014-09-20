#!/usr/bin/env python
from flask.ext.script import Manager
from dnsforever import web
from dnsforever.models import Base, engine
from dnsforever.web.tools import password_hash

app = web.create_app()
manager = Manager(app)


@manager.command
def run(host='127.0.0.1', port=5000):
    app.run(debug=True, use_reloader=True, host=host, port=port)


@manager.command
def initdb():
    Base.metadata.create_all(engine)


@manager.command
def dropdb():
    Base.metadata.drop_all(engine)

if __name__ == '__main__':
    manager.run()
