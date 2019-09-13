import yaml
import os
from time import time
from ldapauthkeys.logging import get_logger

def cache_valid_for_user(user, lifetime, dir):
    """
    Check if the cache file is valid for a given username.
    """
    cache_file = os.path.join(dir, user)

    try:
        cache_stat = os.stat(cache_file)
        now = int(time())

        if cache_stat.st_mtime + lifetime >= now:
            with open(cache_file, 'r') as f:
                return True
    except Exception as e:
        pass

    return False

def load_cache(user, config):
    """
    Return the parsed cache file contents for the given user.
    """
    cache_file = os.path.join(config['cache']['dir'], user)

    with open(cache_file, 'r') as fp:
        get_logger('cache').info("Loading authkeys for user \"%s\" from cachefile: %s" % (user, cache_file))
        return yaml.load(fp, Loader=yaml.loader.SafeLoader)

def write_cache_file(user, authkeys, config):
    """
    Write authkeys for a user to the cache file.
    """
    cache_file = os.path.join(config['cache']['dir'], user)

    with open(cache_file, 'w') as fp:
        yaml.dump(authkeys, fp)
        fp.flush()