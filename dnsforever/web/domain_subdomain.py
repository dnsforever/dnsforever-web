from flask import Blueprint, g, render_template, request, url_for, redirect
from wtforms import Form, StringField, validators
from dnsforever.web.tools.session import login, get_domain, get_user
from dnsforever.models import Domain, SubdomainSharing

app = Blueprint('domain_subdomain', __name__,
                url_prefix='/domain/<string:domain>/subdomain')


@app.route('/')
@login(True, '/')
def subdomain_info(domain):
    domain = get_domain(domain, True)

    if not domain:
        return redirect(url_for('domain.index'))

    tickets = g.session.query(SubdomainSharing)\
                       .filter(SubdomainSharing.domain == domain)\
                       .all()

    subdomains = g.session.query(Domain)\
                          .filter(Domain.parent_id == domain.id)\
                          .all()

    return render_template('domain_subdomain/info.html',
                           domain=domain,
                           subdomains=subdomains,
                           tickets=tickets)


class SubdomainForm(Form):
    name = StringField('name',
                       [validators.Regexp('(^$)|'
                                          '(^([a-z0-9\-]+\.)*'
                                          '([a-z0-9\-]+)$)')])
    email = StringField('email', [validators.Email()])


@app.route('/new', methods=['GET'])
@login(True, '/')
def ticket_new(domain):
    domain = get_domain(domain, True)

    if not domain:
        return redirect(url_for('domain.index'))

    form = SubdomainForm()

    return render_template('domain_subdomain/new.html',
                           domain=domain,
                           form=form)


@app.route('/new', methods=['POST'])
@login(True, '/')
def ticket_new_process(domain):
    form = SubdomainForm(request.form)
    domain = get_domain(domain, True)

    if not domain:
        return redirect(url_for('domain.index'))

    if not form.validate():
        return render_template('domain_subdomain/new.html',
                               domain=domain,
                               form=form)

    if form.email.data == get_user().email:
        form.email.errors.append('Email error')
        return render_template('domain_subdomain/new.html',
                               domain=domain,
                               form=form)

    try:
        ticket = SubdomainSharing(domain=domain,
                                  name=form.name.data,
                                  email=form.email.data)

        with g.session.begin():
            g.session.add(ticket)
    except ValueError as e:
        form.name.errors.append(e)
        return render_template('domain_subdomain/new.html',
                               domain=domain,
                               form=form)

    return redirect(url_for('domain_subdomain.subdomain_info',
                            domain=domain.name))


@app.route('/ticket/<int:ticket_id>/del', methods=['GET', 'POST'])
@login(True, '/')
def ticket_delete(domain, ticket_id):
    domain = get_domain(domain, True)
    if not domain:
        return redirect(url_for('domain.index'))

    ticket = g.session.query(SubdomainSharing)\
                      .filter(SubdomainSharing.id == ticket_id)\
                      .filter(SubdomainSharing.domain == domain)\
                      .first()

    if not ticket:
        return redirect(url_for('domain_subdomain.subdomain_info',
                                domain=domain.name))

    if request.method == 'POST':
        with g.session.begin():
            g.session.delete(ticket)
        return redirect(url_for('domain_subdomain.subdomain_info',
                                domain=domain.name))

    return render_template('domain_subdomain/del.html',
                           domain=domain, ticket=ticket)


@app.route('/<int:subdomain_id>/del', methods=['GET', 'POST'])
@login(True, '/')
def subdomain_delete(domain, subdomain_id):
    domain = get_domain(domain, True)
    if not domain:
        return redirect(url_for('domain.index'))

    subdomain = g.session.query(Domain)\
                         .filter(Domain.id == subdomain_id)\
                         .filter(Domain.parent == domain)\
                         .first()

    if not subdomain:
        return redirect(url_for('domain_subdomain.subdomain_info',
                                domain=domain.name))

    if request.method == 'POST':
        with g.session.begin():
            g.session.delete(subdomain)
        return redirect(url_for('domain_subdomain.subdomain_info',
                                domain=domain.name))

    return render_template('domain_subdomain/del.html',
                           domain=domain, subdomain=subdomain)
