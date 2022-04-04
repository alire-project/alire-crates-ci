# TODO:
# Test external crates?
# Detect gnat in deps? being not the one in env?
# Fix `alr test` for binary crates
# Test all version, lowering prio of old versions?

import distro
import os
import platform
import random
import subprocess
import sys
import time
import uuid

from alr import db
from alr.db import gnat_version

from datetime import datetime, timezone
from glob import glob
from subprocess import check_output, run
from typing import *

BRANCH="results"
MIN_RUN_TIME = 20*60  # Seconds running tests until finishing
# MIN_RUN_TIME = 0*60  # Seconds running tests until finishing

tested_count : int = 0

def pick(crates : Iterable[db.Test]):
    # Check if there is crate override (for local testing)
    if "CRATE" in os.environ.keys():
        crate_override = os.environ["CRATE"]
        for crate in crates:
            if crate.crate == crate_override:
                return crate
        print(f"WARNING: overridding crate {crate_override} not found, falling back to random pick")

    # Find total urgency weight:
    urgency = 0
    for crate in crates:
        urgency += crate.urgency()

    # Pick a winner
    random.seed()
    target = random.randint(1, urgency)
    print(f"TESTING {target} out of {urgency}")

    pos = 0
    for crate in crates:
        pos += crate.urgency()
        if target <= pos:
            return crate

    print("WARNING: reached end of crates but not target")
    return crates[-1]


def test_one(crate):
    # crate : Test
    milestone = f"{crate.crate}={crate.version}"
    print(f"TEST {milestone} (nudged by {round(crate.nudge(), 2)}) (gnat={gnat_version(crate=crate.crate)})")

    if not os.path.isdir("test"):
        os.mkdir("test")

    os.chdir("test")

    # Test in a pristine folder
    global tested_count
    folder = uuid.uuid4()
    os.mkdir(f"{folder}")
    os.chdir(f"{folder}")
    tested_count += 1

    try:
        start = time.monotonic()
        solution = check_output(["alr", "--non-interactive", "--no-tty", "show", "--solve", milestone]).decode()
        run(["alr", "--non-interactive", "--no-tty", "test", "--redo", f"{crate.crate}={crate.version}"])
        duration = time.monotonic() - start

        logs = glob(os.path.join(f"{crate.crate}_{crate.version}_*", "alire", "alr_test_*.log"))
        if len(logs) == 1:
            with open(logs[0], "rt") as log:
                log = log.readlines()
                print(f"LOG contains {len(log)} lines")
        else:
            log = ["Failed to locate log\n"]

        log = ["SOLUTION:\n"] + [f"{line}\n" if not line.endswith('\n') else line for line in solution.split("\n")] + ["\nLOG:\n"] + log

        # Use the text log output to ascertain crate status
        outcomes = glob(f"alr_test_*txt")
        if len(outcomes) == 1:
            with open(outcomes[0], "rt") as outcome:
                lines = outcome.readlines()
                status = lines[1].split(":")[0].strip()
                # one of ERR FAIL pass SKIP UNAV DEPS
        else:
            status = "MISS"

        log = [f"Test ran at {datetime.now(timezone.utc)}\n\n"] + log

        crate.set_result(status=db.BUILD_STATUS[status], log=log, duration=duration)

        if status == "FAIL" or status == "ERR" or status == "MISS":
            print("".join(crate.log))

        print(f"DONE: {crate.status} ({status})")
        print(f"ELAPSED {round(crate.duration, 2)} seconds")
    finally:
        os.chdir("..")
        os.chdir("..")

    crate.write()
    print(f"::set-output name=crate::{crate.crate}")
    print(f"::set-output name=version::{crate.version}")
    print(f"::set-output name=status::{status}")
    print(f"::set-output name=gnat_version::{gnat_version()}")


def commit(crate : db.Test):
    if "CI" not in os.environ.keys():
        print("Not on GHA, not committing")
        return

    def git_check(args):
        print(f"RUN check: {args}")
        print(check_output(args).decode())

    def git_run(args):
        print(f"RUN nochk: {args}")
        out = run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(out.stdout.decode())
        return out

    if os.path.isdir("alire_install"):
        with open(os.path.join("alire_install", ".gitignore"), "wt") as file:
            file.write("*\n")

    print("--------------- GIT RUN START ----------------")

    if os.path.isfile(os.path.join("status", ".gitignore")):
        os.remove(os.path.join("status", ".gitignore"))

    db.backoff(10)

    git_check(["git", "config", "--global", "user.name", "GHA"])
    git_check(["git", "config", "--global", "user.email", "actions@github.com"])

    git_check(["git", "status"])
    git_check(["git", "stash", "--include-untracked"])
    git_check(["git", "fetch", "--all"])
    git_check(["git", "reset", "--hard", f"origin/{BRANCH}"])

    if git_run(["git", "stash", "pop"]).returncode != 0:
        print("WARNING: pop failed")
        git_run(["git", "merge", "--abort"])
        git_run(["git", "rebase", "--abort"])
        git_run(["git", "reset", "--hard", f"origin/{BRANCH}"])
        git_run(["git", "clean", "-f"])
        git_run(["git", "stash", "drop"])
    else:
        git_check(["git", "add", "status", "heads"])
        git_check(["git", "status"])

        prev_log = check_output(["git", "log", "-1", "--oneline"]).decode()
        squash = True if "Auto:" in prev_log else False
        commit_args = [
            "git", "commit", "-m",
            f"Auto: test {crate.crate}={crate.version} ({crate.status}) "
            f"({crate.platform.lower()}/{crate.distro.lower()}/gnat={crate.gnat})"
            f"{ '(S)' if squash else ''}"
            ]

        if squash:
            commit_args += ["--amend"]
        out = git_run(commit_args)
        if out.returncode != 0:
            print("WARNING: git commit failed: " + out.stdout.decode())

        if git_run(["git", "push", "-f"]).returncode != 0:
            print("WARNING: force push failed")
        else:
            print("COMMIT+PUSH successful")

    print("--------------- GIT RUN END ----------------")


def main():
    print(f"START {db.osname()}--{db.distro_full()}--gnat={gnat_version()}")

    # Switch to testing branch so previous test info can be reused
    print(check_output(["git", "fetch", "origin", f"{BRANCH}"]).decode())
    print(check_output(["git", "checkout", f"{BRANCH}"]).decode())

    # Load will fallback to repopulation if there are new commits in the index
    crates = db.load()

    start = time.monotonic()
    while True:
        print(f"ROUND START after {time.monotonic() - start} seconds")
        crate = pick(crates)
        test_one(crate)
        commit(crate)
        if time.monotonic() - start > MIN_RUN_TIME:
            break


main()
print("DONE")