from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Unicode, Boolean, DateTime, \
    UnicodeText
from sqlalchemy import ForeignKey
from sqlalchemy.orm import sessionmaker, validates, relationship, backref
from sqlalchemy.sql import functions
from sqlalchemy.ext.declarative import declarative_base
import re
import unittest
import string
import random

from dnsforever.config import database_url, webforwarding_domain


Base = declarative_base()


def random_string(size=40, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in xrange(size))


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


class Token(Base):
    __tablename__ = 'token'

    id = Column(Integer, primary_key=True)

    type = Column(Unicode(127), nullable=False)
    token = Column(Unicode(127), nullable=False)
    data = Column(UnicodeText, nullable=False)


class Domain(Base):
    __tablename__ = 'domain'

    DOMAIN_PATTERN = re.compile('^([a-z0-9\-]+\.)+([a-z0-9\-]+)$')

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False,
                        default=functions.now())

    parent_id = Column(Integer, ForeignKey('domain.id'), nullable=True,
                       default=None)
    parent = relationship('Domain')

    inheritable = Column(Boolean, nullable=False, default=True)

    @validates('domain')
    def domain_validates(self, key, domain):
        if not isinstance(domain, str):
            raise ValueError
        if not self.DOMAIN_PATTERN.match(domain):
            raise ValueError

        check_domain(domain)
        return domain


class DomainOwnership(Base):
    __tablename__ = 'domain_ownership'

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user = relationship(User, backref='ownership')

    domain_id = Column(Integer, ForeignKey('domain.id'), nullable=False)
    domain = relationship(Domain, backref='ownership')

    master = Column(Boolean, nullable=False, default=False)
    inheritable = Column(Boolean, nullable=False, default=False)


class NameServer(Base):
    __tablename__ = 'nameserver'

    id = Column(Integer, primary_key=True)

    domain = Column(String(255), nullable=False)
    ip = Column(String(64), nullable=False)
    status = Column(Unicode(32), nullable=False)


class Record(Base):
    __tablename__ = 'record'

    id = Column(Integer, primary_key=True)
    service = Column(UnicodeText, nullable=False)

    domain_id = Column(Integer, ForeignKey('domain.id'), nullable=False)
    domain = relationship(Domain, backref='records')

    name = Column(String(255), nullable=True)
    type = Column(String(32), nullable=False)
    cls = Column(Integer, nullable=False)
    ttl = Column(Integer, nullable=False)
    rdata = Column(String(255), nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': None,
        'polymorphic_on': service,
    }


class RecordA(Record):
    __tablename__ = 'record_a'

    __mapper_args__ = {
        'polymorphic_identity': 'A',
    }

    def __init__(self, domain, name, ip, memo=u'', ttl=3600):
        self.domain = domain
        self.name = name
        self.rdata = ip
        self.ttl = ttl
        self.cls = 0
        self.type = u'A'
        self.memo = memo

    id = Column(Integer, ForeignKey('record.id'), primary_key=True)
    domain = relationship(Domain, backref='a')
    memo = Column(UnicodeText, default=u'')

    @property
    def ip(self):
        return self.rdata

    @ip.setter
    def ip(self, value):
        self.rdata = value


class RecordAAAA(Record):
    __tablename__ = 'record_aaaa'

    __mapper_args__ = {
        'polymorphic_identity': 'AAAA',
    }

    def __init__(self, domain, name, ip, memo=u'', ttl=3600):
        self.domain = domain
        self.name = name
        self.rdata = ip
        self.ttl = ttl
        self.cls = 0
        self.type = u'AAAA'
        self.memo = memo

    id = Column(Integer, ForeignKey('record.id'), primary_key=True)
    domain = relationship(Domain, backref='aaaa')
    memo = Column(UnicodeText, default=u'')

    @property
    def ip(self):
        return self.rdata

    @ip.setter
    def ip(self, value):
        self.rdata = value


class RecordCNAME(Record):
    __tablename__ = 'record_cname'

    __mapper_args__ = {
        'polymorphic_identity': 'CNAME',
    }

    def __init__(self, domain, name, target, memo=u'', ttl=3600):
        self.domain = domain
        self.name = name
        self.rdata = target
        self.ttl = ttl
        self.cls = 0
        self.type = u'CNAME'
        self.memo = memo

    id = Column(Integer, ForeignKey('record.id'), primary_key=True)
    domain = relationship(Domain, backref='cname')
    memo = Column(UnicodeText, default=u'')

    @property
    def target(self):
        return self.rdata

    @target.setter
    def target(self, value):
        self.rdata = value


