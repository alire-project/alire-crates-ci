#!/usr/bin/env bash

# Script is run after a commit to this repo
# It checks out latest alr and tests all crates

trap 'echo "ERROR at line ${LINENO} (code: $?)" >&2' ERR 
trap 'echo "Interrupted" >&2 ; exit 1' INT 

set -o errexit
set -o nounset

# Get alire
git clone --recurse-submodules https://github.com/alire-project/alire
pushd alire
git checkout $BRANCH
commit=`git log --pretty=oneline -1 | cut -c1-8`
gprbuild -j0 -p -P alr_env
export PATH+=:`pwd`/bin
popd

testdir=alrtest

# Ensure native package index is up to date
apt-get update

# Check crates
mkdir $testdir
pushd $testdir
alr test --newest --full
cp *.xml ../shippable/testresults 
popd

# Generate .md result file
dst=status-`basename $IMAGE_TAG`

if [ "`find $testdir -name '*.md' | wc -l`" -gt 0 ]; then
    echo "Storing crate test results for image tagged as $dst"
    cp -fv $testdir/*.md $dst.md
else
    echo "alr test failed to run in $dst" > $dst.md
fi

# Push results
git pull
git add $dst.md
git commit -m "alire@$commit [skip ci]" 
git push git@github.com:alire-project/alire-crates-ci.git
