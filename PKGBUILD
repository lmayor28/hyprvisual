# Maintainer: lmayor28 <lmayormoreno@gmail.com>
pkgname=hyprvisual-git
pkgver=r1.0
pkgrel=1
pkgdesc="TUI monitor layout controller for Hyprland"
arch=('any')
url="https://github.com/lmayor28/hyprvisual"
license=('MIT')
depends=('python>=3.12' 'python-textual' 'hyprland')
makedepends=('git' 'python-build' 'python-installer' 'python-hatchling')
provides=('hyprvisual')
conflicts=('hyprvisual')
source=("$pkgname::git+https://github.com/lmayor28/hyprvisual.git")
sha256sums=('SKIP')

pkgver() {
    cd "$srcdir/$pkgname"
    printf "r%s.%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short HEAD)"
}

build() {
    cd "$srcdir/$pkgname"
    python -m build --wheel --no-isolation
}

package() {
    cd "$srcdir/$pkgname"
    python -m installer --destdir="$pkgdir" dist/*.whl
    install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
    install -Dm644 hyprvisual.desktop "$pkgdir/usr/share/applications/hyprvisual.desktop"
}
