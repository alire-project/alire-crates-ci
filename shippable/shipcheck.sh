#!/usr/bin/env bash

trap 'echo "ERROR at line ${LINENO} (code: $?)" >&2' ERR 
trap 'echo "Interrupted" >&2 ; exit 1' INT 

set -o errexit
set -o nounset

# This script is triggered after a commit/PR to alire or alire-index
# It checks that the trigger is not a PR but a real commit
# This can probably be done through shippable resources,
#   although I'm unsure if the added complexity is worth it.

# Get alire
git clone https://github.com/alire-project/alire
pushd alire
git checkout $BRANCH
commit=`git log --pretty=oneline -1 | cut -c1-8`
popd

# Check changed commit
touch shippable/$BRANCH.txt
oldcommit=`cat shippable/$BRANCH.txt`

if [ "$commit" == "$oldcommit" ]; then
    echo Commit unchanged, stopping now.
    exit 0
else
    echo "Testing crates because of alire@$BRANCH changes:"
    echo "Old commit: $oldcommit"
    echo "New commit: $commit"
fi

# Force testing by committing to ourselves
# We do this instead of running shiptest.sh because this way unit tests are managed by shippable automatically
git config --global user.email "shippable@alire-crates-ci"
git config --global user.name "Shippable"
git pull
date -u > last-commit
git add last-commit
git commit -m "alire@$BRANCH triggered"
git push git@github.com:alire-project/alire-crates-ci.git
