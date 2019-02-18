type Ldapauthkeys::Authmap = Hash[
  Ldapauthkeys::Localuser,
  Array[Ldapauthkeys::Authuser]
]