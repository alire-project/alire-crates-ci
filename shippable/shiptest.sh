#!/usr/bin/env bash

trap 'echo "ERROR at line ${LINENO} (code: $?)" >&2' ERR 
trap 'echo "Interrupted" >&2 ; exit 1' INT 

set -o errexit
set -o nounset

# Get alire
git clone --recurse-submodules https://github.com/alire-project/alire
pushd alire
gprbuild -j0 -p -P alr_env
export PATH+=:`pwd`/bin
popd

testdir=alrtest

# Check crates
mkdir $testdir
pushd $testdir
alr test --latest hello
cp *.xml ../shippable/testresults 
popd

# Generate MD result file
dst=`basename $IMAGE_TAG`
if [ "`find $testdir -name '*.md' | wc -l`" -gt 0 ]; then
    echo "Storing crate test results for image tagged as $dst"
    cp -fv $testdir/*.md $dst.md
else
    echo "alr test failed to run in $dst" > $dst.md
fi

git commit -a -m "alr test results for $dst [skip ci]"
git push
