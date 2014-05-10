from flask import Blueprint, g, render_template, request, url_for, redirect
from wtforms import Form, TextField, BooleanField, validators
from dnsserver.tools import random_string
from dnsserver.tools.session import login, get_user
from dnsserver.models import Domain, RecordA, RecordAAAA
import re

DOMAIN_PATTERN = re.compile('^([a-z0-9\-]+\.)+([a-z0-9\-]+)$')

app = Blueprint('domain', __name__, url_prefix='/domain')


@app.route('/')
@login(True, '/')
def index():
    domain_list = g.domain_list
    return render_template('domain.html', domain_list=domain_list)


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


@app.route('/<string:domain>/aaaa', methods=['GET', 'POST'])
@login(True, '/')
def record_aaaa(domain):
    domain = g.session.query(Domain).filter(Domain.domain.like(domain))\
                                    .filter(Domain.owner == get_user())\
                                    .first()
    if not domain:
        return redirect(url_for('domain.index'))

    records = g.session.query(RecordAAAA).filter(RecordAAAA.domain == domain)\
                                         .order_by(RecordAAAA.name).all()

    if not records:
        return redirect(url_for('domain.record_aaaa_new',
                                domain=domain.domain))

    return render_template('domain_aaaa/list.html',
                           domain=domain,
                           records=records)


class RecordAAAAForm(Form):
    name = TextField('name',
                     [validators.Regexp('(^$)|'
                                        '(^([a-z0-9\-]+\.)*([a-z0-9\-]+)$)')])
    # TODO: Check max length of name.
    ip = TextField('ip', [validators.IPAddress(ipv4=False, ipv6=True)])
    memo = TextField('memo', [validators.Length(max=1000)])


@app.route('/<string:domain>/aaaa/new', methods=['GET'])
@login(True, '/')
def record_aaaa_new(domain):
    domain = g.session.query(Domain).filter(Domain.domain.like(domain))\
                                    .filter(Domain.owner == get_user())\
                                    .first()
    if not domain:
        return redirect(url_for('domain.index'))

    form = RecordAAAAForm()

    return render_template('domain_aaaa/new.html',
                           domain=domain,
                           form=form)


@app.route('/<string:domain>/aaaa/<int:record_id>', methods=['GET'])
@login(True, '/')
def record_aaaa_edit(domain, record_id):
    domain = g.session.query(Domain).filter(Domain.domain.like(domain))\
                                    .filter(Domain.owner == get_user())\
                                    .first()
    if not domain:
        return redirect(url_for('domain.index'))

    record = g.session.query(RecordAAAA).filter(RecordAAAA.id == record_id)\
                                        .filter(RecordAAAA.domain == domain)\
                                        .first()
    if not record:
        return redirect(url_for('domain.record_aaaa', domain=domain.domain))

    form = RecordAAAAForm(name=record.name, ip=record.ip, memo=record.memo)

    return render_template('domain_aaaa/edit.html',
                           domain=domain,
                           form=form)


@app.route('/<string:domain>/aaaa/new', methods=['POST'])
@login(True, '/')
def record_aaaa_new_process(domain):
    form = RecordAAAAForm(request.form)
    domain = g.session.query(Domain).filter(Domain.domain.like(domain))\
                                    .filter(Domain.owner == get_user())\
                                    .first()
    if not domain:
        return redirect(url_for('domain.index'))

    if not form.validate():
        return render_template('domain_aaaa/new.html',
                               domain=domain,
                               form=form)

    aaaa_record = RecordAAAA(domain=domain,
                             name=form.name.data or None,
                             ip=form.ip.data,
                             memo=form.memo.data)

    with g.session.begin():
        g.session.add(aaaa_record)

    return redirect(url_for('domain.record_aaaa', domain=domain.domain))


@app.route('/<string:domain>/aaaa/<int:record_id>', methods=['POST'])
@login(True, '/')
def record_aaaa_edit_process(domain, record_id):
    form = RecordAAAAForm(request.form)
    domain = g.session.query(Domain).filter(Domain.domain.like(domain))\
                                    .filter(Domain.owner == get_user())\
                                    .first()
    if not domain:
        return redirect(url_for('domain.index'))

    record = g.session.query(RecordAAAA).filter(RecordAAAA.id == record_id)\
                                        .filter(RecordAAAA.domain == domain)\
                                        .first()
    if not record:
        return redirect(url_for('domain.record_aaaa', domain=domain.domain))

    form.name.data = record.name

    if not form.validate():
        return render_template('domain_aaaa/edit.html',
                               domain=domain,
                               form=form)

    record.ip = form.ip.data
    record.memo = form.memo.data

    with g.session.begin():
        g.session.add(record)

    return redirect(url_for('domain.record_aaaa', domain=domain.domain))


@app.route('/<string:domain>/aaaa/<int:record_id>/del',
           methods=['GET', 'POST'])
@login(True, '/')
def record_aaaa_delete(domain, record_id):
    domain = g.session.query(Domain).filter(Domain.domain.like(domain))\
                                    .filter(Domain.owner == get_user())\
                                    .first()
    if not domain:
        return redirect(url_for('domain.index'))

    record = g.session.query(RecordAAAA).filter(RecordAAAA.id == record_id)\
                                        .filter(RecordAAAA.domain == domain)\
                                        .first()
    if not record:
        return redirect(url_for('domain.record_aaaa', domain=domain.domain))

    if request.method == 'POST':
        with g.session.begin():
            g.session.delete(record)
        return redirect(url_for('domain.record_aaaa', domain=domain.domain))

    return render_template('domain_aaaa/del.html', domain=domain,
                           record=record)
