from ldapauthkeys.logging import get_logger
import dns.resolver
import re

from ldapauthkeys.util import *
from .logging import get_logger

class SrvRecord:
    """
    Represents a single SRV record query. Representing this as an object allows
    SRV query results to be sorted by priority and weight.
    """
    hostname = None
    port = None
    priority = 0
    weight = 0

    def __init__(self, hostname, port, priority, weight):
        self.hostname = hostname.rstrip('.')
        self.port     = port
        self.priority = priority
        self.weight   = weight

def sort_srv_results(results):
    """
    Sort a list of SrvRecords by weight and priority.
    """
    results.sort(key=lambda x: (x.priority << 16) | x.weight)
    return results

def protocolize(records, protocol):
    """
    Given a list of SrvRecords, turn them into URLs in the format of
    "protocol://{record.host}:{record.port}".
    """
    result = [
        "%s://%s:%d" % (protocol, r.hostname, r.port)
        for r in records
    ]

    for url in result:
        get_logger('resolver').info(f'SRV discovery found server: {url}')

    return result

def lookup_srv(record):
    """
    Perform a SRV record lookup, returning a list of SrvRecord objects.
    """
    try:
        answer = dns.resolver.query(record, 'SRV')
    except Exception:
        get_logger('resolve').info("SRV lookup failed")
        return []
 
    result = []
    for rr in answer.rrset:
        result.append(SrvRecord(rr.target.to_unicode(), rr.port, rr.priority, rr.weight))

    return sort_srv_results(result)

def resolve_ldap_srv(domain):
    """
    Given an LDAP basedn, attempt to auto-discover LDAP servers for the domain
    name it represents. Returns a list of URLs in the format of
    "ldap(s)://server:port".
    """
    # try LDAPS first
    results = lookup_srv('_ldaps._tcp.%s' % (domain))
    if len(results):
        return protocolize(results, 'ldaps')

    # then try LDAP
    results = lookup_srv('_ldap._tcp.%s' % (domain))
    if len(results):
        return protocolize(results, 'ldap')

    raise RuntimeError("Couldn't find any LDAP SRV records for %s" % (domain))
