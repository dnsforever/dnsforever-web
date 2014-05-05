from flask import Blueprint, g, render_template
from dnsserver.tools.session import login

app = Blueprint('domain', __name__, url_prefix='/domain')


@app.route('/')
@login(True, '/')
def index():
    domain_list = g.domain_list
    return render_template('domain.html', domain_list=domain_list)


@app.route('/new', methods=['GET', 'POST'])
@login(True, '/')
def new():
    return render_template('domain_new.html')


@app.route('/<string:domain>', methods=['GET', 'POST'])
@login(True, '/')
def detail(domain):
    return render_template('domain_detail.html', domain_name=domain)
