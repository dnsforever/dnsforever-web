from flask import Blueprint, g, render_template, request, url_for, redirect
from wtforms import Form, TextField
from wtforms.validators import Length, Regexp
from dnsforever.tools.session import login, get_user
from dnsforever.models import Domain, RecordCNAME

app = Blueprint('domain_cname', __name__,
                url_prefix='/domain/<string:domain>/cname',
                template_folder='templates/domain_cname')


@app.route('/', methods=['GET', 'POST'])
@login(True, '/')
def record_list(domain):
    domain = g.session.query(Domain).filter(Domain.domain.like(domain))\
                                    .filter(Domain.owner == get_user())\
                                    .first()
    if not domain:
        return redirect(url_for('domain.index'))

    records = g.session.query(RecordCNAME)\
                       .filter(RecordCNAME.domain == domain)\
                       .order_by(RecordCNAME.name).all()

    if not records:
        return redirect(url_for('domain.detail',
                                domain=domain.domain))

    return render_template('domain_cname/list.html',
                           domain=domain,
                           records=records)


class RecordCNAMEForm(Form):
    name = TextField('name', [Regexp('(^([a-z0-9\-]+\.)*([a-z0-9\-]+)$)')])
    # TODO: Check max length of name.
    target = TextField('target', [Regexp('(^([a-z0-9\-]+\.)*([a-z0-9\-]+)$)')])
    memo = TextField('memo', [Length(max=1000)])


@app.route('/new', methods=['GET'])
@login(True, '/')
def record_new(domain):
    domain = g.session.query(Domain).filter(Domain.domain.like(domain))\
                                    .filter(Domain.owner == get_user())\
                                    .first()
    if not domain:
        return redirect(url_for('domain.index'))

    form = RecordCNAMEForm()

    return render_template('domain_cname/new.html', domain=domain, form=form)


@app.route('/<int:record_id>', methods=['GET'])
@login(True, '/')
def record_edit(domain, record_id):
    domain = g.session.query(Domain).filter(Domain.domain.like(domain))\
                                    .filter(Domain.owner == get_user())\
                                    .first()
    if not domain:
        return redirect(url_for('domain.index'))

    record = g.session.query(RecordCNAME).filter(RecordCNAME.id == record_id)\
                                         .filter(RecordCNAME.domain == domain)\
                                         .first()
    if not record:
        return redirect(url_for('domain_cname.record_list',
                                domain=domain.domain))

    form = RecordCNAMEForm(name=record.name,
                           target=record.target,
                           memo=record.memo)

    return render_template('domain_cname/edit.html',
                           domain=domain,
                           form=form)


@app.route('/new', methods=['POST'])
@login(True, '/')
def record_new_process(domain):
    form = RecordCNAMEForm(request.form)
    domain = g.session.query(Domain).filter(Domain.domain.like(domain))\
                                    .filter(Domain.owner == get_user())\
                                    .first()
    if not domain:
        return redirect(url_for('domain.index'))

    if not form.validate():
        return render_template('domain_cname/new.html',
                               domain=domain,
                               form=form)

    record = g.session.query(RecordCNAME)\
              .filter(RecordCNAME.domain == domain)\
              .filter(RecordCNAME.name.like(form.name.data)).first()

    if record:
        form.name.errors.append('Already exists.')
        return render_template('domain_cname/new.html',
                               domain=domain,
                               form=form)

    try:
        cname_record = RecordCNAME(domain=domain,
                                   name=form.name.data or None,
                                   target=form.target.data,
                                   memo=form.memo.data)
    except ValueError as e:
        form.name.errors.append(e)
        return render_template('domain_cname/new.html',
                               domain=domain,
                               form=form)

    with g.session.begin():
        g.session.add(cname_record)

    return redirect(url_for('domain_cname.record_list', domain=domain.domain))


@app.route('/<int:record_id>', methods=['POST'])
@login(True, '/')
def record_edit_process(domain, record_id):
    form = RecordCNAMEForm(request.form)
    domain = g.session.query(Domain).filter(Domain.domain.like(domain))\
                                    .filter(Domain.owner == get_user())\
                                    .first()
    if not domain:
        return redirect(url_for('domain.index'))

    record = g.session.query(RecordCNAME).filter(RecordCNAME.id == record_id)\
                                         .filter(RecordCNAME.domain == domain)\
                                         .first()
    if not record:
        return redirect(url_for('domain_cname.record_list',
                                domain=domain.domain))

    form.name.data = record.name

    if not form.validate():
        return render_template('domain_cname/edit.html',
                               domain=domain,
                               form=form)

    record.target = form.target.data
    record.memo = form.memo.data

    with g.session.begin():
        g.session.add(record)

    return redirect(url_for('domain_cname.record_list', domain=domain.domain))


@app.route('/<int:record_id>/del',
           methods=['GET', 'POST'])
@login(True, '/')
def record_delete(domain, record_id):
    domain = g.session.query(Domain).filter(Domain.domain.like(domain))\
                                    .filter(Domain.owner == get_user())\
                                    .first()
    if not domain:
        return redirect(url_for('domain.index'))

    record = g.session.query(RecordCNAME).filter(RecordCNAME.id == record_id)\
                                         .filter(RecordCNAME.domain == domain)\
                                         .first()
    if not record:
        return redirect(url_for('domain_cname.record_list',
                                domain=domain.domain))

    if request.method == 'POST':
        with g.session.begin():
            g.session.delete(record)
        return redirect(url_for('domain_cname.record_list',
                                domain=domain.domain))

    return render_template('domain_cname/del.html', domain=domain,
                           record=record)
