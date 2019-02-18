type Ldapauthkeys::Cacheconfig = Struct[{
  lifetime => Optional[Integer],
  dir => Optional[String],
  allow_stale_cache_on_failure => Optional[Boolean],
}]