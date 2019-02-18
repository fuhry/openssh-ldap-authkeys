import re
import pwd
import grp
import ldap.asyncsearch
import ldap.filter
import ldap.dn
from ldapauthkeys.util import *
from ldapauthkeys.logging import get_logger
from ldapauthkeys.config import array_merge_unique

# List of paths where we'll search for an authmap
authmap_paths = [
    './authmap',
    '/etc/openssh-ldap-authkeys/authmap',
]

class AuthorizedEntity:
    """
    Represents a single LDAP entity (user or group) authorized to login to a
    local account.
    """
    entity = None
    realm = None

    def __init__(self, entity, realm):
        self.entity = entity
        self.realm = realm

    def to_ldap_user_list(self, connection, config):
        """
        Turn this authorized entity into a user, or list of users, permitted to
        login to LDAP. Must return a list of (user, realm) tuples. Example
        return value:

          [("jdoe", "EXAMPLE.COM",),]

        Arguments:

          - LDAP connection handle
          - Configuration YAML hash
        """
        return []

class AuthorizedGroup(AuthorizedEntity):
    """
    Represents an LDAP group.
    """
    def to_ldap_user_list(self, connection, config):
        # Initialize the result
        users = []

        # Attempt to obtain a record of this group from LDAP. Perform a search
        # matching on the configured group filter, group name attribute and name
        # of the group.
        search = ldap.asyncsearch.List(connection)
        search_filter = ldap.filter.filter_format(
            "(&%s%s)" % (config['ldap']['filters']['group'], "(%s=%s)"),
            [config['ldap']['attributes']['group_name'], self.entity]
        )

        get_logger('authmap').info(
            'Attempting to find group "%s" in basedn "%s"' % (
                self.entity,
                self.realm
            )
        )

        try:
            # Search the basedn for the group. Retrieve only the group
            # membership attribute - we don't care about the rest.
            search.startSearch(self.realm, ldap.SCOPE_SUBTREE, search_filter,
                [config['ldap']['attributes']['group_member']])
        except Exception as e:
            # On any exception, return an empty array.
            get_logger('ldap').error(
                'Failed to search for group "%s" in basedn "%s": %s: %s' % (
                    self.entity,
                    self.realm,
                    e.__class__.__name__,
                    repr(e.args)
                )
            )
            return []

        search.processResults()

        for rcode, result in search.allResults:
            # For each result, we have the DN of the group, and attributes.
            group_dn, attrs = result

            get_logger('authmap').info(
                'Located group "%s" at DN "%s"' % (
                    self.entity,
                    group_dn
                )
            )

            # Iterate through group members.
            for user in attrs[config['ldap']['attributes']['group_member']]:
                if config['ldap']['group_membership'] == 'uid':
                    # "user" contains just a username (i.e. "jdoe"). We'll
                    # search the user tree for this username, relying on the
                    # config to tell us which attribute the username must match.
                    users.append([user.decode('utf-8'), self.realm])
                elif config['ldap']['group_membership'] == 'dn':
                    # FIXME: this LDAP server uses DNs to identify members of
                    # groups, but if the RDN attribute isn't the same as the
                    # configured username attribute, we would need to go get the
                    # user by DN and then search and retrieve their entry a
                    # second time to get their SSH keys. This isn't suppported
                    # at the moment. Throw a nice warning and skip this user.
                    user_dn = ldap.dn.str2dn(user.decode('utf-8'))
                    attr, value = user_dn[0][0][0:2]

                    if attr != config['ldap']['attributes']['username']:
                        get_logger('authmap').error(
                            ('At present, group membership lookups rely on the username attribute ' +
                             'being the RDN attribute for users. The group "%s" references the DN "%s", ' +
                             'which we can\'t look up as part of a search because the UID attribute ' +
                             'is not "%s" but rather "%s". This user won\'t be authorized.') % (
                                group_dn, user.decode('utf-8'), attr, config['ldap']['attributes']['username']
                            )
                        )

                    get_logger('authmap').info(
                        'Found user "%s" in group "%s"' % (
                            value,
                            self.entity
                        )
                    )

                    users.append([value, self.realm])
                else:
                    raise ValueError('Unsupported group membership strategy "%s". Supported strategies are "uid" and "dn".' % (
                        config['ldap']['group_membership']
                    ))

        return users