class RecordMX(Record):
    __tablename__ = 'record_mx'

    __mapper_args__ = {
        'polymorphic_identity': 'MX',
    }

    def __init__(self, domain, name, preference, target, memo=u'', ttl=3600):
        self.domain = domain
        self.name = name
        self.preference = preference
        self.target = target
        self.ttl = ttl
        self.cls = 0
        self.type = u'MX'
        self.memo = memo

    id = Column(Integer, ForeignKey('record.id'), primary_key=True)
    domain = relationship(Domain, backref='mx')
    memo = Column(UnicodeText, default=u'')

    @property
    def preference(self):
        if not isinstance(self.rdata, basestring):
            print([self.rdata])
            return 2
        rdata = self.rdata.split(' ', 1)
        if len(rdata) != 2:
            return 3

        return int(rdata[0])

    @preference.setter
    def preference(self, value):
        self.rdata = '%d %s' % (value, self.target)

    @property
    def target(self):
        if not isinstance(self.rdata, basestring):
            return ''
        rdata = self.rdata.split(' ', 1)
        if len(rdata) != 2:
            return ''

        return rdata[1]

    @target.setter
    def target(self, value):
        self.rdata = '%d %s' % (self.preference, value)


class RecordTXT(Record):
    __tablename__ = 'record_txt'

    __mapper_args__ = {
        'polymorphic_identity': 'TXT',
    }

    def __init__(self, domain, name, txt, memo=u'', ttl=3600):
        self.domain = domain
        self.name = name
        self.txt = txt
        self.ttl = ttl
        self.cls = 0
        self.type = u'TXT'
        self.memo = memo

    id = Column(Integer, ForeignKey('record.id'), primary_key=True)
    domain = relationship(Domain, backref='txt')
    memo = Column(UnicodeText, default=u'')

    @property
    def txt(self):
        return self.rdata[1:-1]

    @txt.setter
    def txt(self, value):
        self.rdata = '"%s"' % value


class RecordNS(Record):
    __tablename__ = 'record_ns'

    __mapper_args__ = {
        'polymorphic_identity': 'NS',
    }

    def __init__(self, domain, name, target, memo=u'', ttl=3600):
        self.domain = domain
        self.name = name
        self.rdata = target
        self.ttl = ttl
        self.cls = 0
        self.type = u'NS'
        self.memo = memo

    id = Column(Integer, ForeignKey('record.id'), primary_key=True)
    domain = relationship(Domain, backref='ns')
    memo = Column(UnicodeText, default=u'')

    @property
    def target(self):
        return self.rdata

    @target.setter
    def target(self, value):
        self.rdata = value


class RecordServiceNameServer(Record):
    __tablename__ = 'record_servicenameserver'

    __mapper_args__ = {
        'polymorphic_identity': 'servicenameserver',
    }

    def __init__(self, domain, nameserver, ttl=3600):
        self.domain = domain
        self.name = ''
        self.rdata = nameserver.ip
        self.ttl = ttl
        self.cls = 0
        self.type = u'NS'
        self.nameserver = nameserver

    id = Column(Integer, ForeignKey('record.id'), primary_key=True)

    nameserver_id = Column(Integer, ForeignKey('nameserver.id'), nullable=False)
    nameserver = relationship(NameServer)


class RecordDDNS_A(Record):
    __tablename__ = 'record_ddns_a'

    __mapper_args__ = {
        'polymorphic_identity': 'ddns_a',
    }

    def __init__(self, domain, name, ip, ttl=300):
        self.domain = domain
        self.name = name
        self.rdata = ip
        self.ttl = ttl
        self.cls = 0
        self.type = u'A'
        self.ddns_key = random_string(10)

    id = Column(Integer, ForeignKey('record.id'), primary_key=True)
    ddns_key = Column(Unicode(80), nullable=False)
    memo = Column(UnicodeText, default=u'')

    @property
    def ip(self):
        return self.rdata

    @ip.setter
    def ip(self, value):
        self.rdata = value

    def reset_key(self):
        self.ddns_key = random_string(10)


