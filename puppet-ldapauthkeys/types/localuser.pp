type Ldapauthkeys::Localuser = Variant[
  Pattern[/^&?[a-z0-9_-]+$/],
  Enum['@all'],
]