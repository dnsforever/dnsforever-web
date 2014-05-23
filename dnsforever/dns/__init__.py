#!/usr/bin/env python

from twisted.internet import reactor
from twisted.names.dns import DNSDatagramProtocol
from twisted.names.server import DNSServerFactory

from dnsforever.dns.dbresolver import DatabaseAuthority


def create_server():
    authority = DatabaseAuthority()
    verbosity = 0

    factory = DNSServerFactory(authorities=[authority],
                               verbose=verbosity)

    protocol = DNSDatagramProtocol(factory)
    factory.noisy = protocol.noisy = verbosity

    reactor.listenUDP(53, protocol)
    reactor.listenTCP(53, factory)
    return reactor
