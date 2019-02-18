import ldap
import ldap.filter
import ldap.asyncsearch
from ldapauthkeys.logging import get_logger
from ldapauthkeys.util import *

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

def check_user_disabled(attrs, disable_options):
    user_disabled = False

    if disable_options['attribute'] is not None \
        and disable_options['op'] is not None \
        and disable_options['value'] is not None:

        disable_attr = attrs[disable_options['attribute']]

        if disable_options['op'] in ['eq', '=', '==']:
            if isinstance(disable_attr, list):
                user_disabled = disable_options['value'] in disable_attr
            else:
                user_disabled = disable_options['value'] == disable_attr
        elif disable_options['op'] in ['ne', 'neq', '!=']:
            if isinstance(disable_attr, list):
                user_disabled = disable_options['value'] not in disable_attr
            else:
                user_disabled = disable_options['value'] != disable_attr
        elif disable_options['op'] in ['bitmask', 'and', '&']:
            mask = 0
            if isinstance(disable_attr, list):
                for m in disable_attr:
                    mask |= int(m)
            else:
                mask = int(disable_attr)

            user_disabled = (mask & int(disable_options['value'])) == int(disable_options['value'])

    return user_disabled

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
    disable_options = config_attributes['user_disabled']

    # One search per base dn
    for basedn in searches.keys():
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
        for user in searches[basedn]:
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

        attrlist = [
            config_attributes['username'], config_attributes['ssh_key']
        ]

        if disable_options['attribute'] is not None:
            attrlist.append(disable_options['attribute'])

        # Perform search
        search.startSearch(
            basedn,
            ldap.SCOPE_SUBTREE,
            search_filter,
            attrlist
        )

        search.processResults()

        for result in search.allResults:
            # Isolate entry, DN and attributes
            rcode, entry = result

            dn, attrs = entry

            # Skip this user if they don't have any SSH keys
            if not config_attributes['ssh_key'] in attrs.keys():
                continue

            user_disabled = check_user_disabled(attrs, disable_options)

            if user_disabled:
                get_logger('ldap').info(
                    'Excluding user "%s" from results because the account is disabled.' % (
                        dn
                    )
                )
                continue

            # Format the username.
            if basedn == config['ldap']['default_realm']:
                # Default realm. Don't append realm name.
                user_format = attrs[config_attributes['username']][0].decode('utf-8')
            else:
                # Non-default realm, add "@REALM" to the username. This directly
                # affects the value of the username_env_var.
                user_format = dn

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