from twisted.names import dns
from twisted.names.error import DomainError
from twisted.names.common import ResolverBase
from twisted.internet import defer
from twisted.python.failure import Failure

from dnsforever import models
from dnsforever.models import Session


class DatabaseAuthority(ResolverBase):
    def __init__(self, connection=None):
        ResolverBase.__init__(self)
        self._cache = {}

    def __setstate__(self, state):
        self.__dict__ = state

    def _query(self, name, type, session, dapth=5):
        if dapth < 0:
            return []

        results = []

        if not isinstance(type, list):
            type = [type]

        type_dict = {dns.A: models.RecordA,
                     dns.AAAA: models.RecordAAAA,
                     dns.CNAME: models.RecordCNAME,
                     dns.MX: models.RecordMX,
                     dns.TXT: models.RecordTXT}

        for t in type:
            results.extend(session.query(type_dict[t])
                                  .filter(type_dict[t].fullname == name).all())

        if not results and dns.CNAME not in type:
            results.extend(self._query(name, dns.CNAME, session, dapth - 1))
            additional = []
            for cname in results:
                additional.extend(self._query(cname.target, type,
                                              session, dapth - 1))
            results.extend(additional)

        return results

    def _make_result(self, result):
        if isinstance(result, models.RecordA):
            return dns.RRHeader(result.fullname, dns.A, dns.IN, result.ttl,
                                dns.Record_A(result.ip, result.ttl),
                                auth=True)
        elif isinstance(result, models.RecordAAAA):
            return dns.RRHeader(result.fullname, dns.AAAA, dns.IN, result.ttl,
                                dns.Record_AAAA(result.ip, result.ttl),
                                auth=True)
        elif isinstance(result, models.RecordCNAME):
            return dns.RRHeader(result.fullname, dns.CNAME, dns.IN, result.ttl,
                                dns.Record_CNAME(result.target, result.ttl),
                                auth=True)
        elif isinstance(result, models.RecordMX):
            return dns.RRHeader(result.fullname, dns.MX, dns.IN, result.ttl,
                                dns.Record_MX(result.rank, result.target,
                                              result.ttl),
                                auth=True)
        elif isinstance(result, models.RecordTXT):
            return dns.RRHeader(result.fullname, dns.TXT, dns.IN, result.ttl,
                                dns.Record_TXT(result.txt, result.ttl),
                                auth=True)

    def _lookup(self, name, cls, type, timeout=None):
        session = Session()

        results = self._query(name, type, session)
        authority = []
        additional = []

        results = [self._make_result(r) for r in results]

        if results:
            return defer.succeed((results, authority, additional))
        elif False and dns._isSubdomainOf(name, self.soa[0]):
            return defer.fail(Failure(dns.AuthoritativeDomainError(name)))

        return defer.fail(Failure(DomainError(name)))
