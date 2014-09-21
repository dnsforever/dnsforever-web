import string

from flask import Blueprint, g
from flask.ext import restful

from dnsforever.models import Domain, DomainOwnership, Record

app = Blueprint('apis', __name__, url_prefix='/apis')
api = restful.Api(app)


class ServerUpdate(restful.Resource):
    def get(self):
        domains = g.session.query(Domain).all()

        result = {}

        for domain in domains:
            records = g.session.query(Record)\
                               .filter(Record.domain == domain)\
                               .all()
            zone = [string.join([record.name or '@', record.type, record.rdata], ' ')
                    for record in records]

            soa_record = '@ SOA ns1.dnsforever.kr. root.%s. '\
                         '%d 3600 600 86400 3600' %\
                         (domain.name, domain.update_serial)
            zone.insert(0, soa_record)

            result[domain.name] = zone

        return result

api.add_resource(ServerUpdate, '/server/update')