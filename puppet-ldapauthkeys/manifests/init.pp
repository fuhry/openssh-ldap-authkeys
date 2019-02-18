class ldapauthkeys (
  Ldapauthkeys::Authmap     $authmap,
  Ldapauthkeys::Olakconfig  $config,
  Boolean                   $manage_package        = true,
  String                    $package_name          = $::ldapauthkeys::params::package_name,
  Boolean                   $manage_sshd_config    = true,
  String                    $sshd_config_path      = $::ldapauthkeys::params::sshd_config_path,
  Boolean                   $manage_sshd_service   = true,
  Optional[String]          $sshd_service_provider = undef,
  String                    $sshd_service_state    = 'running',
  Boolean                   $sshd_service_enable   = true,
  String                    $sshd_service_name     = $::ldapauthkeys::params::sshd_service_name,
) inherits ldapauthkeys::params {
  $conffile_header = "# This file is managed by Puppet. Changes will be lost on the next agent run!"
  $err_os_unsupported = "Your OS family ${::os['family']} isn't supported. You can specify \$package_name and \$sshd_service_name manually to work around this."

  $sshd_notify = $manage_sshd_service ? {
    true => [Service['olak_sshd']],
    default => [Service['olak_sshd']],
  }

  if ($manage_package) {
    if ($package_name =~ Undef) {
      fail($err_os_unsupported)
    }

    package { $package_name:
      ensure => installed,
      before => [
        Group['olak'],
        User['olak'],
      ],
    }
  }

  group { 'olak':
    ensure => present,
    system => true,
  }
  -> user { 'olak':
    ensure => present,
    gid    => 'olak',
    system => true,
    home   => '/dev/null',
    shell  => '/bin/false',
    before => File['/etc/openssh-ldap-authkeys'],
  }

  file { '/etc/openssh-ldap-authkeys':
    ensure => directory,
    owner  => 'root',
    group  => 'root',
    mode   => '0755',
  }

  -> file {
    default:
      ensure  => file,
      owner   => 'root',
      group   => 'olak',
      mode    => '0640',
      notify  => $sshd_notify;
    '/etc/openssh-ldap-authkeys/olak.yml':
      content => sprintf("%s\n\n%s", $conffile_header, to_yaml($config));
    '/etc/openssh-ldap-authkeys/authmap':
    content => template("${module_name}/authmap.erb");
  }

  if ($manage_sshd_config) {
    file_line {
      default:
        ensure => present,
        path   => $sshd_config_path,
        after  => '^#? *Port',
        notify => $sshd_notify;
      'olak: sshd_config: AuthorizedKeysCommand':
        match => '^#? *AuthorizedKeysCommand(\s+.*)?$',
        line  => "AuthorizedKeysCommand /usr/bin/openssh-ldap-authkeys %u %t %k";
      'olak: sshd_config: AuthorizedKeysCommandUser':
        match => '^#? *AuthorizedKeysCommandUser(\s+.*)?$',
        line  => "AuthorizedKeysCommandUser olak";
      'olak: sshd_config: PermitUserEnvironment':
        match => '^#? *PermitUserEnvironment(\s+.*)?$',
        line  => "PermitUserEnvironment yes";
    }
  }

  if ($manage_sshd_service) {
    if ($sshd_service_name =~ Undef) {
      fail($err_os_unsupported)
    }
    service { 'olak_sshd':
      ensure   => $sshd_service_state,
      name     => $sshd_service_name,
      enable   => $sshd_service_enable,
      provider => $sshd_service_provider,
    }
  }
}