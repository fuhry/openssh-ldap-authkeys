type Ldapauthkeys::Olakconfig = Struct[{
  ldap => Ldapauthkeys::Ldapconfig,
  tls => Optional[Ldapauthkeys::Tlsconfig],
  cache => Optional[Ldapauthkeys::Cacheconfig],
  output => Optional[Ldapauthkeys::Outputconfig],
  logging => Optional[Ldapauthkeys::Loggingconfig],
}]