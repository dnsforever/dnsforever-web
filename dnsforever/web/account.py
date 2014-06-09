from flask import Blueprint, g, render_template, redirect, url_for, request
from wtforms import Form, TextField, PasswordField, validators, ValidationError
from hashlib import sha256

from dnsforever.config import hash_salt
from dnsforever.models import User
from dnsforever.web.tools.session import login, set_user, get_user

app = Blueprint('account', __name__, url_prefix='/account')


def password_hash(data):
    for i in xrange(9999):
        data = sha256(data + hash_salt).digest()
    return sha256(data + hash_salt).hexdigest()


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
    return redirect(url_for('account.signin'))


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
