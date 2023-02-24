class ldapauthkeys::params (
) {
  $package_name = $::os['family'] ? {
    'RedHat'    => 'openssh-ldap-authkeys',
    'Suse'      => 'openssh-ldap-authkeys',
    'Mandrake'  => 'openssh-ldap-authkeys',
    'Debian'    => 'python3-openssh-ldap-authkeys',
    'Archlinux' => 'openssh-ldap-authkeys',
    default     => undef,
  }

  $selinux_package_name = "${package_name}-selinux"

  $sshd_config_path = '/etc/ssh/sshd_config'

  $sshd_service_name = $::os['family'] ? {
    'RedHat'    => 'sshd',
    'Suse'      => 'sshd',
    'Mandrake'  => 'sshd',
    'Debian'    => 'sshd',
    'Archlinux' => 'ssh',
    default     => undef,
  }
}
