from flask import Blueprint, g, render_template, request, url_for, redirect
from sqlalchemy.sql.expression import true
from sqlalchemy.sql import func

from dnsforever.web.tools.session import login, get_user
from dnsforever.models import Domain, RecordA, RecordAAAA, RecordCNAME
from dnsforever.models import RecordMX, RecordTXT
import re

DOMAIN_PATTERN = re.compile('^([a-z0-9\-]+\.)+([a-z0-9\-]+)$')

app = Blueprint('domain', __name__, url_prefix='/domain')


@app.route('/')
@login(True, '/')
def index():
    count = lambda type, label: g.session\
                                 .query(type.domain_id,
                                        func.count(type.id).label(label))\
                                 .group_by(type.domain_id).subquery()

    count_a = count(RecordA, 'count_a')
    count_ddns = g.session.query(RecordA.domain_id,
                                 func.count(RecordA.id).label('count_ddns'))\
                          .group_by(RecordA.domain_id)\
                          .filter(RecordA.ddns == true()).subquery()
    count_aaaa = count(RecordAAAA, 'count_aaaa')
    count_cname = count(RecordCNAME, 'count_cname')
    count_mx = count(RecordMX, 'count_mx')
    count_txt = count(RecordTXT, 'count_txt')

    domain_list = g.session\
                   .query(Domain.domain.label('domain'),
                          count_a.c.count_a,
                          count_ddns.c.count_ddns,
                          count_aaaa.c.count_aaaa,
                          count_cname.c.count_cname,
                          count_mx.c.count_mx,
                          count_txt.c.count_txt)\
                   .outerjoin(count_a)\
                   .outerjoin(count_ddns)\
                   .outerjoin(count_aaaa)\
                   .outerjoin(count_cname)\
                   .outerjoin(count_mx)\
                   .outerjoin(count_txt)\
                   .filter(Domain.owner == get_user()).all()

    return render_template('dashboard.html', domain_list=domain_list)


@app.route('/new', methods=['GET'])
@login(True, '/')
def new():
    return render_template('domain_new.html')


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

        try:
            with g.session.begin():
                g.session.add(Domain(domain=domain.lower(), owner=get_user()))
        except:
            error_domains.append(domain)

    if len(error_domains) > 0:
        return render_template('domain_new.html',
                               error_domains=error_domains,
                               domains=domains)

    return redirect(url_for('domain.index'))


@app.route('/<string:domain>', methods=['GET', 'POST'])
@login(True, '/')
def detail(domain):
    domain = g.session.query(Domain).filter(Domain.domain.like(domain))\
                                    .filter(Domain.owner == get_user())\
                                    .first()
    if not domain:
        return redirect(url_for('domain.index'))

    return render_template('domain_detail.html', domain=domain)
