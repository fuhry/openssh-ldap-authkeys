type Ldapauthkeys::Tlsconfig = Struct[{
    require => Optional[Enum['prohibit', 'noverify', 'allow', 'require']],
    ca_file => Optional[String],
    ca_dir => Optional[String],
    client_credentials => Optional[Struct[{
        certificate => String,
        private_key => String,
    }]],
}]
