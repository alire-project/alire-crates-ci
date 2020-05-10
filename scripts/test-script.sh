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
commit=`git log --pretty=oneline -1 | cut -c1-8`
[[ "$OSTYPE" =~ darwin.* ]] && export OS=macOS
gprbuild -j0 -p -P alr_env
export PATH+=:`pwd`/bin
popd

testdir=alrtest

# Check crates
mkdir $testdir
pushd $testdir
alr -n test --newest --full || true
# alr will exit with error if some crate didn't test out properly
popd

# Generate .md result file
dst=status-$SETUP_NAME

if [ "`find $testdir -name '*.md' | wc -l`" -gt 0 ]; then
    echo "Storing crate test results for image tagged as $dst"
    cp -fv $testdir/*.md $dst.md
else
    echo "alr test failed to run in $dst" > $dst.md
fi

# SYNC BARRIER To avoid conflicts when pushing results, we allow each setup to
# only do so at a specific minute. The root of this problem is at GH not
# allowing using "needs:" on matrix jobs.

# Array vars fail on MacOS bash version. Resort to a more verbose case
case $SETUP_NAME in
    centos-latest-community-latest) ending=0 ;;
    community-latest)               ending=1 ;;
    debian-stable)                  ending=2 ;;
    ubuntu-lts)                     ending=3 ;;
    windows-latest)                 ending=4 ;;
    macos-latest)                   ending=5 ;;
esac

while ! [[ "$(date +%M)" =~ .$ending ]]; do
    echo Waiting for slot $ending at $(date)
    sleep 30s
done

echo Barrier left behind at $(date)

# push to publishing branch
remote_repo="https://${GITHUB_ACTOR}:${GITHUB_TOKEN}@github.com/${GITHUB_REPOSITORY}.git"
remote_branch="master"
git config user.name "${GITHUB_ACTOR}"
git config user.email "${GITHUB_ACTOR}@users.noreply.github.com"
git remote rm origin || true
git remote add origin "${remote_repo}"
git add $dst.md
git commit -m "Automated deployment: $(date -u) ${GITHUB_SHA}"
git checkout -b to_publish
git pull --rebase origin ${remote_branch}
git push origin "to_publish:${remote_branch}"
