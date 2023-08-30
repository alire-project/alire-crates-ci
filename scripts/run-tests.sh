#!/bin/bash -x

set -o errexit

[ "$DISTRO" != "windows-latest" ] && sudo=sudo

case $DISTRO in
    arch-rolling)
        $sudo pacman -Sy
        $sudo pip3 install -r requirements.txt
        ;;
    debian-stable)
        $sudo apt-get update
        $sudo apt-get install $(awk '{print "python-" $0}' requirements.txt)
        ;;
    ubuntu-lts | ubuntu-latest)
        $sudo apt-get update
        $sudo pip3 install -r requirements.txt
        ;;
    fedora-latest)
        $sudo yum makecache
        $sudo pip3 install -r requirements.txt
        ;;
    *)
        echo WARNING: unsupported distro $DISTRO, not updating package metadata
        # For windows-latest, we would need to know the location of pacman.
        # This is buried somewhere in the alr installation.
        # Maybe with alr exec -- pacman it will work.
        ;;
esac

# Disable check for ownership that sometimes confuses docker-run git
# Also, Github is not vulnerable to iCVE-2022-24765/CVE-2022-24767, see
# https://github.blog/2022-04-12-git-security-vulnerability-announced/
git config --global --add safe.directory '*'

python3 -X utf8 test_release.py
