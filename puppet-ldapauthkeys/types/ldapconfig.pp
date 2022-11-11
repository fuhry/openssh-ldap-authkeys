type Ldapauthkeys::Ldapconfig = Struct[{
	basedn => String,
	use_dns_srv => Boolean,
	srv_discovery_domain => Optional[String],
	server_uri => Optional[String],
	default_realm => Optional[String],
	authdn => Optional[String],
	authpw => Optional[String],
	sasl_method => Optional[Enum['EXTERNAL']],
	timeout => Optional[Integer],
	filters => Struct[{
		user => String,
		group => String,
	}],
	group_membership => Enum['dn', 'uid'],
	attributes => Struct[{
		username => String,
		ssh_key => String,
		group_name => String,
		group_member => String,
		user_disabled => Optional[Struct[{
			attribute => String,
			op => Enum['eq', '=', '==', 'ne', 'neq', '!=', 'bitmask', 'and', '&'],
			value => Variant[String, Integer],
		}]],
	}],
}]