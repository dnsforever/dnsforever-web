from flask import Blueprint, g, render_template, request, url_for, redirect
from wtforms import Form, TextField, BooleanField, validators
from dnsserver.tools import random_string
from dnsserver.tools.session import login, get_user
from dnsserver.models import Domain, RecordA

app = Blueprint('domain_a', __name__, url_prefix='/domain/<string:domain>/a')


@app.route('/')
@login(True, '/')
def record_list(domain):
    domain = g.session.query(Domain).filter(Domain.domain.like(domain))\
                                    .filter(Domain.owner == get_user())\
                                    .first()
    if not domain:
        return redirect(url_for('domain.index'))

    records = g.session.query(RecordA).filter(RecordA.domain == domain)\
                                      .order_by(RecordA.name).all()

    if not records:
        return redirect(url_for('domain.detail', domain=domain.domain))

    return render_template('domain_a/list.html',
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


@app.route('/new', methods=['GET'])
@login(True, '/')
def record_new(domain):
    domain = g.session.query(Domain).filter(Domain.domain.like(domain))\
                                    .filter(Domain.owner == get_user())\
                                    .first()
    if not domain:
        return redirect(url_for('domain.index'))

    form = RecordAForm(ip=request.remote_addr)

    return render_template('domain_a/new.html',
                           domain=domain,
                           form=form)


@app.route('/<int:record_id>', methods=['GET'])
@login(True, '/')
def record_edit(domain, record_id):
    domain = g.session.query(Domain).filter(Domain.domain.like(domain))\
                                    .filter(Domain.owner == get_user())\
                                    .first()
    if not domain:
        return redirect(url_for('domain.index'))

    record = g.session.query(RecordA).filter(RecordA.id == record_id)\
                                     .filter(RecordA.domain == domain)\
                                     .first()
    if not record:
        return redirect(url_for('domain_a.record_list', domain=domain.domain))

    form = RecordAForm(name=record.name, ip=record.ip, memo=record.memo,
                       ddns=record.ddns)

    return render_template('domain_a/edit.html',
                           domain=domain,
                           form=form)


@app.route('/new', methods=['POST'])
@login(True, '/')
def record_new_process(domain):
    form = RecordAForm(request.form)
    domain = g.session.query(Domain).filter(Domain.domain.like(domain))\
                                    .filter(Domain.owner == get_user())\
                                    .first()
    if not domain:
        return redirect(url_for('domain.index'))

    if not form.validate():
        return render_template('domain_a/new.html',
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

    return redirect(url_for('domain_a.record_list', domain=domain.domain))


@app.route('/<int:record_id>', methods=['POST'])
@login(True, '/')
def record_edit_process(domain, record_id):
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
        return redirect(url_for('domain_a.record_list', domain=domain.domain))

    form.name.data = record.name

    if not form.validate():
        return render_template('domain_a/edit.html',
                               domain=domain,
                               form=form)

    record.ip = form.ip.data
    record.memo = form.memo.data
    record.ddns = form.ddns.data
    record.key = record.key or form.ddns.data and random_string(10) or None

    with g.session.begin():
        g.session.add(record)

    return redirect(url_for('domain_a.record_list', domain=domain.domain))


@app.route('/<int:record_id>/del', methods=['GET', 'POST'])
@login(True, '/')
def record_delete(domain, record_id):
    domain = g.session.query(Domain).filter(Domain.domain.like(domain))\
                                    .filter(Domain.owner == get_user())\
                                    .first()
    if not domain:
        return redirect(url_for('domain.index'))

    record = g.session.query(RecordA).filter(RecordA.id == record_id)\
                                     .filter(RecordA.domain == domain)\
                                     .first()
    if not record:
        return redirect(url_for('domain_a.record_list', domain=domain.domain))

    if request.method == 'POST':
        with g.session.begin():
            g.session.delete(record)
        return redirect(url_for('domain_a.record_list', domain=domain.domain))

    return render_template('domain_a/del.html', domain=domain, record=record)