class RecordWebForwarding(Record):
    __tablename__ = 'record_webforwarding'

    __mapper_args__ = {
        'polymorphic_identity': 'webforwarding',
    }

    def __init__(self, domain, name, target_url, type='iframe', ttl=3600):
        self.domain = domain
        self.name = name
        self.rdata = webforwarding_domain
        self.ttl = ttl
        self.cls = 0
        self.type = u'CNAME'
        self.forwarding_target = target_url
        self.forwarding_type = type


    id = Column(Integer, ForeignKey('record.id'), primary_key=True)

    forwarding_target = Column(String(1024), nullable=False)
    forwarding_type = Column(String(32), nullable=False, default='iframe')

    memo = Column(UnicodeText, default=u'')


class RecordWebParking(Record):
    __tablename__ = 'record_webparking'

    __mapper_args__ = {
        'polymorphic_identity': 'webparking',
    }

    def __init__(self, domain, name, ttl=3600):
        self.domain = domain
        self.name = name
        self.rdata = webforwarding_domain
        self.ttl = ttl
        self.cls = 0
        self.type = u'CNAME'
        self.parking_type = 'default'
        self.parking_data = u''


    id = Column(Integer, ForeignKey('record.id'), primary_key=True)

    parking_type = Column(String(32), nullable=False, default='default')
    parking_data = Column(UnicodeText, default=u'')

    memo = Column(UnicodeText, default=u'')


engine = create_engine(database_url, pool_recycle=300)

Session = sessionmaker(autocommit=True)
Session.configure(bind=engine)


def db_install():
    Base.metadata.create_all(engine)


def db_uninstall():
    Base.metadata.drop_all(engine)


