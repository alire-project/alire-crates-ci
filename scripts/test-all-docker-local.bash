#!/usr/bin/env bash

# Intended to locally jumpstart tests by testing crates
# in docker tags. Requires the relevant scripts to be in path.
# To be run at the folder below which each tag is created.

trap 'echo "ERROR in $0 at line ${LINENO} (code: $?)" >&2' ERR 
trap 'echo "Interrupted" >&2 ; exit 1' INT 

set -o errexit
set -o nounset

tags=("debian-stable" "ubuntu-lts" "community-latest" "centos-latest-community-latest")

# Iterate over regular crates x tags

crates=$(alr search -n -q --list | tail +2 | awk '{print $1}' | xargs)

for tag in ${tags[@]}; do
    echo Testing in docker image alire/gnat:${tag}
    test-crates-docker.bash ${tag} ${crates}
done

popd