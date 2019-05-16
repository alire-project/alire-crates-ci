#!/usr/bin/env bash

trap 'echo "ERROR at line ${LINENO} (code: $?)" >&2' ERR 
trap 'echo "Interrupted" >&2 ; exit 1' INT 

set -o errexit
set -o nounset

# This script is triggered after a commit to alire or alire-index
# Checks in shippable.yml should ensure that it only runs after
#   a real commit (not PR) to master or stable

# Force testing by committing to ourselves
# We do this instead of running shiptest.sh because this way unit tests are managed by shippable automatically
git config --global user.email "shippable@alire-crates-ci"
git config --global user.name "Shippable"
git pull
date -u > shippable/last-run
git add shippable/last-run
git commit -m "alire@$BRANCH triggered"
git push git@github.com:alire-project/alire-crates-ci.git
