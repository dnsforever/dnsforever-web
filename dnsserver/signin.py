from flask import Blueprint, render_template
from dnsserver.tools.session import login

app = Blueprint('signin', __name__, url_prefix='/signin')


@app.route('/', methods=['GET', 'POST'])
@login(False, '/')
def index():
    return render_template('signin.html')
