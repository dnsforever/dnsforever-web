from flask import Blueprint, g, render_template, request, url_for, redirect
from wtforms import Form, TextField, BooleanField, validators
from dnsserver.tools import random_string
from dnsserver.tools.session import login, get_user
from dnsserver.models import Domain, RecordA
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


@app.route('/<string:domain>/a', methods=['GET', 'POST'])
@login(True, '/')
def record_a(domain):
    domain = g.session.query(Domain).filter(Domain.domain.like(domain))\
                                    .filter(Domain.owner == get_user())\
                                    .first()
    if not domain:
        return redirect(url_for('domain.index'))

    records = g.session.query(RecordA).filter(RecordA.domain == domain)\
                                      .order_by(RecordA.name).all()

    if not records:
        return redirect(url_for('domain.record_a_new', domain=domain.domain))

    return render_template('domain_a.html',
                           domain=domain,
                           records=records)


class RecordAForm(Form):
    name = TextField('name',
                     [validators.Regexp('(^$)|'
                                        '(^([a-z0-9\-]+\.)*([a-z0-9\-]+)$)')])
    # TODO: Check max length of name.
    ip = TextField('ip', [validators.IPAddress()])
    memo = TextField('memo', [validators.Length(max=1000)])
    ddns = BooleanField('ddns')


@app.route('/<string:domain>/a/new', methods=['GET'])
@login(True, '/')
def record_a_new(domain):
    domain = g.session.query(Domain).filter(Domain.domain.like(domain))\
                                    .filter(Domain.owner == get_user())\
                                    .first()
    if not domain:
        return redirect(url_for('domain.index'))

    form = RecordAForm(ip=request.remote_addr)

    return render_template('domain_a_new.html',
                           domain=domain,
                           form=form)


@app.route('/<string:domain>/a/<int:record_id>', methods=['GET'])
@login(True, '/')
def record_a_edit(domain, record_id):
    domain = g.session.query(Domain).filter(Domain.domain.like(domain))\
                                    .filter(Domain.owner == get_user())\
                                    .first()
    if not domain:
        return redirect(url_for('domain.index'))

    record = g.session.query(RecordA).filter(RecordA.id == record_id)\
                                     .filter(RecordA.domain == domain)\
                                     .first()
    if not record:
        return redirect(url_for('domain.record_a', domain=domain.domain))

    form = RecordAForm(name=record.name, ip=record.ip, memo=record.memo,
                       ddns=record.ddns)

    return render_template('domain_a_edit.html',
                           domain=domain,
                           form=form)


@app.route('/<string:domain>/a/new', methods=['POST'])
@login(True, '/')
def record_a_new_process(domain):
    form = RecordAForm(request.form)
    domain = g.session.query(Domain).filter(Domain.domain.like(domain))\
                                    .filter(Domain.owner == get_user())\
                                    .first()
    if not domain:
        return redirect(url_for('domain.index'))

    if not form.validate():
        return render_template('domain_a_new.html',
                               domain=domain,
                               form=form)

    a_record = RecordA(domain=domain,
                       name=form.name.data or None,
                       ip=form.ip.data,
                       memo=form.memo.data,
                       ddns=form.ddns.data,
                       key=form.ddns.data and random_string(10) or None)

    with g.session.begin():
        g.session.add(a_record)

    return redirect(url_for('domain.record_a', domain=domain.domain))


@app.route('/<string:domain>/a/<int:record_id>', methods=['POST'])
@login(True, '/')
def record_a_edit_process(domain, record_id):
    form = RecordAForm(request.form)
    domain = g.session.query(Domain).filter(Domain.domain.like(domain))\
                                    .filter(Domain.owner == get_user())\
                                    .first()
    if not domain:
        return redirect(url_for('domain.index'))

    record = g.session.query(RecordA).filter(RecordA.id == record_id)\
                                     .filter(RecordA.domain == domain)\
                                     .first()
    if not record:
        return redirect(url_for('domain.record_a', domain=domain.domain))

    form.name.data = record.name

    if not form.validate():
        return render_template('domain_a_edit.html',
                               domain=domain,
                               form=form)

    record.ip = form.ip.data
    record.memo = form.memo.data
    record.ddns = form.ddns.data
    record.key = record.key or form.ddns.data and random_string(10) or None

    with g.session.begin():
        g.session.add(record)

    return redirect(url_for('domain.record_a', domain=domain.domain))


@app.route('/<string:domain>/a/<int:record_id>/del', methods=['GET', 'POST'])
@login(True, '/')
def record_a_delete(domain, record_id):
    domain = g.session.query(Domain).filter(Domain.domain.like(domain))\
                                    .filter(Domain.owner == get_user())\
                                    .first()
    if not domain:
        return redirect(url_for('domain.index'))

    record = g.session.query(RecordA).filter(RecordA.id == record_id)\
                                     .filter(RecordA.domain == domain)\
                                     .first()
    if not record:
        return redirect(url_for('domain.record_a', domain=domain.domain))

    if request.method == 'POST':
        with g.session.begin():
            g.session.delete(record)
        return redirect(url_for('domain.record_a', domain=domain.domain))

    return render_template('domain_a_del.html', domain=domain, record=record)
