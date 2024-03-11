#!/bin/bash -x
# Script to be run before invoking jekyll

set -o errexit

# Clone the results branch
rm -rf /tmp/results
git clone https://github.com/alire-project/alire-crates-ci --depth=1 --single-branch --branch results /tmp/results
rm -rf status
cp -r /tmp/results/status status
echo '*' > status/.gitignore

# Generate website
rm -rf _data/{crate_names,distros,tests}.yaml
python3 prepare-full-crate-list.py

[ "$CI" != "" ] || { echo Not in GHA, exiting; exit 0; }

###########################################################

rm -f {_badges,_crates,_data,status}/.gitignore

# deploy script based on https://github.com/peaceiris/actions-gh-pages

remote_repo="https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_REPOSITORY}.git"
remote_branch="gh-pages"
local_dir="${HOME}/000"
PUBLISH_DIR="."

git clone --depth=1 --single-branch --branch "${remote_branch}" "${remote_repo}" "${local_dir}"
cd "${local_dir}"
git rm -r '*'
find "${GITHUB_WORKSPACE}/${PUBLISH_DIR}" -maxdepth 1 | \
        tail -n +2 | \
        xargs -I % cp -rf % "${local_dir}/"

# push to publishing branch
git config user.name "${GITHUB_ACTOR}"
git config user.email "${GITHUB_ACTOR}@users.noreply.github.com"
git remote rm origin || true
git remote add origin "${remote_repo}"
git add --all
git commit --allow-empty --amend -m "Auto: website updated $(date -u) ${GITHUB_SHA}"
git checkout -b to_publish
git push -f origin "to_publish:${remote_branch}"
