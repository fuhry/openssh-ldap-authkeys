import ldap
import ldap.filter
import ldap.asyncsearch
from ldapauthkeys.logging import get_logger

def domain_to_basedn(domain):
    dn = []
    for part in domain.lower().split('.'):
        dn.append("dc=%s" % (part))
    
    return ','.join(dn)

def connect_to_ldap(address, authdn, authpw, timeout):
    ldap.set_option(ldap.OPT_NETWORK_TIMEOUT, timeout)
    handle = ldap.initialize(address, bytes_mode=False)
    
    handle.set_option(ldap.OPT_PROTOCOL_VERSION, ldap.VERSION3)
    
    if authdn is not None and authpw is not None:
        result = handle.simple_bind_s(authdn, authpw)
    
        if not result:
            raise RuntimeError('Failed to bind to server "%s" as "%s"' % (address, authdn))
    
    get_logger('ldap').info('Connected to LDAP server %s and bound successfully' % (address))
    
    return handle

def fetch_ldap_authkeys(handle, config, searches):
    authkeys = {}
    
    config_attributes = config['ldap']['attributes']
    
    for realm in searches.keys():
        basedn = domain_to_basedn(realm)
        
        search = ldap.asyncsearch.List(handle)
        
        user_searches = []
        for user in searches[realm]:
            user_searches.append(
                ldap.filter.filter_format(
                    "(%s=%s)" % (config_attributes['username'], '%s'),
                    [user]
                )
            )
                                        
        search_filter = "(&%s(%s=*)(|%s))" % (
            config['ldap']['filters']['user'],
            config_attributes['ssh_key'],
            ''.join(user_searches)
        )
        
        get_logger('ldap').info("Searching LDAP in base \"%s\" for filter \"%s\"" % (basedn, search_filter))
        
        search.startSearch(
            basedn,
            ldap.SCOPE_SUBTREE,
            search_filter,
            [config_attributes['username'], config_attributes['ssh_key']]
        )
        
        search.processResults()
        
        for result in search.allResults:
            rcode, entry = result
            
            dn, attrs = entry
            
            if not config_attributes['ssh_key'] in attrs.keys():
                continue
            
            if realm.upper() == config['ldap']['default_realm']:
                user_format = attrs[config_attributes['username']][0].decode('utf-8')
            else:
                user_format = "%s@%s" % (
                    attrs[config_attributes['username']][0].decode('utf-8'),
                    realm.upper()
                )
            
            ssh_keys = []
            for k in attrs[config_attributes['ssh_key']]:
                ssh_keys.append(k.decode('utf-8'))
            
            authkeys[user_format] = {
                config_attributes['ssh_key']: ssh_keys
            }
    
    return authkeys