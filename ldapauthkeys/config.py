import yaml
from ldapauthkeys.util import *

_cached_config = None

config_paths = [
    './olak.yml',
    '/etc/openssh-ldap-authkeys/olak.yml',
]

default_config = {
    'ldap': {
        'use_dns_srv': False,
        'srv_discovery_domain': '',
        'filters': {
            'user': '(&(objectClass=posixAccount)(sshPublicKey=*))',
            'group': '(objectClass=posixGroup)'
        },
        'authdn': None,
        'authpw': None,
        'group_membership': 'uid',
        'attributes': {
            'username': 'uid',
            'ssh_key': 'sshPublicKey',
            'group_name': 'cn',
            'group_member': 'memberUid',
            'user_disabled': {
                'attribute': None,
                'op': None,
                'value': None,
            }
        }
    },
    'cache': {
        'lifetime': 900,
        'dir': '/var/run/ldap/ssh-cache',
        'allow_stale_cache_on_failure': False
    },
    'output': {
        'username_env_var': 'OLAK_USER'
    },
    'logging': {
        'to_stdout': False,
        'to_stderr': False,
    }
}

def array_merge_unique(arr1, arr2):
    """
    Merge two arrays and return a result with no duplicates.
    """
    for e in arr2:
        if not e in arr1:
            arr1.append(e)

    return arr1

def deep_merge(hash1, hash2):
    """
    Deep merge two hashes.
    """
    total_keys = array_merge_unique(list(hash1.keys()), list(hash2.keys()))
    result = {}

    for k in total_keys:
        if k in hash1.keys() and k in hash2.keys() and isinstance(hash1[k], dict):
            result[k] = deep_merge(hash1[k], hash2[k])
        elif k in hash1.keys() and k in hash2.keys() and isinstance(hash1[k], list):
            result[k] = array_merge_unique(hash1[k], hash2[k])
        elif k in hash2.keys():
            result[k] = hash2[k]
        elif k in hash1.keys():
            result[k] = hash1[k]

    return result

def _load_config():
    """
    Internal function to load the configuration
    """
    for path in config_paths:
        try:
            with open(path) as fp:
                config = deep_merge(default_config, yaml.load(fp, Loader=yaml.loader.SafeLoader))
                if 'default_realm' in config['ldap'].keys():
                    config['ldap']['default_realm'] = domain_to_basedn(config['ldap']['default_realm'])
                else:
                    config['ldap']['default_realm'] = config['ldap']['basedn']

                return config
        except FileNotFoundError as e:
            continue

    raise FileNotFoundError("Unable to load the OLAK config from any of these paths: %s" % (', '.join(config_paths)))

def load_config():
    """
    Search for the configuration file, load it and populate any unset items with
    default values.
    """
    try:
        return _cached_config
    except UnboundLocalError as e:
        _cached_config = _load_config()

    return _cached_config