from flask import Blueprint, g, render_template, request, url_for, redirect
from wtforms import Form, StringField, BooleanField, validators
from dnsforever.web.tools import random_string
from dnsforever.web.tools.session import login, get_user, get_domain
from dnsforever.models import Domain, RecordA

app = Blueprint('domain_a', __name__, url_prefix='/domain/<string:domain>/a')


@app.route('/')
@login(True, '/')
def record_list(domain):
    domain = get_domain(domain)

    if not domain:
        return redirect(url_for('domain.index'))

    records = g.session.query(RecordA).filter(RecordA.domain == domain)\
                                      .order_by(RecordA.name).all()

    if not records:
        return redirect(url_for('domain_a.record_new', domain=domain.name))

    return render_template('domain_a/list.html',
                           domain=domain,
                           records=records)


class RecordAForm(Form):
    name = StringField('name',
                       [validators.Regexp('(^$)|'
                                          '(^([a-z0-9\-]+\.)*([a-z0-9\-]+)$)')])
    # TODO: Check max length of name.
    ip = StringField('ip', [validators.IPAddress()])
    memo = StringField('memo', [validators.Length(max=1000)])


@app.route('/new', methods=['GET'])
@login(True, '/')
def record_new(domain):
    domain = get_domain(domain)

    if not domain:
        return redirect(url_for('domain.index'))

    form = RecordAForm(ip=request.remote_addr)

    return render_template('domain_a/new.html',
                           domain=domain,
                           form=form)


@app.route('/<int:record_id>', methods=['GET'])
@login(True, '/')
def record_edit(domain, record_id):
    domain = get_domain(domain)

    if not domain:
        return redirect(url_for('domain.index'))

    record = g.session.query(RecordA).filter(RecordA.id == record_id)\
                                     .filter(RecordA.domain == domain)\
                                     .first()
    if not record:
        return redirect(url_for('domain_a.record_list', domain=domain.name))

    form = RecordAForm(name=record.name, ip=record.ip, memo=record.memo)

    return render_template('domain_a/edit.html',
                           domain=domain,
                           form=form)


@app.route('/new', methods=['POST'])
@login(True, '/')
def record_new_process(domain):
    form = RecordAForm(request.form)
    domain = get_domain(domain)

    if not domain:
        return redirect(url_for('domain.index'))

    if not form.validate():
        return render_template('domain_a/new.html',
                               domain=domain,
                               form=form)

    try:
        a_record = RecordA(domain=domain,
                           name=form.name.data or None,
                           ip=form.ip.data,
                           memo=form.memo.data)
        with g.session.begin():
            a_record.update()
            g.session.add(a_record)
    except ValueError as e:
        form.name.errors.append(e)
        return render_template('domain_a/new.html',
                               domain=domain,
                               form=form)

    return redirect(url_for('domain_a.record_list', domain=domain.name))


@app.route('/<int:record_id>', methods=['POST'])
@login(True, '/')
def record_edit_process(domain, record_id):
    form = RecordAForm(request.form)
    domain = get_domain(domain)

    if not domain:
        return redirect(url_for('domain.index'))

    record = g.session.query(RecordA).filter(RecordA.id == record_id)\
                                     .filter(RecordA.domain == domain)\
                                     .first()
    if not record:
        return redirect(url_for('domain_a.record_list', domain=domain.name))

    form.name.data = record.name

    if not form.validate():
        return render_template('domain_a/edit.html',
                               domain=domain,
                               form=form)

    record.ip = form.ip.data
    record.memo = form.memo.data

    with g.session.begin():
        record.update()
        g.session.add(record)

    return redirect(url_for('domain_a.record_list', domain=domain.name))


@app.route('/<int:record_id>/del', methods=['GET', 'POST'])
@login(True, '/')
def record_delete(domain, record_id):
    domain = get_domain(domain)

    if not domain:
        return redirect(url_for('domain.index'))

    record = g.session.query(RecordA).filter(RecordA.id == record_id)\
                                     .filter(RecordA.domain == domain)\
                                     .first()
    if not record:
        return redirect(url_for('domain_a.record_list', domain=domain.name))

    if request.method == 'POST':
        with g.session.begin():
            record.domain.update()
            g.session.add(record.domain)
            g.session.delete(record)
        return redirect(url_for('domain_a.record_list', domain=domain.name))

    return render_template('domain_a/del.html', domain=domain, record=record)
