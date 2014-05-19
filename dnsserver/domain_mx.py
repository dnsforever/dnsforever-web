from flask import Blueprint, g, render_template, request, url_for, redirect
from wtforms import Form, TextField, IntegerField
from wtforms.validators import Regexp, NumberRange
from dnsserver.tools.session import login, get_user
from dnsserver.models import Domain, RecordMX

app = Blueprint('domain_mx', __name__,
                url_prefix='/domain/<string:domain>/mx',
                template_folder='templates/domain_mx')


@app.route('/')
@login(True, '/')
def record_list(domain):
    domain = g.session.query(Domain).filter(Domain.domain.like(domain))\
                                    .filter(Domain.owner == get_user())\
                                    .first()
    if not domain:
        return redirect(url_for('domain.index'))

    records = g.session.query(RecordMX).filter(RecordMX.domain == domain)\
                                       .order_by(RecordMX.name)\
                                       .order_by(RecordMX.rank.asc()).all()

    if not records:
        return redirect(url_for('domain.detail',
                                domain=domain.domain))

    return render_template('domain_mx/list.html',
                           domain=domain,
                           records=records)


class RecordMXForm(Form):
    name = TextField('name',
                     [Regexp('(^$)|(^([a-z0-9\-]+\.)*([a-z0-9\-]+)$)')])
    # TODO: Check max length of name.
    target = TextField('target', [Regexp('(^([a-z0-9\-]+\.)*([a-z0-9\-]+)$)')])
    rank = IntegerField('rank', [NumberRange(0, 99)])


@app.route('/new', methods=['GET'])
@login(True, '/')
def record_new(domain):
    domain = g.session.query(Domain).filter(Domain.domain.like(domain))\
                                    .filter(Domain.owner == get_user())\
                                    .first()
    if not domain:
        return redirect(url_for('domain.index'))

    form = RecordMXForm()

    return render_template('domain_mx/new.html', domain=domain, form=form)


@app.route('/<int:record_id>', methods=['GET'])
@login(True, '/')
def record_edit(domain, record_id):
    domain = g.session.query(Domain).filter(Domain.domain.like(domain))\
                                    .filter(Domain.owner == get_user())\
                                    .first()
    if not domain:
        return redirect(url_for('domain.index'))

    record = g.session.query(RecordMX).filter(RecordMX.id == record_id)\
                                      .filter(RecordMX.domain == domain)\
                                      .first()
    if not record:
        return redirect(url_for('domain_mx.record_list',
                                domain=domain.domain))

    form = RecordMXForm(name=record.name,
                        target=record.target,
                        rank=record.rank)

    return render_template('domain_mx/edit.html',
                           domain=domain,
                           form=form)


@app.route('/new', methods=['POST'])
@login(True, '/')
def record_new_process(domain):
    form = RecordMXForm(request.form)
    domain = g.session.query(Domain).filter(Domain.domain.like(domain))\
                                    .filter(Domain.owner == get_user())\
                                    .first()
    if not domain:
        return redirect(url_for('domain.index'))

    if not form.validate():
        return render_template('domain_mx/new.html',
                               domain=domain,
                               form=form)

    try:
        mx_record = RecordMX(domain=domain,
                             name=form.name.data or None,
                             target=form.target.data,
                             rank=form.rank.data)
    except ValueError as e:
        form.name.errors.append(e)
        return render_template('domain_mx/new.html',
                               domain=domain,
                               form=form)

    with g.session.begin():
        g.session.add(mx_record)

    return redirect(url_for('domain_mx.record_list', domain=domain.domain))


@app.route('/<int:record_id>', methods=['POST'])
@login(True, '/')
def record_edit_process(domain, record_id):
    form = RecordMXForm(request.form)
    domain = g.session.query(Domain).filter(Domain.domain.like(domain))\
                                    .filter(Domain.owner == get_user())\
                                    .first()
    if not domain:
        return redirect(url_for('domain.index'))

    record = g.session.query(RecordMX).filter(RecordMX.id == record_id)\
                                      .filter(RecordMX.domain == domain)\
                                      .first()
    if not record:
        return redirect(url_for('domain_mx.record_list',
                                domain=domain.domain))

    form.name.data = record.name

    if not form.validate():
        return render_template('domain_mx/edit.html',
                               domain=domain,
                               form=form)

    record.target = form.target.data
    record.rank = form.rank.data

    with g.session.begin():
        g.session.add(record)

    return redirect(url_for('domain_mx.record_list', domain=domain.domain))


@app.route('/<int:record_id>/del',
           methods=['GET', 'POST'])
@login(True, '/')
def record_delete(domain, record_id):
    domain = g.session.query(Domain).filter(Domain.domain.like(domain))\
                                    .filter(Domain.owner == get_user())\
                                    .first()
    if not domain:
        return redirect(url_for('domain.index'))

    record = g.session.query(RecordMX).filter(RecordMX.id == record_id)\
                                      .filter(RecordMX.domain == domain)\
                                      .first()
    if not record:
        return redirect(url_for('domain_mx.record_list',
                                domain=domain.domain))

    if request.method == 'POST':
        with g.session.begin():
            g.session.delete(record)
        return redirect(url_for('domain_mx.record_list',
                                domain=domain.domain))

    return render_template('domain_mx/del.html', domain=domain,
                           record=record)
