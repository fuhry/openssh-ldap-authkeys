type Ldapauthkeys::Authuser = Variant[
  Pattern[/^&?[A-Za-z0-9_ -]+(@[A-Z0-9-]+(\.[A-Z0-9-]+)*)?$/],
  Enum['~self'],
]