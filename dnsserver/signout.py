from flask import Blueprint, redirect, url_for
from dnsserver.tools.session import login

app = Blueprint('signout', __name__, url_prefix='/signout')


@app.route('/', methods=['GET', 'POST'])
@login(False, '/')
def signout():
    return redirect(url_for('index.index'))
