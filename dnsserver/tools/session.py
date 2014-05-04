from flask import session, redirect, g
from functools import wraps

from dnsserver.models import User


def set_user(user):
    if user is None:
        del session['user_id']
        return
    if not isinstance(user, User):
        raise TypeError
    session['user_id'] = user.id


def get_user():
    if 'user_id' not in session:
        return None
    if hasattr(g, 'user'):
        return g.user
    g.user = g.session.query(User).filter_by(id=session['user_id']).first()
    return g.user


def is_login():
    if get_user():
        return True
    return False


def login(state=True, redirect_url='/'):
    def dco_func(func):
        @wraps(func)
        def wrapper(*args, **xargs):
            if is_login() == state:
                return func(*args, **xargs)
            else:
                return redirect(redirect_url)
        return wrapper
    return dco_func
