from flask import Blueprint, render_template
from dnsserver.tools.session import login

app = Blueprint('reserpasswd', __name__, url_prefix='/resetpasswd')


@app.route('/', methods=['GET', 'POST'])
@login(False, '/')
def signin_main():
    return render_template('resetpasswd.html')
