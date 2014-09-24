from flask import Blueprint, g, render_template, request, url_for, redirect
from wtforms import Form, TextField, IntegerField
from wtforms.validators import Regexp, NumberRange
from dnsforever.web.tools.session import login, get_user, get_domain
from dnsforever.models import Domain, RecordMX

app = Blueprint('domain_mx', __name__,
                url_prefix='/domain/<string:domain>/mx',
                template_folder='templates/domain_mx')


@app.route('/')
@login(True, '/')
def record_list(domain):
    domain = get_domain(domain)

    if not domain:
        return redirect(url_for('domain.index'))

    records = g.session.query(RecordMX).filter(RecordMX.domain == domain)\
                                       .all()

    records = sorted(records, key=lambda record: record.preference)

    if not records:
        return redirect(url_for('domain_mx.record_new', domain=domain.name))

    return render_template('domain_mx/list.html',
                           domain=domain,
                           records=records)


class RecordMXForm(Form):
    name = TextField('name',
                     [Regexp('(^$)|(^([a-z0-9\-]+\.)*([a-z0-9\-]+)$)')])
    # TODO: Check max length of name.
    target = TextField('target', [Regexp('(^([a-z0-9\-]+\.)*([a-z0-9\-]+)$)')])
    preference = IntegerField('preference', [NumberRange(0, 99)])


@app.route('/new', methods=['GET'])
@login(True, '/')
def record_new(domain):
    domain = get_domain(domain)

    if not domain:
        return redirect(url_for('domain.index'))

    form = RecordMXForm()

    return render_template('domain_mx/new.html', domain=domain, form=form)


@app.route('/<int:record_id>', methods=['GET'])
@login(True, '/')
def record_edit(domain, record_id):
    domain = get_domain(domain)

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
                        preference=record.preference)

    return render_template('domain_mx/edit.html',
                           domain=domain,
                           form=form)


@app.route('/new', methods=['POST'])
@login(True, '/')
def record_new_process(domain):
    form = RecordMXForm(request.form)
    domain = get_domain(domain)

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
                             preference=form.preference.data)
        with g.session.begin():
            mx_record.update()
            g.session.add(mx_record)
    except ValueError as e:
        form.name.errors.append(e)
        return render_template('domain_mx/new.html',
                               domain=domain,
                               form=form)

    return redirect(url_for('domain_mx.record_list', domain=domain.name))


@app.route('/<int:record_id>', methods=['POST'])
@login(True, '/')
def record_edit_process(domain, record_id):
    form = RecordMXForm(request.form)
    domain = get_domain(domain)

    if not domain:
        return redirect(url_for('domain.index'))

    record = g.session.query(RecordMX).filter(RecordMX.id == record_id)\
                                      .filter(RecordMX.domain == domain)\
                                      .first()
    if not record:
        return redirect(url_for('domain_mx.record_list',
                                domain=domain.name))

    form.name.data = record.name

    if not form.validate():
        return render_template('domain_mx/edit.html',
                               domain=domain,
                               form=form)

    record.target = form.target.data
    record.preference = form.preference.data

    with g.session.begin():
        record.update()
        g.session.add(record)

    return redirect(url_for('domain_mx.record_list', domain=domain.name))


@app.route('/<int:record_id>/del',
           methods=['GET', 'POST'])
@login(True, '/')
def record_delete(domain, record_id):
    domain = get_domain(domain)

    if not domain:
        return redirect(url_for('domain.index'))

    record = g.session.query(RecordMX).filter(RecordMX.id == record_id)\
                                      .filter(RecordMX.domain == domain)\
                                      .first()
    if not record:
        return redirect(url_for('domain_mx.record_list',
                                domain=domain.name))

    if request.method == 'POST':
        with g.session.begin():
            record.domain.update()
            g.session.add(record.domain)
            g.session.delete(record)
        return redirect(url_for('domain_mx.record_list',
                                domain=domain.name))

    return render_template('domain_mx/del.html', domain=domain,
                           record=record)
