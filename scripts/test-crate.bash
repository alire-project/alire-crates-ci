#!/usr/bin/env bash

# This script tests the latest release of a single crate. It expects to be run
# at the root of the folder for a particular OS results
# $1 is the crate to test, without version.

[ "$1" != "" ] && crate=$1 || { echo Missing crate; exit 1; }

trap 'echo "ERROR in $0 at line ${LINENO} (code: $?)" >&2' ERR 
trap 'echo "Interrupted" >&2 ; exit 1' INT 

set -o errexit
set -o nounset

# Identify last version

echo Target crate: ${crate}

[[ "$(alr show $crate | head -1)" =~ .*=(.*): ]]
version=${BASH_REMATCH[1]}
[ "$version" == "" ] && { echo Missing version; exit 1; }

# Enter appropriate folder

mkdir -p ${crate}/${version}
pushd ${crate}/${version}

# Clear any previous results
rm -f *.{log,xml,md,txt}

# Test crate and retrieve its log, clearing checkout afterwards

alr -n test --newest --redo $crate || true
find . -name 'alr_test*.log' -exec mv '{}' . \;
rm -rf ${crate}_${version}_*

popd