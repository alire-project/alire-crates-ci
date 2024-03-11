# CRATE BUILD TESTS

Website: https://alire-project.github.io/alire-crates-ci/

Cron jobs in this repository test crates continuously on different platforms
and with different compiler versions. The objective is to have early warning of
failing releases in new configurations after the checks they undergo during
submission to the community index.

The files under `status/` reflect the individual build result of crates for the
different platforms.

Collected releases that have some issue, per platform, are found in the
`troubles-<platform>.yaml` files, updated hourly.
