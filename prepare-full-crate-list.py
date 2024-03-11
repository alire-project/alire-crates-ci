#  Script to gather all crate test info into a single collection more easily processed from jekyll

import math
import os
import yaml

from alr import db
from hashlib import sha1


def color(success : int, missing : int, fail : int, total : int):
    if total == 0:
        return "yellow"
    elif success + missing == total and success > 0:
        return "green"
    elif fail == 0:
        return "yellow"
    elif success == 0:
        return "red"
    else:
        return "orange"


tests = db.load(populate_if_empty=False, all_platforms=True, online=False)

# Compute some extra info and remove logs, which cause the file to exceed the GH 100 MB limit
for test in tests:
    test.duration_log = math.log10(1.0 + test.duration)
    test.log = None  # Logs are taken from their individual files, no need in this collection

if not os.path.isdir("_badges"):
    os.mkdir("_badges")
if not os.path.isdir("_data"):
    os.mkdir("_data")

with open(os.path.join("_data", "tests.yaml"), "wt") as file:
    yaml.dump(tests, file)

crates = set()
distros = set()
badges = {}
# crate -> { success: int, total: int}

# Extract crate names, distro names, and aggregate counts per crate
for test in tests:
    crates.add(test.crate)
    distros.add(test.distro)
    count = badges.get(test.crate, { "total" : 0, "success" : 0, "fail" : 0, "missing" : 0 })
    if test.status in [db.BUILD_SUCCESS, db.BUILD_FAIL, db.BUILD_DEPS]:
        count["total"] += 1
        count["success"] += 1 if test.status == db.BUILD_SUCCESS else 0
        count["missing"] += 1 if test.status == db.BUILD_DEPS else 0
        count["fail"] += 1 if test.status == db.BUILD_FAIL else 0
    badges[test.crate] = count

with open(os.path.join("_data", "crate_names.yaml"), "wt") as file:
    yaml.dump(list(crates), file)
with open(os.path.join("_data", "distros.yaml"), "wt") as file:
    yaml.dump(list(distros), file)

# Prepare a collection in which each crate has a page and summary badge
if not os.path.isdir("_crates"):
    os.mkdir("_crates")
for crate in crates:
    # Crate page
    with open(os.path.join("_crates", f"{crate}.html"), "wt") as file:
        file.write("---\n")
        file.write(f"crate: {crate}\n")
        file.write(f"title: {crate}\n")
        file.write(f"layout: page\n")
        file.write("---\n")
        file.write("{% include crate_body.html %}\n")

    # Crate badge
    with open(os.path.join("_badges", f"{crate}.json"), "wt") as file:
        success=badges[crate].get("success", 0)
        missing=badges[crate].get("missing", 0)
        fail=badges[crate].get("fail", 0)
        total=badges[crate].get("total", 0)
        file.write(f"""---
layout: badge
crate: {crate}
total: {total}
success: {success}
fail: {fail}
missing: {missing}
color: {color(success=success, missing=missing, fail=fail, total=total)}
---
        """)
