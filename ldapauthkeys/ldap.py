import ldap
import ldap.filter
import ldap.asyncsearch
from ldapauthkeys.logging import get_logger

def domain_to_basedn(domain):
    """
    Convert a domain (example.com) to base DN (dc=example,dc=com)
    """
    dn = []
    for part in domain.lower().split('.'):
        dn.append("dc=%s" % (part))

    return ','.join(dn)

def connect_to_ldap(address, authdn, authpw, timeout):
    """
    Connect to an LDAP server.

    Inputs:
      - LDAP server URI (ldaps://host:port)
      - DN to bind as (None for anonymous bind)
      - Password for simple bind (None for anonymous bind)

    Output:
      - python-ldap connection instance
    """
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
    """
    Fetch SSH keys from LDAP and return as a dict.

    Inputs:
      - LDAP connection handle returned from connect_to_ldap()
      - Configuration hash returned from load_config() in config.py
      - LDAP search dict returned from
        AuthorizedEntityCollection.to_ldap_search() in authmap.py

    Output:
      - Dict in the format of user: [ssh key attribute]: [list of SSH keys].
        "user" is the username, with "@REALM" appended for users not in the
        default realm. "ssh key attribute" means ldap.attributes.ssh_key from
        the configuration yaml. "list of SSH keys" is a list of Unicode strings
        containing OpenSSH public keys.
    """
    authkeys = {}

    config_attributes = config['ldap']['attributes']

    # One search per base dn
    for realm in searches.keys():
        basedn = domain_to_basedn(realm)

        search = ldap.asyncsearch.List(handle)

        """
        Build the user filter.

        It's worth noting here that this will build an "or" expression
        consisting of one possibility for each user. For massive (500+) user
        groups this may seem a bit concerning. This approach was tested at a
        1,500 person organization and extensive performance data was collected
        to verify that these large search queries are more sustainable than the
        alternatives of simply fetching all users and cutting down the result
        set locally, or fetching each user individually by calculating the DN.
        The caveat is that it does require your LDAP database to be properly
        indexed on the uid attribute, which is relatively doable in OpenLDAP but
        might be a tall order for Windows/AD.
        """
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

        # Perform search
        search.startSearch(
            basedn,
            ldap.SCOPE_SUBTREE,
            search_filter,
            [config_attributes['username'], config_attributes['ssh_key']]
        )

        search.processResults()

        for result in search.allResults:
            # Isolate entry, DN and attributes
            rcode, entry = result

            dn, attrs = entry

            if not config_attributes['ssh_key'] in attrs.keys():
                continue

            # Format the username.
            if realm.upper() == config['ldap']['default_realm'].upper():
                # Default realm. Don't append realm name.
                user_format = attrs[config_attributes['username']][0].decode('utf-8')
            else:
                # Non-default realm, add "@REALM" to the username. This directly
                # affects the value of the username_env_var.
                user_format = "%s@%s" % (
                    attrs[config_attributes['username']][0].decode('utf-8'),
                    realm.upper()
                )

            # Decode SSH keys as UTF-8
            ssh_keys = []
            for k in attrs[config_attributes['ssh_key']]:
                ssh_keys.append(k.decode('utf-8'))

            # Produce output
            # Note that this assumes no duplicates. If you have a duplicate
            # LDAP entry, for example two users in different OUs with the same
            # username, this will overwrite one with the other. This edge case
            # is not considered in-scope.
            authkeys[user_format] = {
                config_attributes['ssh_key']: ssh_keys
            }

    return authkeys