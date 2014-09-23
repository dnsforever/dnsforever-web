from flask import Blueprint, g, render_template, request, url_for, redirect
from wtforms import Form, StringField
from wtforms.validators import Regexp, Length
from dnsforever.web.tools.session import login, get_user, get_domain
from dnsforever.models import Domain, RecordTXT

app = Blueprint('domain_txt', __name__,
                url_prefix='/domain/<string:domain>/txt',
                template_folder='templates/domain_txt')


@app.route('/')
@login(True, '/')
def record_list(domain):
    domain = get_domain(domain)

    if not domain:
        return redirect(url_for('domain.index'))

    records = g.session.query(RecordTXT).filter(RecordTXT.domain == domain)\
                                        .order_by(RecordTXT.name).all()

    if not records:
        return redirect(url_for('domain_txt.record_new', domain=domain.name))

    return render_template('domain_txt/list.html',
                           domain=domain,
                           records=records)


class RecordTXTForm(Form):
    name = StringField('name',
                     [Regexp('(^$)|(^([a-z0-9\-]+\.)*([a-z0-9\-]+)$)')])
    txt = StringField('txt', [Length(max=255),
                            Regexp('^[a-z0-9\-_\.]+=[a-zA-Z0-9\-_=\.]+$')])


@app.route('/new', methods=['GET'])
@login(True, '/')
def record_new(domain):
    domain = get_domain(domain)

    if not domain:
        return redirect(url_for('domain.index'))

    form = RecordTXTForm()

    return render_template('domain_txt/new.html', domain=domain, form=form)


@app.route('/<int:record_id>', methods=['GET'])
@login(True, '/')
def record_edit(domain, record_id):
    domain = get_domain(domain)

    if not domain:
        return redirect(url_for('domain.index'))

    record = g.session.query(RecordTXT).filter(RecordTXT.id == record_id)\
                                       .filter(RecordTXT.domain == domain)\
                                       .first()
    if not record:
        return redirect(url_for('domain_txt.record_list',
                                domain=domain.name))

    form = RecordTXTForm(name=record.name, txt=record.txt)

    return render_template('domain_txt/edit.html',
                           domain=domain,
                           form=form)


@app.route('/new', methods=['POST'])
@login(True, '/')
def record_new_process(domain):
    form = RecordTXTForm(request.form)
    domain = get_domain(domain)

    if not domain:
        return redirect(url_for('domain.index'))

    if not form.validate():
        return render_template('domain_txt/new.html',
                               domain=domain,
                               form=form)

    try:
        txt_record = RecordTXT(domain=domain,
                               txt=form.txt.data)
        with g.session.begin():
            g.session.add(txt_record)
    except ValueError as e:
        form.name.errors.append(e)
        return render_template('domain_txt/new.html',
                               domain=domain,
                               form=form)

    return redirect(url_for('domain_txt.record_list', domain=domain.name))


@app.route('/<int:record_id>', methods=['POST'])
@login(True, '/')
def record_edit_process(domain, record_id):
    form = RecordTXTForm(request.form)
    domain = get_domain(domain)

    if not domain:
        return redirect(url_for('domain.index'))

    record = g.session.query(RecordTXT).filter(RecordTXT.id == record_id)\
                                       .filter(RecordTXT.domain == domain)\
                                       .first()
    if not record:
        return redirect(url_for('domain_txt.record_list',
                                domain=domain.name))

    form.name.data = record.name

    if not form.validate():
        return render_template('domain_txt/edit.html',
                               domain=domain,
                               form=form)

    record.txt = form.txt.data

    with g.session.begin():
        g.session.add(record)

    return redirect(url_for('domain_txt.record_list', domain=domain.name))


@app.route('/<int:record_id>/del', methods=['GET', 'POST'])
@login(True, '/')
def record_delete(domain, record_id):
    domain = get_domain(domain)

    if not domain:
        return redirect(url_for('domain.index'))

    record = g.session.query(RecordTXT).filter(RecordTXT.id == record_id)\
                                       .filter(RecordTXT.domain == domain)\
                                       .first()
    if not record:
        return redirect(url_for('domain_txt.record_list',
                                domain=domain.name))

    if request.method == 'POST':
        with g.session.begin():
            g.session.delete(record)
        return redirect(url_for('domain_txt.record_list',
                                domain=domain.name))

    return render_template('domain_txt/del.html', domain=domain,
                           record=record)
