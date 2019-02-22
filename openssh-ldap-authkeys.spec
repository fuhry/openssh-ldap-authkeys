# Enable Python dependency generation for Fedora and EL8+
%{?python_enable_dependency_generator}

# Begin Python macros
%{!?__python3: %global __python3 /usr/bin/python3}
%{!?python3_pkgversion: %global python3_pkgversion 3}
%if %{_vendor} == "debbuild"
	%global pyinstflags --no-compile -O0
	%global pytargetflags --install-layout=deb
%else
	%global pyinstflags -O1
	%global pytargetflags %{nil}
%endif

%{!?py3_build: %global py3_build CFLAGS="%{optflags}" %{__python3} setup.py build}
%{!?py3_install: %global py3_install %{__python3} setup.py install %{?pyinstflags} --skip-build --root %{buildroot} %{?pytargetflags}}

%if %{undefined python3_sitelib}
%global python3_sitelib %(%{__python3} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")
%endif

# End Python macros

%if %{_vendor} == "debbuild"
	%global _buildshell /bin/bash
	%global devsuffix dev
	%global _tmpfilesdir /usr/lib/tmpfiles.d
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

BuildRequires:	systemd
%{?systemd_requires}

BuildRequires:	python%{python3_pkgversion}-%{devsuffix}
BuildRequires:	python%{python3_pkgversion}-setuptools

%if %{_vendor} == "debbuild"
# Compatibility with dsc packaging?
Provides:	python%{python3_pkgversion}-%{name} = %{version}-%{release}

# Requirements for py3compile / py3clean scripts
Requires(preun): python%{python3_pkgversion}-minimal
Requires(post):	python%{python3_pkgversion}-minimal
Requires(pre):	passwd
%else
Requires(pre):	shadow-utils
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
%{_tmpfilesdir}/openssh-ldap-authkeys.tmpfiles.conf

%pre
getent group olak >/dev/null || groupadd -r olak
getent passwd olak >/dev/null || \
    useradd -r -g olak -d /dev/null -s /bin/false \
    -c "System account for %{name} to run as" olak
exit 0


%if %{_vendor} == "debbuild"
%post
# Generate tmpfiles
systemd-tmpfiles --create openssh-ldap-authkeys.tmpfiles.conf >/dev/null 2>&1 || :
# Do late-stage bytecompilation, per debian policy
py3compile -p %{name} -V -4.0

%preun
# Ensure all __pycache__ files are deleted, per debian policy
py3clean -p %{name}
%endif


%changelog
* Fri Feb 22 2019 Neal Gompa <ngompa13@gmail.com> - 0.1.0
- Initial release
