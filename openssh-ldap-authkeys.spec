# Enable Python dependency generation for Fedora and EL8+
%{?python_enable_dependency_generator}

%if "%{_vendor}" == "redhat"
%define _enableselinux 1
%endif

Name:		openssh-ldap-authkeys
Version:	0.2.0
Release:	2%{?dist}
Summary:	Python script to generate SSH authorized_keys files using an LDAP directory

%if "%{_vendor}" == "debbuild"
Packager:	Dan Fuhry <dan@fuhry.com>
Group:		admin
%endif

License:	MIT
URL:		https://github.com/fuhry/%{name}
Source0:	%{url}/archive/%{version}/%{name}-%{version}.tar.gz

BuildArch:	noarch


%if "%{_vendor}" == "debbuild"
BuildRequires:	python%{python3_pkgversion}-dev
BuildRequires:	python3-deb-macros
BuildRequires:	systemd-deb-macros
# Compatibility with dsc packaging?
Provides:	python%{python3_pkgversion}-%{name} = %{version}-%{release}
%{?py3_bytecompile_requires}
%else
BuildRequires:	python%{python3_pkgversion}-devel
BuildRequires:	systemd-rpm-macros
%endif
%{?systemd_requires}

BuildRequires:	python%{python3_pkgversion}-setuptools

# This is only for cases that we don't have a dependency generator active...
%if %{undefined python_enable_dependency_generator} && %{undefined python_disable_dependency_generator}
Requires:	python%{python3_pkgversion}-ldap

# Names are fun...
%if "%{_vendor}" == "redhat"
Requires:	python%{python3_pkgversion}-dns
%else
Requires:	python%{python3_pkgversion}-dnspython
%endif

%if "%{_vendor}" == "suse"
Requires:	python%{python3_pkgversion}-PyYAML
%else
Requires:	python%{python3_pkgversion}-yaml
%endif

%endif

# SELinux stuff!
%if "%{_enableselinux}" == "1"
%define relabel_files() \
restorecon -R /usr/bin/openssh-ldap-authkeys \
    /etc/openssh-ldap-authkeys; \

%define selinux_policyver 37.19-1

BuildRequires: selinux-policy-devel >= %{selinux_policyver}
Requires: policycoreutils, libselinux-utils
Requires(post): selinux-policy-base >= %{selinux_policyver}, policycoreutils
Requires(postun): policycoreutils
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
%if "%{_enableselinux}" == "1"
pushd selinux
make -f /usr/share/selinux/devel/Makefile olak.pp
popd
%endif


%install
%py3_install

%if "%{_enableselinux}" == "1"
install -d %{buildroot}%{_datadir}/selinux/packages
install -d %{buildroot}%{_datadir}/selinux/devel/include/contrib
install -d %{buildroot}%{_mandir}/man8/
install -d %{buildroot}/etc/selinux/targeted/contexts/users/

install -m 644 %{_builddir}/%{name}-%{version}/selinux/olak.pp %{buildroot}%{_datadir}/selinux/packages
install -m 644 %{_builddir}/%{name}-%{version}/selinux/olak.if  %{buildroot}%{_datadir}/selinux/devel/include/contrib/
install -m 644 %{_builddir}/%{name}-%{version}/selinux/olak_selinux.8 %{buildroot}%{_mandir}/man8/
%endif


%files
%if "%{_vendor}" == "debbuild"
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
%if "%{_enableselinux}" == "1"
%attr(0600,root,root) %{_datadir}/selinux/packages/olak.pp
%{_datadir}/selinux/devel/include/contrib/olak.if
%{_mandir}/man8/olak_selinux.8.*
%endif

%post
%if 0%{?el7}
%sysusers_create %{name}.sysusers.conf
%tmpfiles_create %{name}.tmpfiles.conf
%endif

%if "%{_vendor}" == "debbuild"
%sysusers_create %{name}.sysusers.conf
%tmpfiles_create %{name}.tmpfiles.conf
%py3_bytecompile_post %{name}
%endif

%if "%{_enableselinux}" == "1"
semodule -n -i %{_datadir}/selinux/packages/olak.pp
if /usr/sbin/selinuxenabled ; then
    /usr/sbin/load_policy
    %relabel_files

fi;
%endif

%if "%{_vendor}" == "debbuild"
%preun
%py3_bytecompile_preun %{name}
%endif

%if "%{_enableselinux}" == "1"
%postun
if [ $1 -eq 0 ]; then
	semodule -n -r olak
	if /usr/sbin/selinuxenabled ; then
		/usr/sbin/load_policy
		%relabel_files
	fi;
fi;
%endif
exit 0


%changelog
* Fri Nov 11 2022 Dan Fuhry <dan@fuhry.com> - 0.2.0
- New release

* Fri Feb 22 2019 Neal Gompa <ngompa13@gmail.com> - 0.1.0
- Initial release
