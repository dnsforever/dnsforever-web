from flask import session, redirect, g
from functools import wraps

from dnsforever.models import User, Domain, DomainOwnership


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


def get_domain(domain, master=False):
    if not get_user():
        return None

    query = g.session.query(Domain, DomainOwnership)
    query = query.join(DomainOwnership.domain)
    query = query.filter(Domain.name.like(domain))
    query = query.filter(DomainOwnership.user_id == get_user().id)
    if master:
        query = query.filter(DomainOwnership.master)

    if query.count() == 0:
        return None

    domain, ownership = query.first()

    domain.master = ownership.master

    return domain
