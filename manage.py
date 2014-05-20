#!/usr/bin/env python
from flask.ext.script import Manager
from dnsforever import create_app
from dnsforever.models import Base, engine

app = create_app()
manager = Manager(app)


@manager.command
def run():
    app.run(debug=True, use_reloader=True)


@manager.command
def run_public(port=7000):
    app.run(debug=True, use_reloader=True, host='0.0.0.0', port=int(port))


@manager.command
def initdb():
    Base.metadata.create_all(engine)


@manager.command
def dropdb():
    Base.metadata.drop_all(engine)

if __name__ == '__main__':
    manager.run()
