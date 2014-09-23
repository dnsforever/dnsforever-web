from flask import Blueprint, g, render_template, request, url_for, redirect

from dnsforever.domain import ROOT_DOMAIN
from dnsforever.web.tools.session import login, get_user, get_domain
from dnsforever.models import Domain, DomainOwnership
import re
import string

DOMAIN_PATTERN = re.compile('^([a-z0-9\-]+\.)+([a-z0-9\-]+)$')

app = Blueprint('domain', __name__, url_prefix='/domain')


@app.route('/')
@login(True, '/')
def index():
    return render_template('dashboard.html', ownership_list=g.user.ownership)


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
