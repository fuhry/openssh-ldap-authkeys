# Enable Python dependency generation for Fedora and EL8+
%{?python_enable_dependency_generator}

%if %{_vendor} == "debbuild"
	%global _buildshell /bin/bash
	%global devsuffix dev
%else
	%global devsuffix devel
%endif

Name:		openssh-ldap-authkeys
Version:	0.1.0
Release:	1%{?dist}
Summary:	Python script to generate SSH authorized_keys files using an LDAP directory

%if %{_vendor} == "debbuild"
Packager:	Dan Fuhry <dan@fuhry.com>
Group:		admin
%endif

License:	MIT
URL:		https://github.com/fuhry/%{name}
Source0:	%{url}/archive/%{version}/%{name}-%{version}.tar.gz

BuildArch:	noarch

%if 0%{?fedora} >= 30 || 0%{?rhel} >= 9 || 0%{?suse_version}
BuildRequires:	systemd-rpm-macros
%else
BuildRequires:	systemd
%endif
%{?systemd_requires}

BuildRequires:	python%{python3_pkgversion}-%{devsuffix}
BuildRequires:	python%{python3_pkgversion}-setuptools

%if %{_vendor} == "debbuild"
BuildRequires:	python3-deb-macros
BuildRequires:	systemd-deb-macros
# Compatibility with dsc packaging?
Provides:	python%{python3_pkgversion}-%{name} = %{version}-%{release}

# Requirements for py3compile / py3clean scripts
Requires(preun): python%{python3_pkgversion}-minimal
Requires(post):	python%{python3_pkgversion}-minimal
Requires(pre):	passwd
%else
Requires(pre):	%{_sbindir}/groupadd
Requires(pre):	%{_sbindir}/useradd
%endif

# This is only for cases that we don't have a dependency generator active...
%if (0%{?rhel} && 0%{?rhel} < 8) || 0%{?suse_version} || 0%{?debian} || 0%{?ubuntu}
Requires:	python%{python3_pkgversion}-ldap

# Names are fun...
%if %{_vendor} == "redhat"
Requires:	python%{python3_pkgversion}-dns
%else
Requires:	python%{python3_pkgversion}-dnspython
%endif

%if %{_vendor} == "suse"
Requires:	python%{python3_pkgversion}-PyYAML
%else
Requires:	python%{python3_pkgversion}-yaml
%endif

%endif


%description
openssh-ldap-authkeys is an implementation of AuthorizedKeysCommand for
OpenSSH 6.9 and newer that allows SSH public keys to be retrieved from
an LDAP source. It's provided for situations where a solution other
than 1:1 mapping is needed for users.

With SSH keys stored centrally in LDAP, revocation of a compromised
key is a quick and painless exercise for the user or IT department.

openssh-ldap-authkeys allows shared accounts to be fully auditable as
to who used them.


%prep
%autosetup -p1


%build
%py3_build


%install
%py3_install


%files
%if %{_vendor} == "debbuild"
%license debian/copyright
%endif
%license COPYING
%doc README.md
%{python3_sitelib}/ldapauthkeys/
%{python3_sitelib}/openssh_ldap_authkeys*egg-info
%{_bindir}/openssh-ldap-authkeys
%dir %{_sysconfdir}/%{name}
%config(noreplace) %{_sysconfdir}/%{name}/olak.yml.example
%config(noreplace) %{_sysconfdir}/%{name}/authmap.example
%{_sysusersdir}/openssh-ldap-authkeys.sysusers.conf
%{_tmpfilesdir}/openssh-ldap-authkeys.tmpfiles.conf

%pre
getent group olak >/dev/null || groupadd -r olak
getent passwd olak >/dev/null || \
    useradd -r -g olak -d /dev/null -s /bin/false \
    -c "System account for %{name} to run as" olak
exit 0


%if %{_vendor} == "debbuild"
%post
%{sysusers_create %{name}.sysusers.conf}
%{tmpfiles_create %{name}.tmpfiles.conf}
%{py3_bytecompile_post %{name}}

%preun
%{py3_bytecompile_preun %{name}}
%endif


%changelog
* Fri Feb 22 2019 Neal Gompa <ngompa13@gmail.com> - 0.1.0
- Initial release
