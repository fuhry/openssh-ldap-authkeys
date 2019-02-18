class ldapauthkeys::params (
) {
  $package_name = $::os['family'] ? {
    'Debian'    => 'python3-openssh-ldap-authkeys',
    'Archlinux' => 'openssh-ldap-authkeys',
    default     => undef,
  }

  $sshd_config_path = '/etc/ssh/sshd_config'

  $sshd_service_name = $::os['family'] ? {
    'Debian'    => 'sshd',
    'Archlinux' => 'ssh',
    default     => undef,
  }
}