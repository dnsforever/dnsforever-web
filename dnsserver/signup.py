from flask import Blueprint, render_template
from dnsserver.tools.session import login

app = Blueprint('signup', __name__, url_prefix='/signup')


@app.route('/', methods=['GET', 'POST'])
@login(False, '/')
def index():
    return render_template('signup.html')
