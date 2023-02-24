# Enable Python dependency generation for Fedora and EL8+
%{?python_enable_dependency_generator}

%if "%{_vendor}" != "debbuild"
%global with_selinux 1
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

%if 0%{?with_selinux}

%if 0%{?rhel} && 0%{?rhel} < 8
Requires:	%{name}-selinux = %{version}-%{release}
%else
Requires:	(%{name}-selinux = %{version}-%{release} if selinux-policy)
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

%if 0%{?el7}
%post
%sysusers_create %{name}.sysusers.conf
%tmpfiles_create %{name}.tmpfiles.conf
%endif

%if "%{_vendor}" == "debbuild"
%post
%sysusers_create %{name}.sysusers.conf
%tmpfiles_create %{name}.tmpfiles.conf
%py3_bytecompile_post %{name}

%preun
%py3_bytecompile_preun %{name}
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


%if 0%{?with_selinux}
# -------------------------------------------------------------------

%package selinux
Summary:	SELinux module for %{name}
BuildRequires:	selinux-policy
BuildRequires:	selinux-policy-devel
BuildRequires:	make
%{?selinux_requires}

%description selinux
This package provides the SELinux policy module to ensure
%{name} runs properly under an environment with
SELinux enabled.

%pre selinux
%selinux_relabel_pre

%post selinux
%selinux_modules_install %{_datadir}/selinux/packages/olak.pp.bz2

%posttrans selinux
if [ $1 -eq 1 ] && /usr/sbin/selinuxenabled ; then
	fixfiles -FR %{name} restore || :
fi

%postun selinux
%selinux_modules_uninstall olak
if [ $1 -eq 0 ]; then
	%selinux_relabel_post
fi

%files selinux
%license COPYING
%attr(0600,-,-) %{_datadir}/selinux/packages/olak.pp.bz2
%{_datadir}/selinux/devel/include/contrib/olak.if
%{_mandir}/man8/olak_selinux.8*

# -------------------------------------------------------------------
%endif


%prep
%autosetup -p1


%build
%py3_build

%if 0%{?with_selinux}
pushd selinux
make SHARE="%{_datadir}" TARGETS="olak"
popd
%endif


%install
%py3_install

%if 0%{?with_selinux}
install -d %{buildroot}%{_datadir}/selinux/packages
install -d %{buildroot}%{_datadir}/selinux/devel/include/contrib
install -d %{buildroot}%{_mandir}/man8/

install -m 644 selinux/olak.pp.bz2 %{buildroot}%{_datadir}/selinux/packages
install -m 644 selinux/olak.if  %{buildroot}%{_datadir}/selinux/devel/include/contrib/
install -m 644 selinux/olak_selinux.8 %{buildroot}%{_mandir}/man8/
%endif


%changelog
* Fri Nov 11 2022 Dan Fuhry <dan@fuhry.com> - 0.2.0
- New release

* Fri Feb 22 2019 Neal Gompa <ngompa13@gmail.com> - 0.1.0
- Initial release
