from flask import Blueprint, g, render_template, request, url_for, redirect
from wtforms import Form, StringField, validators
from dnsforever.web.tools.session import login, get_domain
from dnsforever.models import RecordDDNS_A

app = Blueprint('domain_ddns',
                __name__,
                url_prefix='/domain/<string:domain>/ddns')


@app.route('/')
@login(True, '/')
def record_list(domain):
    domain = get_domain(domain)

    if not domain:
        return redirect(url_for('domain.index'))

    records = g.session.query(RecordDDNS_A)\
                       .filter(RecordDDNS_A.domain == domain)\
                       .order_by(RecordDDNS_A.name).all()

    if not records:
        return redirect(url_for('domain_ddns.record_new', domain=domain.name))

    return render_template('domain_ddns/list.html',
                           domain=domain,
                           records=records)


class RecordDDNSForm(Form):
    name = StringField('name',
                       [validators.Regexp('(^$)|'
                                          '(^([a-z0-9\-]+\.)*'
                                          '([a-z0-9\-]+)$)')])
    ip = StringField('ip', [validators.IPAddress()])
    memo = StringField('memo', [validators.Length(max=1000)])


@app.route('/new', methods=['GET'])
@login(True, '/')
def record_new(domain):
    domain = get_domain(domain)

    if not domain:
        return redirect(url_for('domain.index'))

    form = RecordDDNSForm(ip=request.remote_addr)

    return render_template('domain_ddns/new.html',
                           domain=domain,
                           form=form)


@app.route('/<int:record_id>', methods=['GET'])
@login(True, '/')
def record_edit(domain, record_id):
    domain = get_domain(domain)

    if not domain:
        return redirect(url_for('domain.index'))

    record = g.session.query(RecordDDNS_A)\
                      .filter(RecordDDNS_A.id == record_id)\
                      .filter(RecordDDNS_A.domain == domain)\
                      .first()
    if not record:
        return redirect(url_for('domain_ddns.record_list', domain=domain.name))

    form = RecordDDNSForm(name=record.name, ip=record.ip, memo=record.memo)

    return render_template('domain_ddns/edit.html',
                           domain=domain,
                           form=form)


@app.route('/new', methods=['POST'])
@login(True, '/')
def record_new_process(domain):
    form = RecordDDNSForm(request.form)
    domain = get_domain(domain)

    if not domain:
        return redirect(url_for('domain.index'))

    if not form.validate():
        return render_template('domain_ddns/new.html',
                               domain=domain,
                               form=form)

    try:
        ddns_record = RecordDDNS_A(domain=domain,
                                   name=form.name.data or None,
                                   ip=form.ip.data,
                                   memo=form.memo.data)
        with g.session.begin():
            ddns_record.update()
            g.session.add(ddns_record)
    except ValueError as e:
        form.name.errors.append(e)
        return render_template('domain_ddns/new.html',
                               domain=domain,
                               form=form)

    return redirect(url_for('domain_ddns.record_list', domain=domain.name))


@app.route('/<int:record_id>', methods=['POST'])
@login(True, '/')
def record_edit_process(domain, record_id):
    form = RecordDDNSForm(request.form)
    domain = get_domain(domain)

    if not domain:
        return redirect(url_for('domain.index'))

    record = g.session.query(RecordDDNS_A)\
                      .filter(RecordDDNS_A.id == record_id)\
                      .filter(RecordDDNS_A.domain == domain)\
                      .first()
    if not record:
        return redirect(url_for('domain_ddns.record_list', domain=domain.name))

    form.name.data = record.name

    if not form.validate():
        return render_template('domain_ddns/edit.html',
                               domain=domain,
                               form=form)

    record.ip = form.ip.data
    record.memo = form.memo.data

    with g.session.begin():
        record.domain.update()
        g.session.add(record)

    return redirect(url_for('domain_ddns.record_list', domain=domain.name))


@app.route('/<int:record_id>/del', methods=['GET', 'POST'])
@login(True, '/')
def record_delete(domain, record_id):
    domain = get_domain(domain)

    if not domain:
        return redirect(url_for('domain.index'))

    record = g.session.query(RecordDDNS_A)\
                      .filter(RecordDDNS_A.id == record_id)\
                      .filter(RecordDDNS_A.domain == domain)\
                      .first()
    if not record:
        return redirect(url_for('domain_ddns.record_list', domain=domain.name))

    if request.method == 'POST':
        with g.session.begin():
            record.domain.update()
            g.session.add(record.domain)
            g.session.delete(record)
        return redirect(url_for('domain_ddns.record_list', domain=domain.name))

    return render_template('domain_ddns/del.html',
                           domain=domain, record=record)
