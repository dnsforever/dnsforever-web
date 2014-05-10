from flask import Blueprint, g, render_template, request, url_for, redirect
from wtforms import Form, TextField, validators
from dnsserver.tools.session import login, get_user
from dnsserver.models import Domain, RecordAAAA

app = Blueprint('domain_aaaa', __name__,
                url_prefix='/domain/<string:domain>/aaaa',
                template_folder='templates/domain_aaaa')


@app.route('/')
@login(True, '/')
def record_list(domain):
    domain = g.session.query(Domain).filter(Domain.domain.like(domain))\
                                    .filter(Domain.owner == get_user())\
                                    .first()
    if not domain:
        return redirect(url_for('domain.index'))

    records = g.session.query(RecordAAAA).filter(RecordAAAA.domain == domain)\
                                         .order_by(RecordAAAA.name).all()

    if not records:
        return redirect(url_for('domain.detail',
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


@app.route('/new', methods=['GET'])
@login(True, '/')
def record_new(domain):
    domain = g.session.query(Domain).filter(Domain.domain.like(domain))\
                                    .filter(Domain.owner == get_user())\
                                    .first()
    if not domain:
        return redirect(url_for('domain.index'))

    form = RecordAAAAForm()

    return render_template('domain_aaaa/new.html', domain=domain, form=form)


@app.route('/<int:record_id>', methods=['GET'])
@login(True, '/')
def record_edit(domain, record_id):
    domain = g.session.query(Domain).filter(Domain.domain.like(domain))\
                                    .filter(Domain.owner == get_user())\
                                    .first()
    if not domain:
        return redirect(url_for('domain.index'))

    record = g.session.query(RecordAAAA).filter(RecordAAAA.id == record_id)\
                                        .filter(RecordAAAA.domain == domain)\
                                        .first()
    if not record:
        return redirect(url_for('domain_aaaa.record_list',
                                domain=domain.domain))

    form = RecordAAAAForm(name=record.name, ip=record.ip, memo=record.memo)

    return render_template('domain_aaaa/edit.html',
                           domain=domain,
                           form=form)


@app.route('/new', methods=['POST'])
@login(True, '/')
def record_new_process(domain):
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

    return redirect(url_for('domain_aaaa.record_list', domain=domain.domain))


@app.route('/<int:record_id>', methods=['POST'])
@login(True, '/')
def record_edit_process(domain, record_id):
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
        return redirect(url_for('domain_aaaa.record_list',
                                domain=domain.domain))

    form.name.data = record.name

    if not form.validate():
        return render_template('domain_aaaa/edit.html',
                               domain=domain,
                               form=form)

    record.ip = form.ip.data
    record.memo = form.memo.data

    with g.session.begin():
        g.session.add(record)

    return redirect(url_for('domain_aaaa.record_list', domain=domain.domain))


@app.route('/<int:record_id>/del',
           methods=['GET', 'POST'])
@login(True, '/')
def record_delete(domain, record_id):
    domain = g.session.query(Domain).filter(Domain.domain.like(domain))\
                                    .filter(Domain.owner == get_user())\
                                    .first()
    if not domain:
        return redirect(url_for('domain.index'))

    record = g.session.query(RecordAAAA).filter(RecordAAAA.id == record_id)\
                                        .filter(RecordAAAA.domain == domain)\
                                        .first()
    if not record:
        return redirect(url_for('domain_aaaa.record_list',
                                domain=domain.domain))

    if request.method == 'POST':
        with g.session.begin():
            g.session.delete(record)
        return redirect(url_for('domain_aaaa.record_list',
                                domain=domain.domain))

    return render_template('domain_aaaa/del.html', domain=domain,
                           record=record)
