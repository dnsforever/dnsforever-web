from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Unicode, Boolean, DateTime, \
    UnicodeText
from sqlalchemy import ForeignKey
from sqlalchemy.event import listen
from sqlalchemy.orm import sessionmaker, validates, relationship, backref
from sqlalchemy.sql import functions
from sqlalchemy.ext.declarative import declarative_base
import re

from dnsforever.config import database_url

engine = create_engine(database_url, pool_recycle=300)

Session = sessionmaker(autocommit=True)
Session.configure(bind=engine)

Base = declarative_base()


def check_domain(domain):
    if len(domain) > 255:
        raise ValueError('Domain name is too long.')
    for label in domain.split('.'):
        if len(label) > 63:
            raise ValueError('Domain name is too long.')
    return True


class User(Base):
    __tablename__ = 'user'

    EMAIL_PATTERN = re.compile('[^@]+@[^@]+\.[^@]+')

    id = Column(Integer, primary_key=True)

    name = Column(Unicode(100), nullable=False)

    email = Column(Unicode(100), nullable=False, index=True, unique=True)
    password = Column(Unicode(100), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False,
                        default=functions.now())
    type = Column(Integer, nullable=False, default=2)

    @validates('email')
    def email_validates(self, key, email):
        if email is None:
            return None
        email = email.strip()
        if self.EMAIL_PATTERN.match(email):
            return email
        raise ValueError


class DomainOwnerShip(Base):
    __tablename__ = 'domain_ownership'

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user = relationship(User, backref='user.ownership')

    domain_id = Column(Integer, ForeignKey('domain.id'), nullable=False)
    domain = relationship('Domain', backref='ownership')

    permission = Column(UnicodeText, nullable=False)


class Domain(Base):
    __tablename__ = 'domain'

    DOMAIN_PATTERN = re.compile('^([a-z0-9\-]+\.)+([a-z0-9\-]+)$')

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False,
                        default=functions.now())

    parent_id = Column(Integer, ForeignKey('domain.id'), nullable=True,
                       default=None)
    inheritable = Column(Boolean, nullable=False, default=True)

    @validates('domain')
    def domain_validates(self, key, domain):
        if not isinstance(domain, str):
            raise ValueError
        if not self.DOMAIN_PATTERN.match(domain):
            raise ValueError

        check_domain(domain)
        return domain


class Record(Base):
    __tablename__ = 'record'

    id = Column(Integer, primary_key=True)
    service = Column(UnicodeText, nullable=False)

    domain_id = Column(Integer, ForeignKey('domain.id'), nullable=False)
    domain = relationship(Domain, backref='records')

    name = Column(Unicode(255), nullable=True)
    type = Column(Unicode(32), nullable=False)
    cls = Column(Integer, nullable=False)
    ttl = Column(Integer, nullable=False)
    rdata = Column(Unicode(255), nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': None,
        'polymorphic_on': service,
    }


class RecordA(Record):
    __tablename__ = 'record_a'

    __mapper_args__ = {
        'polymorphic_identity': 'A',
    }

    def __init__(self, domain, name, ip, ttl=3600):
        self.domain = domain
        self.name = name
        self.rdata = ip
        self.ttl = ttl
        self.cls = 0
        self.type = u'A'

    id = Column(Integer, ForeignKey('record.id'), primary_key=True)
    memo = Column(Unicode(1024), default=u'')

"""
def record_insert_listener(mapper, connection, target):
    if target.name is None:
        target.fullname = target.domain.domain
    else:
        target.fullname = '%s.%s' % (target.name, target.domain.domain)

listen(RecordA, 'before_insert', record_insert_listener)
"""

Base.metadata.create_all(engine)

session = Session()

domain = Domain(name='test.com')
with session.begin():
    session.add(domain)

da = RecordA(domain, u'a', u'1.1.1.1')
with session.begin():
    session.add(da)

print da.name
Base.metadata.drop_all(engine)



