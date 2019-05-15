#!/usr/bin/env bash

trap 'echo "ERROR at line ${LINENO} (code: $?)" >&2' ERR 
trap 'echo "Interrupted" >&2 ; exit 1' INT 

set -o errexit
set -o nounset

# Check compilation in all cases
gprbuild -j0 -p -P alr_env

export PATH+=:`pwd`/bin

# Check crates
mkdir $cratedir
pushd $cratedir
alr test --latest hello
cp *.xml ../shippable/testresults 
popd
#!/usr/bin/env bash

source scripts/shipcommon

dst=`basename $IMAGE_TAG`
if [ "`find $cratedir -name '*.md' | wc -l`" -gt 0 ]; then
    echo "Storing crate test results for image tagged as $dst"
    cp -fv $cratedir/*.md status/$dst.md
else
    echo "alr test failed to run in $dst" > status/$dst.md
fi

git checkout -B crates-ci
git add status
git commit -m "alr test results for $dst [skip ci]"
git push -f git@github.com:alire-project/alr.git
