import traceback

from ldapauthkeys.config import *
from ldapauthkeys.logging import *
from ldapauthkeys.resolver import *
from ldapauthkeys.cache import *
from ldapauthkeys.ldap import *
from ldapauthkeys.authmap import *
from ldapauthkeys.renderer import *

def olak_main(argv):
    load_cache_on_failure = False

    try:
        # Get arguments
        args = argv[1:]

        if len(args) < 1:
            raise ArgumentCountError("Missing argument: username")
        elif len(args) == 1:
            user = args[0]
            key_type = None
            key_value = None
        elif len(args) == 3:
            user = args[0]
            key_type = args[1]
            key_value = args[2]
        else:
            raise ArgumentCountError("Invalid argument count")

        # Load the configuration
        config = load_config()

        get_logger('main').info("Starting; user = %s" % (user))

        # Check the cache.
        if config['cache']['lifetime'] > 0 and \
            cache_valid_for_user(user, config['cache']['lifetime'], config['cache']['dir']):

            # Cache is valid. Render cache to authkeys.
            try:
                cached_keys = load_cache(user, config)
                print(render_authkeys(cached_keys, config, key_type, key_value))
                return None
            except Exception as e:
                get_logger('cache').error(
                    "Failed to load cache: %s: %s" % (
                        e.__class__.__name__,
                        repr(e.args)
                    )
                )

        # Cache not valid. Use LDAP.
        get_logger('main').info("No valid cache found. Will go out to LDAP.")

        # If we crash at any point from here on out, attempt to load the cache.
        load_cache_on_failure = config['cache']['allow_stale_cache_on_failure']

        # Get the authmap, which maps local users and groups to LDAP entities
        authmap = get_authmap()
        # Look up the user in the authmap
        auth_entities = lookup_authmap(authmap, user, config)

        if auth_entities.length() < 1:
            get_logger().info('No LDAP users are authorized to access the local account "%s"' % (user))

        # Init LDAP server list
        ldap_server_addresses = None

        try:
            # Attempt SRV lookup
            if config['ldap']['use_dns_srv']:
                if isinstance(config['ldap']['srv_discovery_domain'], str) and config['ldap']['srv_discovery_domain'] != '':
                    ldap_server_addresses = resolve_ldap_srv(
                        config['ldap']['srv_discovery_domain'])
                else:
                    ldap_server_addresses = resolve_ldap_srv(
                        basedn_to_domain(config['ldap']['basedn']))
        except Exception as e:
            get_logger('ldap').warn(
                "LDAP SRV resolution failed: %s: %s" % (
                    e.__class__.__name__,
                    repr(e.args)
                )
            )

        # If SRV lookup failed, fall back to server_uri
        if ldap_server_addresses is None:
            ldap_server_addresses = [
                config['ldap']['server_uri']
            ]

        # Go down the list of servers and try to connect
        connect_errors = {}
        connect_succeeded = False

        for addr in ldap_server_addresses:
            try:
                ldap = connect_to_ldap(addr,
                    config['ldap']['authdn'],
                    config['ldap']['authpw'],
                    config['ldap']['timeout'])

                connect_succeeded = True
            except Exception as e:
                connect_errors[addr] = e

        if not connect_succeeded:
            raise RuntimeError("Unable to connect to any LDAP server. List of errors:\n%s" % (repr(connect_errors)))

        # Convert to a list of LDAP user searches
        ldap_searches = auth_entities.to_ldap_search(ldap, config)

        authkeys = fetch_ldap_authkeys(ldap, config, ldap_searches)
        try:
            write_cache_file(user, authkeys, config)
        except Exception as e:
            get_logger('cache').error(
                'Failed to write cache: %s: %s' % (
                    e.__class__.__name__,
                    repr(e.args)
                )
            )

        print(render_authkeys(authkeys, config, key_type, key_value))

        return None

    except Exception as e:
        get_logger().error(
            "Unhandled error: %s: %s\n%s" % (
                e.__class__.__name__,
                repr(e.args),
                ''.join(traceback.format_tb(e.__traceback__))
            )
        )

        if load_cache_on_failure:
            try:
                cached_keys = load_cache(user, config)
                get_logger().info(
                    "Using cached authkeys due to crash"
                )
                print(render_authkeys(cached_keys, config, key_type, key_value))
            except Exception as ecache:
                get_logger().error(
                    "Could not perform emergency cache use: %s: %s" % (
                        ecache.__class__.__name__,
                        repr(ecache.args)
                    )
                )

class ArgumentCountError(Exception):
    pass