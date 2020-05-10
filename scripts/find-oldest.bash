#!/usr/bin/env bash

# Look for any untested crate or, if none found, the oldest among the
# tested ones. The idea is to trigger this workflow often to ensure
# eventually all crates are tested. Ideally, once this is complete, 
# we can test a crate on demand after a PR is merged into alire-index.

# The output of this script is a crate name to stdout

trap 'echo "ERROR in $0 at line ${LINENO} (code: $?)" >&2' ERR 
trap 'echo "Interrupted" >&2 ; exit 1' INT 

set -o errexit
set -o nounset

# Check all regular crates against folders below us. If no folder is named
# as the crate, it means it must be tested. This is somewhat flaky since any
# test on any platform will skip the crate as completely tested in all platforms.

crates=$(alr search -n -q --list | tail +2 | awk '{print $1}' | xargs)

for crate in $crates; do
    find . -name ${crate} -type d | grep -q ${crate} || { echo ${crate}; exit 0; }
done

# If no crate has been identified yet, list all files underneath,
# sorted by reverse date, and identify the crate for first one.
# We need to use git to list, the filesystem dates are those of checkout.

git ls-files | grep log | xargs -n1 -I{} git log -1 --format="%at {}" | \
  sort -n | head -1 | cut -f3 -d/ && exit 0

exit 1 # something failed