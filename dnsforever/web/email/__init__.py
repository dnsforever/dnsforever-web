# -*- coding: utf-8 -*-

import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header

from flask import g, url_for
from jinja2 import Environment, FileSystemLoader

from dnsforever.models import EmailValidation, FindPasswd
from dnsforever.config import smtp_ssl, smtp_host, smtp_port, smtp_account

email_env = Environment(loader=FileSystemLoader(os.path.dirname(__file__) +
                                                '/templates'))
email_env.globals = {'g': g, 'url_for': url_for}

__all__ = ['email_validation']


def send_text_email(to, subject, body):
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = 'noreply@dnsforever.kr'
    msg['To'] = to

    if not smtp_ssl:
        s = smtplib.SMTP(smtp_host, smtp_port)
    else:
        s = smtplib.SMTP_SSL(smtp_host, smtp_port)

    if smtp_account:
        s.login(*smtp_account)
    s.sendmail('noreply@dnsforever.kr', [to], msg.as_string())
    s.quit()


def email_validation(user):
    if user.type != 2:
        return

    validation_email = EmailValidation(user=user)
    evs = g.session.query(EmailValidation)\
                   .filter(EmailValidation.user == user)\
                   .all()

    with g.session.begin():
        for ev in evs:
            g.session.delete(ev)

        g.session.add(validation_email)

    template = email_env.get_template('email_validation.txt')
    body = template.render(user=user,
                           token=validation_email.token)

    send_text_email(to=user.email,
                    subject=u'DNS Forever: 회원 가입확인',
                    body=body)


def find_passwd(user):
    findpasswd_info = FindPasswd(user=user)
    findpasswd_list = g.session.query(FindPasswd)\
                               .filter(FindPasswd.user == user)\
                               .all()

    with g.session.begin():
        for fp in findpasswd_list:
            g.session.delete(fp)

        g.session.add(findpasswd_info)

    template = email_env.get_template('find_passwd.txt')
    body = template.render(token=findpasswd_info.token)

    send_text_email(to=user.email,
                    subject=u'DNS Forever: 비밀번호 초기화',
                    body=body)
