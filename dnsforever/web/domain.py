from flask import Blueprint, g, render_template, request, url_for, redirect

from dnsforever.domain import ROOT_DOMAIN
from dnsforever.web.tools.session import login, get_user, get_domain
from dnsforever.models import Domain, DomainOwnership, NameServer, \
    SubdomainSharing
import re
import string

DOMAIN_PATTERN = re.compile('^([a-z0-9\-]+\.)+([a-z0-9\-]+)$')

app = Blueprint('domain', __name__, url_prefix='/domain')


@app.route('/')
@login(True, '/')
def index():
    tickets = g.session.query(SubdomainSharing)\
                       .filter(SubdomainSharing.email.like(get_user().email))\
                       .all()
    ns_list = g.session.query(NameServer).all()
    return render_template('dashboard.html',
                           ns_list=ns_list,
                           ownership_list=g.user.ownership,
                           subdomain_tickets=tickets)


@app.route('/subdomain/<string:token>', methods=['GET'])
@login(True, '/')
def subdomain_add(token):
    ticket = g.session.query(SubdomainSharing)\
                      .filter(SubdomainSharing.token.like(token)).first()
    if not ticket:
        return redirect(url_for('domain.index'))

    if ticket.email and ticket.email != get_user().email:
        return redirect(url_for('domain.index'))

    subdomain_name = '%s.%s' % (ticket.name, ticket.domain.name)
    domain = Domain(name=subdomain_name, parent_id=ticket.domain.id)
    ownership = DomainOwnership(master=False, user=get_user(), domain=domain)

    with g.session.begin():
        g.session.add(domain)
        g.session.add(ownership)
        g.session.delete(ticket)
    return redirect(url_for('domain.index'))


@app.route('/subdomain/<string:token>/delete', methods=['GET'])
@login(True, '/')
def subdomain_delete(token):
    ticket = g.session.query(SubdomainSharing)\
                      .filter(SubdomainSharing.token.like(token)).first()
    if not ticket:
        return redirect(url_for('domain.index'))

    if ticket.email and ticket.email != get_user().email:
        return redirect(url_for('domain.index'))

    with g.session.begin():
        g.session.delete(ticket)

    return redirect(url_for('domain.index'))


@app.route('/new', methods=['GET'])
@login(True, '/')
def new():
    return render_template('domain_new.html')


def check_domain_owner(domain):
    if domain in ROOT_DOMAIN:
        return False
    domain = domain.split('.')
    for i in range(len(domain)):
        sub_domain = domain[i - len(domain):]
        sub_domain = string.join(sub_domain, '.')
        if g.session.query(Domain)\
                    .filter(Domain.name == sub_domain).count() > 0:
            return False
    return True


@app.route('/new', methods=['POST'])
@login(True, '/')
def new_process():
    if 'domain' in request.form:
        domains = request.form['domain'].split()
    else:
        domains = []

    error_domains = []
    for domain in domains:
        try:
            domain = str(domain)
        except:
            error_domains.append(domain)
            continue

        if not DOMAIN_PATTERN.match(domain.lower()):
            error_domains.append(domain)
            continue

        if check_domain_owner(domain) is False:
            error_domains.append(domain)
            continue

        try:
            with g.session.begin():
                domain = Domain(name=domain.lower())
                ownership = DomainOwnership(master=True,
                                            user=get_user(),
                                            domain=domain)
                g.session.add(ownership)
        except:
            error_domains.append(domain)
            continue

    if len(error_domains) > 0:
        return render_template('domain_new.html',
                               error_domains=error_domains,
                               domains=domains)

    return redirect(url_for('domain.index'))


@app.route('/<string:domain>', methods=['GET', 'POST'])
@login(True, '/')
def detail(domain):
    domain = get_domain(domain)

    if not domain:
        return redirect(url_for('domain.index'))

    return render_template('domain_detail.html', domain=domain)


@app.route('/<string:domain>/del', methods=['GET', 'POST'])
@login(True, '/')
def domain_delete(domain):
    domain = get_domain(domain)

    if not domain:
        return redirect(url_for('domain.index'))

    if request.method == 'POST':
        # TODO: Delete action need to solve ownership problem.
        # with g.session.begin():
        #     g.session.delete(domain)
        return redirect(url_for('domain.index'))

    return render_template('domain_del.html', domain=domain)