class UserTestCase(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(engine)

    def test_user(self):
        s = Session()

        user1 = User(name=u'dnsforever',
                     email=u'test@dnsforever.kr',
                     password=u'test')

        with s.begin():
            s.add(user1)

        user2 = s.query(User).filter(User.email=='test@dnsforever.kr').first()

        self.assertEqual(user1.id, user2.id)

    def tearDown(self):
        Base.metadata.drop_all(engine)


class DomainTestCase(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(engine)
        s = Session()
        user = User(name='dnsforever',
                    email='test@dnsforever.kr',
                    password='test')

        with s.begin():
            s.add(user)

        self.user_id = user.id

    def test_domain(self):
        s = Session()
        user = s.query(User).filter(User.id==self.user_id).first()
        self.assertIsNotNone(user)

        domain = Domain(name='dnsforever.kr')
        domain_ownership = DomainOwnership(user=user, domain=domain)

        with s.begin():
            s.add(domain_ownership)

        ownerships = s.query(DomainOwnership).filter(DomainOwnership.user==user).all()
        domain_names = [ownership.domain.name for ownership in ownerships]

        self.assertIn('dnsforever.kr', domain_names)

    def tearDown(self):
        Base.metadata.drop_all(engine)


class RecordTestCase(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(engine)
        s = Session()
        user = User(name='dnsforever',
                    email='test@dnsforever.kr',
                    password='test')
        domain = Domain(name='dnsforever.kr')
        domain_ownership = DomainOwnership(user=user, domain=domain)

        with s.begin():
            s.add(domain_ownership)

        self.user_id = user.id
        self.domain_id = domain.id
        self.domain_name = 'dnsforever.kr'

    def test_record_a(self):
        s = Session()
        domain = s.query(Domain).filter(User.id==self.domain_id).first()
        self.assertIsNotNone(domain)

        record = RecordA(domain=domain, name='test', ip='127.0.0.1')

        with s.begin():
            s.add(record)

        self.assertEqual(record.name, 'test')
        self.assertEqual(record.type, 'A')
        self.assertEqual(record.rdata, '127.0.0.1')

    def test_record_aaaa(self):
        s = Session()
        domain = s.query(Domain).filter(User.id==self.domain_id).first()
        self.assertIsNotNone(domain)

        record = RecordAAAA(domain=domain, name='test', ip='::1')

        with s.begin():
            s.add(record)

        self.assertEqual(record.name, 'test')
        self.assertEqual(record.type, 'AAAA')
        self.assertEqual(record.rdata, '::1')

    def test_record_cname(self):
        s = Session()
        domain = s.query(Domain).filter(User.id==self.domain_id).first()
        self.assertIsNotNone(domain)

        record = RecordCNAME(domain=domain, name='test', target='cname.dnsforever.kr')

        with s.begin():
            s.add(record)

        self.assertEqual(record.name, 'test')
        self.assertEqual(record.type, 'CNAME')
        self.assertEqual(record.rdata, 'cname.dnsforever.kr')

    def test_record_mx(self):
        s = Session()
        domain = s.query(Domain).filter(User.id==self.domain_id).first()
        self.assertIsNotNone(domain)

        record = RecordMX(domain=domain, name='test', preference=1, target='mx.dnsforever.kr')

        with s.begin():
            s.add(record)

        self.assertEqual(record.name, 'test')
        self.assertEqual(record.type, 'MX')
        self.assertEqual(record.rdata, '1 mx.dnsforever.kr')
        self.assertEqual(record.preference, 1)
        self.assertEqual(record.target, 'mx.dnsforever.kr')

        record.preference = 10
        self.assertEqual(record.rdata, '10 mx.dnsforever.kr')
        record.target = 'dnsforever.kr'
        self.assertEqual(record.rdata, '10 dnsforever.kr')

    def test_record_txt(self):
        s = Session()
        domain = s.query(Domain).filter(User.id==self.domain_id).first()
        self.assertIsNotNone(domain)

        record = RecordTXT(domain=domain, name='test', txt='a=b')

        with s.begin():
            s.add(record)

        self.assertEqual(record.name, 'test')
        self.assertEqual(record.type, 'TXT')
        self.assertEqual(record.rdata, '"a=b"')
        self.assertEqual(record.txt, 'a=b')

    def test_record_ns(self):
        s = Session()
        domain = s.query(Domain).filter(User.id==self.domain_id).first()
        self.assertIsNotNone(domain)

        record = RecordNS(domain=domain, name='ns', target='ns.dnsforever.kr')

        with s.begin():
            s.add(record)

        self.assertEqual(record.name, 'ns')
        self.assertEqual(record.type, 'NS')
        self.assertEqual(record.rdata, 'ns.dnsforever.kr')

    def test_record_ddns_a(self):
        s = Session()
        domain = s.query(Domain).filter(User.id==self.domain_id).first()
        self.assertIsNotNone(domain)

        record = RecordDDNS_A(domain=domain, name='ddnsa', ip='127.0.0.1')

        with s.begin():
            s.add(record)

        record = s.query(Record).filter(Record.domain==domain)\
                                .filter(Record.name=='ddnsa')\
                                .filter(Record.type=='A').first()

        self.assertEqual(record.name, 'ddnsa')
        self.assertEqual(record.type, 'A')
        self.assertEqual(record.rdata, '127.0.0.1')

        key1 = record.ddns_key
        record.reset_key()
        key2 = record.ddns_key
        self.assertNotEqual(key1, key2)

    def test_record_webforwarding(self):
        s = Session()
        domain = s.query(Domain).filter(User.id==self.domain_id).first()
        self.assertIsNotNone(domain)

        record = RecordWebForwarding(domain=domain, name='webforwarding', target_url='http://dnsforever.kr/')

        with s.begin():
            s.add(record)

        record = s.query(Record).filter(Record.domain==domain)\
                                .filter(Record.name=='webforwarding').first()

        self.assertEqual(record.name, 'webforwarding')
        self.assertEqual(record.type, 'CNAME')
        self.assertEqual(record.rdata, webforwarding_domain)

    def test_record_webparking(self):
        s = Session()
        domain = s.query(Domain).filter(User.id==self.domain_id).first()
        self.assertIsNotNone(domain)

        record = RecordWebParking(domain=domain, name='webparking')

        with s.begin():
            s.add(record)

        record = s.query(Record).filter(Record.domain==domain)\
                                .filter(Record.name=='webparking')\
                                .filter(Record.type=='CNAME').first()

        self.assertEqual(record.name, 'webparking')
        self.assertEqual(record.type, 'CNAME')
        self.assertEqual(record.rdata, webforwarding_domain)
        self.assertEqual(record.service, 'webparking')


    def tearDown(self):
        Base.metadata.drop_all(engine)


