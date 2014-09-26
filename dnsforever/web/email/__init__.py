# -*- coding: utf-8 -*-

import os
import smtplib
from email.mime.text import MIMEText

from flask import g, url_for
from jinja2 import Environment, FileSystemLoader

from dnsforever.models import EmailValidation

email_env = Environment(loader=FileSystemLoader(os.path.dirname(__file__) +
                                                '/templates'))
email_env.globals = {'g': g, 'url_for': url_for}

__all__ = ['email_validation']


def send_text_email(to, subject, body):
    if g.debug:
        print body
        return

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = 'noreply@dnsforever.kr'
    msg['To'] = to

    s = smtplib.SMTP('localhost')
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
                    subject=u'DNS Forever: 회원 가입 확인',
                    body=body)
