type Ldapauthkeys::Olakconfig = Struct[{
  ldap => Ldapauthkeys::Ldapconfig,
  cache => Optional[Ldapauthkeys::Cacheconfig],
  output => Optional[Ldapauthkeys::Outputconfig],
  logging => Optional[Ldapauthkeys::Loggingconfig],
}]