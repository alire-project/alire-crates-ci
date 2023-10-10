#!/bin/bash -x

set -o errexit

[ "$DISTRO" != "windows-latest" ] && sudo=sudo

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

python3 -X utf8 test_release.py