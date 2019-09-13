# Maintainer: Dan Fuhry <dan@fuhry.com>
pkgname=openssh-ldap-authkeys
pkgver=0.0.0
pkgrel=1
pkgdesc="Python script to generate SSH authorized_keys files using an LDAP directory"
arch=('any')
url="https://github.com/fuhry/openssh-ldap-authkeys"
license=('MIT')
groups=()
depends=(python3 python-dnspython python-ldap python-yaml)
makedepends=('python3' 'git') # 'bzr', 'git', 'mercurial' or 'subversion'
provides=()
conflicts=()
replaces=()
backup=()
options=()
install=
source=("olak::git+file://$PWD#branch=master")
noextract=()
md5sums=('SKIP')

# Please refer to the 'USING VCS SOURCES' section of the PKGBUILD man page for
# a description of each element in the source array.

pkgver() {
	cd "$srcdir/olak"

	printf "r%s.%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short HEAD)"
}

prepare() {
	:
}

build() {
	cd "$srcdir/olak"
	python3 setup.py build
}

check() {
	:
}

package() {
	cd "$srcdir/olak"
	python3 setup.py install --root "${pkgdir}"
}
