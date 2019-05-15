![branch-master](https://badgen.net/badge/branch/master/lightgrey)[![Run Status](https://api.shippable.com/projects/5cdbf0c29bbe6e00074ac61b/badge?branch=master)](https://app.shippable.com/github/alire-project/alire-crates-ci/dashboard) ![branch-master](https://badgen.net/badge/branch/stable/lightgrey)[![Run Status](https://api.shippable.com/projects/5cdbf0c29bbe6e00074ac61b/badge?branch=stable)](https://app.shippable.com/github/alire-project/alire-crates-ci/dashboard)


# CRATE BUILD TESTS

These files reflect the build results of releases during the continuous integration check.

Branches master/stable reflect the results after a commit to the respective branches in https://github.com/alire-project/alire (once tests have completed)

NOTE: only latest versions are tested.

The name of each file reflects that of the docker image used to test `alr`, from https://cloud.docker.com/u/alire/repository/docker/alire/gnat

At the top of each file are the details of the platform as detected by `alr`.

The possible status for each milestone is:

- ![green](https://placehold.it/8/00aa00/000000?text=+) PASS: the release was built normally.
- ![yellow](https://placehold.it/8/ffbb00/000000?text=+) UNAV/DEPS: the release is either disabled or some of its dependencies are missing in that platform.
- ![red](https://placehold.it/8/ff0000/000000?text=+) FAIL/ERR: the release failed to build or `alr` suffered an unexpected error while attempting the test. This should not happen in stable `alr` builds and will be looked at ASAP.
