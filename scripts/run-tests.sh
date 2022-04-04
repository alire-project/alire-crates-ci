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

$sudo pip3 install -r requirements.txt

python3 -X utf8 test_release.py