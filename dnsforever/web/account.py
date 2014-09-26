from flask import Blueprint, g, render_template, redirect, url_for, request
from wtforms import Form, TextField, PasswordField, validators, ValidationError

from dnsforever.models import User, EmailValidation
from dnsforever.web.tools.session import login, set_user, get_user
from dnsforever.web.tools import password_hash
from dnsforever.web import email

app = Blueprint('account', __name__, url_prefix='/account')


class SignupForm(Form):
    name = TextField('name', [validators.Length(min=1, max=25)])
    email = TextField('email', [validators.Length(min=6, max=127),
                                validators.Email()])
    password = PasswordField('password', [validators.Required()])

    def validate_email(form, field):
        if g.session.query(User).filter(User.email == field.data).count() != 0:
            raise ValidationError('Email already exists, '
                                  'please reset your password')


@app.route('/signup', methods=['GET'])
@login(False, '/')
def signup():
    return render_template('signup.html', form=SignupForm())


@app.route('/signup', methods=['POST'])
@login(False, '/')
def signup_process():
    form = SignupForm(request.form)

    if not form.validate():
        return render_template('signup.html', form=form)

    user = User(name=form.name.data,
                email=form.email.data,
                password=password_hash(form.password.data))
    with g.session.begin():
        g.session.add(user)

    email.email_validation(user)

    return redirect(url_for('account.need_email_validation'))


class SigninForm(Form):
    email = TextField('email', [validators.Length(min=6, max=127),
                                validators.Email()])
    password = PasswordField('password', [validators.Required()])

    def validate_email(form, field):
        user = g.session.query(User).filter(User.email == field.data).first()
        if user is None or user.password != password_hash(form.password.data):
            raise ValidationError('Email or Password is wrong.')


@app.route('/signin', methods=['GET'])
@login(False, '/')
def signin():
    return render_template('signin.html', form=SigninForm())


@app.route('/signin', methods=['POST'])
@login(False, '/')
def signin_process():
    form = SigninForm(request.form)

    if not form.validate():
        return render_template('signin.html', form=form)

    user = g.session.query(User).filter(User.email == form.email.data).first()
    if user.type == 2:
        email.email_validation(user)
        return redirect(url_for('account.need_email_validation'))

    set_user(user)

    return redirect(url_for('index.index'))


@app.route('/signout', methods=['GET', 'POST'])
@login(True, '/')
def signout():
    set_user(None)
    return redirect(url_for('index.index'))


class ResetPasswordForm(Form):
    old_password = PasswordField('old_password', [validators.Required()])
    new_password = PasswordField('new_password', [validators.Required()])


@app.route('/resetpasswd', methods=['GET', 'POST'])
@login(True, '/')
def resetpasswd():
    if request.method == 'GET':
        return render_template('resetpasswd.html', form=ResetPasswordForm())

    form = ResetPasswordForm(request.form)

    if not form.validate():
        return render_template('resetpasswd.html', form=form)

    user = get_user()

    if password_hash(form.old_password.data) != user.password:
        form.old_password.errors.append('Please enter the correct password.')
        return render_template('resetpasswd.html', form=form)

    user.password = password_hash(form.new_password.data)

    with g.session.begin():
        g.session.add(user)

    return redirect(url_for('index.index'))


@app.route('/validation', methods=['GET'])
def need_email_validation():
    return render_template('need_email_validation.html')


@app.route('/validation', methods=['POST'])
def need_email_validation_resend():
    return render_template('need_email_validation.html')


@app.route('/validation/<string:token>', methods=['GET'])
def validation(token):
    ev = g.session.query(EmailValidation)\
                  .filter(EmailValidation.token.like(token))\
                  .first()

    if not ev:
        return redirect(url_for('index.index'))

    user = ev.user
    user.type = 1

    evs = g.session.query(EmailValidation)\
                   .filter(EmailValidation.user == user)\
                   .all()

    with g.session.begin():
        g.session.add(user)
        for ev in evs:
            g.session.delete(ev)

    set_user(user)
    return redirect(url_for('index.index'))
