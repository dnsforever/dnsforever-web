#!/usr/bin/env python
from dnsforever.dns import create_server

server = create_server()

if __name__ == '__main__':
    server.run()
