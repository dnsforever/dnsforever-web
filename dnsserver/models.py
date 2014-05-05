from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Unicode, Boolean, DateTime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import sessionmaker, validates, relationship
from sqlalchemy.sql import functions
from sqlalchemy.ext.declarative import declarative_base
import re


engine = create_engine('sqlite:///database.db')

Session = sessionmaker(autocommit=True)
Session.configure(bind=engine)

Base = declarative_base()


@property
def _serialize(self):
    return {}
Base.serialize = _serialize


class User(Base):
    __tablename__ = 'user'

    EMAIL_PATTERN = re.compile('[^@]+@[^@]+\.[^@]+')

    id = Column(Integer, primary_key=True)

    name = Column(Unicode(100), nullable=False, index=True)

    email = Column(Unicode(100), nullable=True, index=True, unique=True)
    email_validate = Column(Boolean, nullable=False, default=False)
    password = Column(Unicode(100), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False,
                        default=functions.now())

    @validates('email')
    def email_validates(self, key, email):
        if email is None:
            return None
        email = email.strip()
        if self.EMAIL_PATTERN.match(email):
            return email
        raise ValueError

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {'id': self.id,
                'name': self.name,
                'email': self.email}


class Domain(Base):
    __tablename__ = 'domain'

    id = Column(Integer, primary_key=True)

    domain = Column(String(256), nullable=False)

    owner_id = Column(Integer, ForeignKey('user.id'), nullable=False,
                      index=True)
    owner = relationship(User, backref='domain')

    created_at = Column(DateTime(timezone=True), nullable=False,
                        default=functions.now())


class RecordDDNS(Base):
    __tablename__ = 'record_ddns'

    id = Column(Integer, primary_key=True)

    domain_id = Column(Integer, ForeignKey('domain.id'), nullable=False,
                       index=True)
    domain = relationship(Domain, backref='ddns')

    name = Column(String(256), nullable=True)
    ip = Column(String(16), nullable=False)
    memo = Column(Unicode(1024), default=u'')


class RecordA(Base):
    __tablename__ = 'record_a'

    id = Column(Integer, primary_key=True)

    domain_id = Column(Integer, ForeignKey('domain.id'), nullable=False,
                       index=True)
    domain = relationship(Domain, backref='a')

    name = Column(String(256), nullable=True)
    ip = Column(String(16), nullable=False)
    memo = Column(Unicode(1024), default=u'')


class RecordAAAA(Base):
    __tablename__ = 'record_aaaa'

    id = Column(Integer, primary_key=True)

    domain_id = Column(Integer, ForeignKey('domain.id'), nullable=False,
                       index=True)
    domain = relationship(Domain, backref='aaaa')

    name = Column(String(256), nullable=True)
    ip = Column(String(40), nullable=False)
    memo = Column(Unicode(1024), default=u'')


class RecordCNAME(Base):
    __tablename__ = 'record_cname'

    id = Column(Integer, primary_key=True)

    domain_id = Column(Integer, ForeignKey('domain.id'), nullable=False,
                       index=True)
    domain = relationship(Domain, backref='cname')

    name = Column(String(256), nullable=True)
    target = Column(String(256), nullable=False)
    memo = Column(Unicode(1024), default=u'')


class RecordMX(Base):
    __tablename__ = 'record_mx'

    id = Column(Integer, primary_key=True)

    domain_id = Column(Integer, ForeignKey('domain.id'), nullable=False,
                       index=True)
    domain = relationship(Domain, backref='mx')

    name = Column(String(256), nullable=True)
    target = Column(String(256), nullable=False)
    rank = Column(Integer)


class RecordTXT(Base):
    __tablename__ = 'record_txt'

    id = Column(Integer, primary_key=True)

    domain_id = Column(Integer, ForeignKey('domain.id'), nullable=False,
                       index=True)
    domain = relationship(Domain, backref='txt')

    name = Column(String(256), nullable=True)
    text = Column(String(256), nullable=False)
