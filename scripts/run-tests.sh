#!/bin/bash -x

set -o errexit

[ "$DISTRO" != "windows-latest" ] && sudo=sudo

# Un-alias sudo if already running as root, to avoid issues with environments without sudo:
[ "$(id -u)" -eq 0 ] && sudo=""

case $DISTRO in
    arch-rolling)
        $sudo pacman -Sy
        ;;
    debian-stable | ubuntu-lts | ubuntu-latest)
        $sudo apt-get update
        ;;
    fedora-latest)
        $sudo yum makecache
        ;;
    *)
        echo WARNING: unsupported distro $DISTRO, not updating package metadata
        # For windows-latest, we would need to know the location of pacman.
        # This is buried somewhere in the alr installation.
        # Maybe with alr exec -- pacman it will work.
        ;;
esac

# Some distros don't allow touching the system python libraries, so create a
# virtualenv for our test environment.
if [ "$DISTRO" != "windows-latest" ]; then
    python3 -m venv venv
    source venv/bin/activate
fi
pip3 install -r requirements.txt

# Disable check for ownership that sometimes confuses docker-run git
# Also, Github is not vulnerable to iCVE-2022-24765/CVE-2022-24767, see
# https://github.blog/2022-04-12-git-security-vulnerability-announced/
git config --global --add safe.directory '*'

# Check if gprbuild has GLIBC dependency issues. We need to do it in a temporary crate

alr -n -f init --bin tempcrate
pushd tempcrate

if alr exec -- gprbuild --version 2>&1 | grep 'not found' | grep version | grep -q GLIBC; then
    echo "gprbuild dependencies not found for the testing configuration."
    echo "SKIPPING TEST BECAUSE OF gprbuild GLIBC DEPENDENCIES"
    exit 0
else
    echo gprbuild ldd dependencies OK
    popd
    rm -rf tempcrate
fi

python3 -u -X utf8 test_release.py
# -u: unbuffered output, simplifies GHA log interpretation on error