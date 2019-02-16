# openssh-ldap-authkeys

`openssh-ldap-authkeys` is an implementation of `AuthorizedKeysCommand` for OpenSSH 6.9 and newer that allows SSH public
keys to be retrieved from an LDAP source. It's provided for situations where a more robust solution than 1:1 mapping is
needed for users. For example, a large corporation with a significant deployment of Linux servers might use
`openssh-ldap-authkeys` to allow specific users or groups to log into the `root` account safely and securely. With SSH
keys stored centrally in LDAP, revocation of a compromised key is a quick and painless exercise for the user or IT
department. `openssh-ldap-authkeys` allows shared accounts to be fully auditable as to who used them.

## History

This program is a clean-room implementation of a tool I developed internally at a former place of employment. It retains
backwards compatibility with the configuration files used by that internal tool, but is unencumbered by any copyrights
other than my own.

# Compatibility

This program is compatible with OpenSSH 6.2 and up, and works best on OpenSSH 6.9 and later which support the
substitutions `%u`, `%t` and `%k` in an `AuthorizedKeysCommand`.

# Dependencies

`openssh-ldap-authkeys` depends on Python 3 and the following Python libraries:

* [dnspython](http://www.dnspython.org/)
* [python-ldap](https://www.python-ldap.org/)
* [PyYAML](https://pyyaml.org/wiki/PyYAML)

Dependency installation one-liners for popular distros:

* Arch Linux (pacman): `pacman -S python-dns python-ldap python-yaml`
* Debian/Ubuntu (apt): `apt-get install -y python3-dns python3-ldap python3-yaml`

# Installation

Run `python3 setup.py build`, then as root/sudo `python3 setup.py install`.

# Configuration

1. Create a user for `openssh-ldap-authkeys`: `useradd -s /bin/false -d /dev/null -r olak`
1. Rename the files in `/etc/openssh-ldap-authkeys`, removing the `.example` suffix. Make these files owned by
   `root:olak`, group-readable and with no world permissions (mode `0640`).
1. Edit these files to your needs. See the sections for [`olak.yml`](#olakyml) and [`authmap`](#authmap) below.
1. To get caching working, copy the file `openssh-ldap-authkeys.tmpfiles` into `/usr/lib/tmpfiles.d`, then run (as root)
   `/usr/bin/systemd-tmpfiles --create`. This will create the directory `/var/run/ldap/ssh-cache`, owned by user `olak`
   and group `olak` with mode `0700`. If you aren't using `systemd-tmpfiles` or a similar temporary file manager, you'll
   need to write a script for your init system to create this directory on system startup.
1. Test OLAK by invoking it as `sshd` would: `sudo -u olak /usr/bin/openssh-ldap-authkeys <user>` (where `<user>` is a
   local user account that will be accessible through OLAK)
1. Add the following lines to `/etc/ssh/sshd_config`:

```
PermitUserEnvironment yes
AuthorizedKeysCommand /usr/bin/openssh-ldap-authkeys %u %t %k
AuthorizedKeysCommandUser olak
```

# Configuration files reference

## `olak.yml`

`olak.yml` is the main configuration file for `openssh-ldap-authkeys`. It tells `openssh-ldap-authkeys` how to connect
and bind to the LDAP server, describes the LDAP schema in use in your current environment, configures caching, logging,
and output. The following keys are supported:

### `ldap.basedn` _(string)_

*Required.*

Base distinguished name of your LDAP tree.

_Default: none_

### `ldap.default_realm` _(string)_

Default realm (domain) name for LDAP users. Defaults to the domain specified by `ldap.basedn`. This should be written
all-uppercase, a convention that was chosen to allow it to resemble Kerberos principals.

_Default: generated from your basedn_

### `ldap.use_dns_srv` _(boolean)_

Whether to attempt to discover the LDAP server using DNS SRV records. If this is set to `true`, a domain name will be
generated using the domain components of `ldap.basedn` and converted to a DNS domain name. From there,
`openssh-ldap-authkeys` will attempt to discover the LDAP server first using the service name `_ldaps._tcp` (for LDAP
with TLS) and then `_ldap._tcp` (for unsecured LDAP).

An example of LDAP SRV records would be:

```zone_file
_ldaps._tcp.example.com.    IN   SRV   ldap.example.com. 636 0 0
_ldap._tcp.example.com.     IN   SRV   ldap.example.com. 389 0 0
```

If LDAP server discovery fails, `ldap.server_uri` will be used instead. However, if discovery succeeds but the script is
unable to connect to any discovered server, it will _not_ fall back to `ldap.server_uri`.

_Default: false_

### `ldap.server_uri` _(string)_

*Required* if `ldap.use_dns_srv` is `false`.

URI to the LDAP server in the format of `protocol://host:port`. Supported protocols include anything supported by the
OpenLDAP C library, including `ldap://`, `ldaps://` and `ldapi://`.

The default TCP ports are 389 for unsecured traffic and 636 for TLS-encrypted LDAP traffic.

_Default: none_

### `ldap.authdn` _(string)_

Distinguished name to use for a simple bind. If omitted, the script will use anonymous bind.

_Default: none_

### `ldap.authpw` _(string)_

Password to be used when performing a simple bind. If omitted, the script will use anonymous bind.

_Default: none_

### `ldap.timeout` _(integer)_

Timeout for establishing of the LDAP connection.

If this timeout is exceeded and there is a stale cache file, the cache file will be used.

_Default: 15_

### `ldap.filters.user` _(string)_

LDAP filter string to use for identifying users.

_Default:_ `(objectClass=posixAccount)`

### `ldap.filters.group` _(string)_

LDAP filter string to use for identifying groups.

_Default:_ `(objectClass=posixGroup)`

### `ldap.group_membership` _(string)_

Indicates the format of group membership entries. Valid values are:

* `uid`: Groups specify the member's username (e.g. `memberUid: john`). Common in POSIX environments.
* `dn`: Groups specify the member's DN (e.g. `member: cn=John Doe,ou=People,o=ACME Corp,dc=acme,dc=com`). Common in
  Windows/AD environments.

_Default:_ `uid`

### `ldap.attributes.username` _(string)_

LDAP attribute used for usernames.

In POSIX environments this is typically `uid`, and in Windows environments this is typically `sAMAccountName`.

_Default:_ `uid`

### `ldap.attributes.ssh_key` _(string)_

LDAP attribute used for SSH keys.

There is no standardized LDAP attribute for storing SSH keys. One common implementation by
[Jakub Jirutka](https://github.com/jirutka) uses the attribute
[`sshPublicKey`](https://github.com/jirutka/ssh-ldap-pubkey/blob/master/etc/openssh-lpk.schema).
[JumpCloud](https://jumpcloud.com/), a Directory-as-a-Service vendor, uses `sshKey`.

_Default:_ `sshPublicKey`

### `ldap.attribtues.group_name` _(string)_

LDAP attribute for group names. Most schemas use common name (`cn`).

_Default:_ `cn`

### `ldap.attributes.group_member` _(string)_

LDAP attribute for group members. Typically `memberUid` in POSIX environments and `member` in Active Directory.

_Default:_ `memberUid`

### `cache.lifetime` _(integer)_

Number of seconds for which a local cache file is valid. During this window, the local cache of SSH keys will be used
without the script attempting to reach back out to the LDAP server. This should typically be a shorter window if you
wish for key revocation to be effective in emergencies.

Keep in mind that if the LDAP server is unreachable and there is a previous local cache, that cache file will be used
even if it's expired. This measure is in place to protect your ability to log into servers in the event that LDAP is
down.

_Default: 900 seconds (15 minutes)_

### `cache.dir` _(string)_

Directory where SSH keys will be cached. Must be writable only by the user running OLAK (set by the
`AuthorizedKeysCommandUser` directive in `sshd_config`).

_Default:_ `/var/run/ldap/ssh-cache`

### `cache.allow_stale_cache_on_failure` _(boolean)_

Allow a stale cache file to be used if any exception occurs when trying to get authorized keys from LDAP. This does pose
a small security risk, but is recommended to be left on in the event that your LDAP server is unreachable.

_Default: true_

### `output.username_env_var` _(string)_

Environment variable that will be populated with the user's LDAP username. If they are coming from a realm other than
the default, `@REALM` will be appended.

_Default:_ `OLAK_USER`

### `logging.to_stderr` _(boolean)_

Set to `true` to write `openssh-ldap-authkeys` log messages to standard error in addition to syslog.

## `authmap`

The `authmap` file is a text file mapping local user accounts and groups to LDAP entities.

The basic format of `authmap` is as follows:

```
local_user:ldapuser1,ldapuser2,ldapuser3
```

The following conventions are observed:

* Prefixing a name with an ampersand (`&`) causes it to be treated as a group. This means you can authorize everyone in
  a certain LDAP group to log into a single local, shared account.
* `@all` is a special keyword that translates to any local user account. Use it in the left-hand column to allow an
  LDAP entity to log in as ANY local user.
* `~self` is a special keyword that translates to the name of the local user being logged into. Use it in the right-hand
  column to allow a user whose LDAP username matches the local username to log into that local account.
* An LDAP username may be suffixed with `@REALM` to search an alternate base DN.

### `authmap` common usage examples

#### Allow users in the LDAP group `admin` to log into a system as `root`

```
root:&admin
```

#### Allow users in the local group `shellusers` to log into their own account

You would use this in combination with an NSS extension like `sssd` to populate a local group for users with shell
access.

```
&shellusers:~self
```

#### Allow everyone to log into their own local account

This could also be called "SSSD emulation mode."

```
@all:~self
```

# Troubleshooting

`openssh-ldap-authkeys` logs output to syslog with the facility `LOG_AUTH` and prefixes all messages with the string
`openssh-ldap-authkeys.`. Enabling the `logging.to_stderr` option documented above can help isolate problems.

# License

This program is provided under the MIT license.

Copyright (c) 2019 Dan Fuhry

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# Author/Contact

Written by [Dan Fuhry](mailto:dan@fuhry.com)