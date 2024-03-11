from asyncio import subprocess
import os
import yaml

from alr import db
from subprocess import check_output, run
from sys import stderr


def commit():
    if "CI" not in os.environ.keys():
        print("Not on GHA, not committing")
        return

    check_output(["git", "config", "--global", "user.name", "GHA"])
    check_output(["git", "config", "--global", "user.email", "actions@github.com"])

    run(["git", "fetch", "--all"])

    branch = os.environ["BRANCH_NAME"]

    if run(["git", "checkout", f"origin/{branch}", "-B", branch]).returncode != 0:
        print("WARNING: checkout failed", file=stderr)
        run(["git", "merge", "--abort"])
        run(["git", "reset", "--hard"])
        run(["git", "clean", "-f"])
    else:
        check_output(["git", "add", "troubles-*"])

        prev_log = check_output(["git", "log", "-1", "--oneline"]).decode()
        squash = True if "Auto:" in prev_log else False
        commit_args = [
            "git", "commit", "-m",
            f"Auto: report on {db.distro_full()}"
            f"{' (S)' if squash else ''}"
            ]

        if squash:
            commit_args += ["--amend"]

        out = run(commit_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print("commit output:")
        print(out.stdout.decode())
        if out.returncode == 0:
            if run(["git", "push", "-f"]).returncode != 0:
                print("WARNING: force push failed", file=stderr)
            else:
                print("COMMIT successful", file=stderr)
        else:
            print("COMMIT failed")


def main():
    crates = db.load(populate_if_empty=False, all_versions=True, online=False)
    if not crates:
        print("WARNING: no crates to check")
        return

    troubles = []
    for release in crates:
        if not release.ok():
            troubles += [release.as_dict()]

    print(f"::set-output name=platform::{db.osname().lower()}-{db.distro_full()}")
    print(f"DONE with {len(troubles)} problems found")

    with open(f"troubles-{db.osname()}-{db.distro_full().lower().replace('.', '_')}.yaml", "wt") as file:
        # We prefer _ to . because jekyll removes dots in filenames
        yaml.dump(troubles, file)

    db.backoff()
    commit()

main()