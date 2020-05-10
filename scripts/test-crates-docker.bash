#!/usr/bin/env bash

# Tests the crates given in $2... in the docker tag given as alire/gnat:$1
# Expected to be run at the parent of the folder with the docker tag name that will be created, e.g.:
# ./${PWD}/ubuntu-lts/
# Requires test-crate.bash and alr to be in path

trap 'echo "ERROR at line ${LINENO} (code: $?)" >&2' ERR 
trap 'echo "Interrupted" >&2 ; exit 1' INT 

set -o errexit
set -o nounset

[ "$1" != "" ] && tag=$1 || { echo Missing docker tag; exit 1; }
shift

# Create/enter appropriate folder

mkdir -p $tag
pushd $tag

# Retrieve docker tag and test crate

image=alire/gnat:${tag}
docker pull ${image}

# Test crates

for crate in "$@"; do
    echo Testing crate $crate...
    
    docker run -v$(which alr):/usr/bin/alr \
            -v$(which test-crate.bash):/usr/bin/test-crate.bash \
            -v${PWD}:/work \
            -w /work \
            ${image} test-crate.bash ${crate}
done

popd