class AuthorizedUser(AuthorizedEntity):
    """
    Represents a single authorized user.
    """
    def to_ldap_user_list(self, ldap, config):
        """
        1:1 map of a username to an LDAP entry
        """
        return [(self.entity, self.realm,)]

class AuthorizedEntityCollection:
    """
    Collection of AuthorizedEntity objects.
    """
    entries = []

    def append(self, entity):
        for e in self.entries:
            if e.entity == entity.entity and e.realm == entity.realm and isinstance(e, entity.__class__):
                return

        self.entries.append(entity)

    def length(self):
        """
        Get the length of the collection.
        """
        return len(self.entries)

    def to_ldap_search(self, ldap, config):
        """
        Generate a list of LDAP entries to search for. The return value of this
        method is to be provided to fetch_ldap_authkeys() (ldap.py) for
        execution of the search.

        Returns a dict composed in the following manner:
          - The keys are the realm name, which is used to set the basedn of the
            search.
          - The values are lists of usernames. (This is the stage at which
            groups are flattened to lists of users.)
        """
        searches = {}
        for entry in self.entries:
            users = entry.to_ldap_user_list(ldap, config)
            for uid, realm in users:
                if not realm in searches.keys():
                    searches[realm] = []

                if not uid in searches[realm]:
                    searches[realm].append(uid)

        return searches

def parse_authmap(fp):
    """
    Low level parser for authmap files. Takes a file pointer to an open authmap
    file and parses it into a dict.

    The returned dict will be composed as follows:
      - The keys are the names of local entities (users or groups)
      - The values are lists of authorized LDAP entities, represented as
        strings.
    """
    authmap = {}

    while True:
        line = line = fp.readline()
        if line == '':
            break

        line = line.strip()

        if line == '' or line[0] == '#' or line.rstrip() == '':
            continue

        localuser, entities = line.split(':')

        if not localuser in authmap:
            authmap[localuser] = []

        for entity in entities.split(','):
            authmap[localuser].append(entity.strip())

    return authmap

def get_authmap():
    """
    Load and parse the authmap file.

    Returns a dict in the format documented by parse_authmap().
    """
    for path in authmap_paths:
        try:
            with open(path) as fp:
                authmap = parse_authmap(fp)
                get_logger('authmap').info("Loaded auth from %s" % (path))
                return authmap
        except Exception as e:
            raise e

    raise FileNotFoundError("Unable to load the OLAK authorized entity file from any of these paths: %s" % (', '.join(authmap_paths)))

def lookup_authmap(authmap, user, config):
    """
    Take an authmap and return the list of LDAP entities authorized to log in as
    the given user.

    Input:
      - The return value of parse_authmap()
      - The local username being logged into
      - The OLAK config dict (load_config() in config.py)

    Output:
      - An AuthorizedEntityCollection representing all of the LDAP entities
        that are allowed to log in as that local user
    """

    entities = []

    for key in authmap.keys():
        entry = authmap[key]

        if key[0] == '&':
            # Local group
            try:
                group = grp.getgrnam(key[1:])
                if user in group.gr_mem:
                    entities.append(entry)


            except KeyError as e:
                get_logger('authmap').warn('Local group "%s" does not exist' % (key[1:]))
        elif key == '@all' or key == user:
            for e in entry:
                entities.append(entry)

    entities_stripped = AuthorizedEntityCollection()

    for entry in entities:
        for e in entry:
            try:
                domain_user, realm = e.split('@')
                realm = domain_to_basedn(realm.lower())
            except ValueError:
                domain_user = e
                realm = config['ldap']['default_realm']

            if domain_user == '~self':
                domain_user = user

            if domain_user[0] == '&':
                entities_stripped.append(AuthorizedGroup(domain_user[1:], realm))
            else:
                entities_stripped.append(AuthorizedUser(domain_user, realm))

    return entities_stripped