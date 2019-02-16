import sys

def print_authkey(key_type, key_value, dn, config, file=sys.stdout):
    return 'ENVIRONMENT="%s=%s" %s %s' % (
        config['output']['username_env_var'],
        dn,
        key_type, key_value
        )

def render_authkeys(authkeys, config, key_type=None, key_value=None):
    """
    Render a hash of authorized keys that came either from a YAML cache file or
    fetch_ldap_authkeys(). Returns a string.
    """
    
    output = []
    ssh_key_attr = config['ldap']['attributes']['ssh_key']
    
    for username in authkeys.keys():
        user_entry = authkeys[username]
        
        for k in user_entry[ssh_key_attr]:
            kt, kv = k.split(' ')
            if (key_type is None or key_type == kt) and (key_value is None or key_value == kv):
                output.append(print_authkey(kt, kv, username, config))
    
    return '\n'.join(output)
