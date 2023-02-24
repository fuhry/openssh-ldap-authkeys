# puppet-ldapauthkeys

This is a Puppet module that sets up `openssh-ldap-authkeys` on a system.

## Parameters

### `$authmap` _(hash)_

*Required.*

Specifies a map of local users to LDAP users. Hash keys are the local user/group and members are LDAP entities.

Example:

```yaml
root:
  - "&admins"
  - jimmy
"&shell-users":
  - "~self"
```

### `$config` _(hash)_

*Required.*

Configuration for OLAK. If your ENC allows parameters to be specified as YAML (i.e. Foreman), you should be able to copy
and paste a working `olak.yml` into this field.

Configuration format is formally defined in the following files:

* `types/olakconfig.pp`
* `types/ldapconfig.pp`
* `types/cacheconfig.pp`
* `types/outputconfig.pp`
* `types/loggingconfig.pp`

A minimal configuration is:

```yaml
ldap:
  basedn: dc=example,dc=com
  server_uri: ldap://ldap.example.com
  authdn: "cn=example-user, ou=Roles, dc=example, dc=com"
  authpw: supersecret123
  filters:
    user: "(objectClass=organizationalPerson)"
    group: "(objectClass=groupOfNames)"
  group_membership: dn
  attributes:
    username: uid
    ssh_key: sshKey
    group_name: cn
    group_member: member
```

### `$manage_package` _(boolean)_

If `true`, the module will attempt to install the `openssh-ldap-authkeys` package.

_Default:_ `true`

### `$package_name` _(string)_

Name of the package to install using your distribution's package manager.

_Default: autodetected based on distribution_

### `$selinux_package_name` _(string)_

Name of the separate package containing the SELinux policy, which will be installed if your system has SELinux enabled.

_Default: `${package_name}-selinux`_

### `$package_ensure` _(string)_

Version of the package to force to. Defaults to `installed`, which merely ensures the package is installed, and does not
attempt to upgrade it if it's out of date. Set to `latest` to always upgrade the package (if an update is available) on
any Puppet run.

_Default: `installed`_

### `$manage_sshd_config` _(boolean)_

If `true`, sets all required configuration options in `sshd_config`. While this is designed to not clobber any existing
sshd configuration you have, if you're using a module that fully manages the sshd configuration like
[saz-ssh](https://forge.puppet.com/saz/ssh), it's recommended to set this parameter to `false` and instead configure the
following options through that module:

* `AuthorizedKeysCommand /usr/bin/openssh-ldap-suthkeys %u %t %k`
* `AuthorizedKeysCommandUser olak`
* `PermitUserEnvironment yes`

_Default:_ `true`

### `$sshd_config_path` _(string)_

Path to the `sshd_config` file.

_Default:_ `/etc/ssh/sshd_config`

### `$manage_sshd_service` _(boolean)_

If `true` will manage the SSH service, which allows the module to automatically restart `sshd` if changes are made to
the configuration. You will probably need to set this to `false` if there's anything else within your site that is
managing the sshd configuration.

_Default:_ `true`

### `$sshd_service_provider` _(string/undef)_

Service provider for the sshd service. If omitted, uses the system's preferred service manager as determined by Puppet's
built-in `service` resource.

_Default:_ `undef`

### `$sshd_service_state` _(string)_

State to enforce for the `sshd` service. Defaults to `running`

_Default:_ `running`

### `$sshd_service_enable` _(boolean)_

If `true`, enables the `sshd` service on system start.

_Default:_ `true`

### `$sshd_service_name` _(string)_

Name of the sshd service.

_Default: autodetected based on distribution_
