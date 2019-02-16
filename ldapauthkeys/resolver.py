import dns.resolver
import re

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
    result = []
    
    for r in records:
        result.append("%s://%s:%d" % (protocol, r.hostname, r.port))
    
    return result

def basedn_to_domain(basedn):
    """
    Convert an LDAP base DN "dc=example,dc=com" into a DNS domain "example.com".
    """
    if not isinstance(basedn, str):
        raise TypeError("basedn is expected to be a string")
        
    basedn = basedn.lower()
    expr = re.compile(r'^(dc=[a-z0-9-]+)(, *dc=[a-z0-9-]+)*$')
    
    if not expr.match(basedn):
        raise ValueError("basedn must consist of only \"dc\" components to use DNS SRV lookup")
    
    domain = []
    basedn = re.split(', *dc=', basedn[3:])
    
    return '.'.join(basedn)

def lookup_srv(record):
    """
    Perform a SRV record lookup, returning a list of SrvRecord objects.
    """
    answer = dns.resolver.query(record, 'SRV')
    
    result = []
    for rr in answer.rrset:
        result.append(SrvRecord(rr.target.to_unicode(), rr.port, rr.priority, rr.weight))
    
    return sort_srv_results(result)

def resolve_ldap_srv(basedn):
    """
    Given an LDAP basedn, attempt to auto-discover LDAP servers for the domain
    name it represents. Returns a list of URLs in the format of
    "ldap(s)://server:port".
    """
    domain = basedn_to_domain(basedn)
        
    # try LDAPS first
    results = lookup_srv('_ldaps._tcp.%s' % (domain))
    if len(results):
        return protocolize(results, 'ldaps')
    
    # then try LDAP
    results = lookup_srv('_ldap._tcp.%s' % (domain))
    if len(results):
        return protocolize(results, 'ldap')
    
    raise RuntimeError("Couldn't find any LDAP SRV records for %s" % (domain))