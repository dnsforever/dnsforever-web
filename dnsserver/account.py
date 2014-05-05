from flask import Blueprint, g, render_template, redirect, url_for, request
from wtforms import Form, TextField, PasswordField, validators, ValidationError
from dnsserver.tools.session import login
from hashlib import sha256

from dnsserver.models import User

app = Blueprint('account', __name__)


def password_hash(data):
    for i in xrange(9999):
        data = sha256(data + 'SECRET_KEY').digest()
    return sha256(data + 'SECRET_KEY').hexdigest()


class SignupForm(Form):
    name = TextField('name', [validators.Length(min=4, max=25)])
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


@app.route('/signin', methods=['GET', 'POST'])
@login(False, '/')
def signin():
    return render_template('signin.html')


@app.route('/signout', methods=['GET', 'POST'])
@login(False, '/')
def signout():
    return redirect(url_for('index.index'))


@app.route('/resetpasswd', methods=['GET', 'POST'])
@login(False, '/')
def resetpasswd():
    return render_template('resetpasswd.html')
