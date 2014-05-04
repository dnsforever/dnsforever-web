from flask import Blueprint, render_template, redirect, url_for
from dnsserver.tools.session import login

app = Blueprint('account', __name__)


@app.route('/signup', methods=['GET', 'POST'])
@login(False, '/')
def signup():
    return render_template('signup.html')


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
