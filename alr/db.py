from asyncore import write
from tabnanny import check
import distro
import glob
import os
import platform
import random
import re
import time
import yaml

from datetime import datetime, timezone
from os.path import join
from subprocess import check_output, run
from typing import *

DEBUG_MAX_CRATES = 999999  # Let's hope ha!
# DEBUG_MAX_CRATES = 10

PRUNE_AFTER_SECONDS = 7*24*60*60  # One week

DB = "status"
BUILD_UNTESTED = "untested"
BUILD_SUCCESS = "success"
BUILD_FAIL = "failing"
BUILD_DEPS = "missing-dependencies"

# Map from `alr test` codes to our more legible codes
BUILD_STATUS = {
    "pass" : BUILD_SUCCESS,
    "ERR"  : "alr-error",
    "FAIL" : BUILD_FAIL,
    "SKIP" : "skipped",
    "UNAV" : "unavailable",
    "DEPS" : BUILD_DEPS,
    "MISS" : "internal-ci-error" # Failed to match the alire exit status
    }


def backoff(max : int=20) -> None:
    """
    Random delay
    """
    seconds = random.uniform(0.0, max)
    print(f"SLEEPING for {round(seconds, 2)} seconds...")
    time.sleep(seconds)


def osname() -> str:
    if platform.system() == "Darwin":
        return "macos"
    else:
        return platform.system().lower()


def distro_full() -> str:
    if platform.system() in ["Linux", "Darwin"]:
        return f"{str(distro.id() + '-' + distro.version()).strip('-')}".lower()
        #  E.g. Arch has no version so it would look like: "arch-"
    else:
        return distro.id().lower()  # Windows msys already has a version


def gnat_version(cached : bool=True, crate : str=None):
    global gnat_version_cached

    if crate:  # Try to ascertain an overriding compiler in the solution
        try:
            gnat_override = re.search(
                "Dependencies \(solution\):.*?gnat(?:=|_[^=]*?=)(.+?)(\s|$).*?Dependencies \(graph\):",
                check_output(["alr", "-n", "--no-tty", "show", crate, "--solve"]).decode(),
                flags=re.MULTILINE+re.DOTALL
            ).group(1)
            print(f"   Crate uses specific GNAT version {gnat_override}")
            return gnat_override
        except KeyboardInterrupt:
            raise
        except:
            print(f"   Could not find a specific gnat version in {crate} solution")

    if cached and "gnat_version_cached" in globals():
        return gnat_version_cached

    # E.g. gnat_native 11.2.1 Default
    if "GNAT_EXTERNAL" in os.environ.keys():
        pattern = "gnat_external\s+(\S+)\s+Available"
    else:
        pattern = "gnat_\S+\s+(\S+)\s+Default"

    gnat_version_cached = re.search(pattern, check_output(["alr","toolchain"]).decode()).group(1)
    return gnat_version_cached


class Test:
    def __init__(self, crate : str, version : str, path : str=None):
        """
        Create a new test, or load its previous result if available from path
        """
        self.crate = crate
        self.version = version
        self.badge = False
        self.status = BUILD_UNTESTED
        self.duration = 0.0
        self.last_attempt = "never"
        self.creation_timestamp = time.time()
        self.log = ["no log available"]

        # Autodetect of reuse
        self.platform = osname()
        self.distro = distro_full()
        self.gnat = None if path else gnat_version(crate=crate)

        on_disk = False
        load_path = path if path else self.filename()
        if load_path:
            try:
                on_disk = self.load(load_path)
            except Exception as Ex:
                print(f"ERROR: loading from {load_path} failed, test will be reset ({Ex})")
                if os.path.isfile(load_path):
                    os.remove(load_path)

        if on_disk:
            reason = "given-path" if path else "built-path"
            # print(f"TEST at {self.filename()} was loaded because of {reason}")
        else:
            print(f"TEST at {self.filename()} was generated from scratch")
            if not self.gnat:
                self.gnat = gnat_version(crate=crate)
            self.write()

    def filename(self):
        return os.path.join(
            DB,
            self.crate[0:2], self.crate, self.version,
            self.platform, self.distro, f"gnat={self.gnat}",
            f"{self.crate}-{self.version}.yaml")

    def delete(self):
        if os.path.isfile(self.filename()):
            print(f"DELETING {self.filename()}")
            os.remove(self.filename())

    def ok(self) -> bool:
        return (self.status in BUILD_UNTESTED) or (self.status in BUILD_SUCCESS)

    def set_result(self, status, log, duration):
        self.duration = duration
        self.status = status
        self.log = log
        self.last_attempt = datetime.now(timezone.utc)
        self.gnat = gnat_version(crate=self.crate)
        self.badge = ("BADGE" in os.environ.keys() and str(os.environ["BADGE"]) == "1")

    def load(self, path : str):
        if os.path.isfile(path):
            with open(path) as file:
                data = yaml.load(file, Loader=yaml.FullLoader)
                for key in data.keys():
                    self.__dict__[key] = data[key]
            if "gnat_version" in vars(self).keys() and self.gnat_version and not self.gnat:
                self.gnat = self.gnat_version
                del self.__dict__["gnat_version"]
            return True
        else:
            return False

    def write(self):
        # This indicates this is a canonical test for badging.
        if self.badge:
            if self.status == "success":
                self.badge_color = "green"
            elif self.status == "failing":
                self.badge_color = "red"
            elif self.status == "missing-dependencies":
                self.badge_color = "yellow"
            else:
                self.badge_color = "inactive"

        if not os.path.isdir(os.path.dirname(self.filename())):
            os.makedirs(os.path.dirname(self.filename()))

        with open(self.filename(), "wt") as file:
            yaml.dump(vars(self), file)

        with open(self.filename() + ".log", "wt") as file:
            # Somehow None makes into the log in some case
            file.writelines([line for line in self.log if line])

    def nudge(self):
        if self.status == BUILD_UNTESTED:
            age = 0
        else:
            delta = datetime.now(timezone.utc) - self.last_attempt
            age = delta.total_seconds()

        week = 7*24*60*60
        return round(min(age/week, 10))

    def urgency(self):
        # If our compiler differs from the one in the environment, do not consider ourselves fit for test:
        # Crates requiring a cross-compiler will still be tested when it matches the version of the native
        # in environment.
        if self.gnat != gnat_version():
            return 0

        # Return a positive, proportional to the urgency to test this crate:
        if self.status == BUILD_UNTESTED:
            return 10000                 # we want to test it
        elif self.status == BUILD_STATUS["FAIL"]:
            return self.nudge() + 1      # failing, retest at lowest prio
        elif self.status == BUILD_STATUS["ERR"]:
            return self.nudge() + 100    # maybe alr was fixed, retry at some point
        else:
            return self.nudge() + 10     # maybe smthng in the environment changed, retry whenever



def identify_latest(crate):
    # Returns either a version or "unknown"
    try:
        output = check_output(["alr", "--no-tty", "show", crate]).decode()
        if "--external" in output:
            return "external"
        else:
            return re.search("=([^:]+):", #  E.g. hello=1.0.1: Hello world
                             output.split("\n")[0]).group(1)
    except KeyboardInterrupt:
        raise
    except:
        print("WARNING: version identification failure:")
        print(check_output(["alr", "--no-tty", "show", crate]).decode())
        return "unknown"


def index_head_file() -> str:
    return os.path.join("heads", f"{distro_full()}-{gnat_version()}")


def last_index_commit():
    heads = check_output(["git", "ls-remote", "https://github.com/alire-project/alire-index"]).decode()
    for line in heads.split("\n"):
        (commit, ref) = tuple(line.split('\t'))
        if ref == "HEAD":
            return commit
    return "unknown"

def last_local_index_commit():
    filename = index_head_file()
    if os.path.isfile(filename):
        with open(filename, "rt") as file:
            return file.readlines()[0].replace("\n", "")
    return "unknown"


def write_last_index_commit(commit : str=None):
    with open(index_head_file(), "wt") as file:
            file.write(f"{commit if commit else last_index_commit()}\n")


def new_index_commits():
    local_head = last_local_index_commit()
    remote_head = last_index_commit()
    print(f"HEADS: {local_head} vs {remote_head}")
    if local_head != remote_head:
        write_last_index_commit(remote_head)
        return True
    else:
        return False

def populate():
    print("POPULATING DB...")
    count = 0
    crates = []
    for line in check_output(["alr", "search", "--crates"]).decode().split("\n"):
        count += 1
        if count > DEBUG_MAX_CRATES:
            return crates

        crate = line.split(" ")[0]
        if crate != "":
            version = identify_latest(crate)
            print(f"POPULATING: {crate}={version}")

            if version == "unknown":
                print(f"INTERNAL ERROR: {crate}")
            elif version == "external":
                print(f"SKIPPED (external): {crate}")
            else:
                crates += [Test(crate, version)]
    return crates


def load(populate_if_empty : bool=True, all_platforms : bool=False, online : bool=True) -> List[Test]:
    # Load from a preexisting database

    def populate_or_empty(reason : str):
        if populate_if_empty:
            print(f"WARNING: defaulting to populate (reason: {reason})")
            return populate()
        else:
            print(f"WARNING: returning empty crate dict (reason: {reason})")
            return {}

    # Check if there are already crates in this configuration, using the aaa crate as telltale:
    if online and not os.path.isdir(join(DB, "aa", "aaa")):
        write_last_index_commit()
        return populate_or_empty("'aaa' crate not found")

    if online and new_index_commits():
        return populate_or_empty("New commits detected in default index branch")

    # Otherwise load
    print("LOADING EXISTING DB...")

    crates = []
    breaking = False
    for prefix in glob.iglob(join(DB, "*")):
        if breaking:
            break
        for path in glob.iglob(join(prefix, "*")):
            name = os.path.basename(path)
            tests = 0
            # Use only last known version for testing
            version = os.path.basename(glob.glob(join(path, "*"))[-1])
            for plat_path in glob.iglob(join(path, version, "*")):
                plat = os.path.basename(plat_path)
                if all_platforms or plat == osname():
                    for dist_path in glob.iglob(join(plat_path, "*")):
                        dist = os.path.basename(dist_path)
                        for gnat_path in glob.iglob(join(dist_path, "*")):
                            gnat = os.path.basename(gnat_path).split("=")[1]
                            assert os.path.isdir(gnat_path)
                            for final_path in glob.iglob(join(gnat_path, "*.yaml")):
                                crates += [Test(name, version, path=final_path)]
                                tests += 1

            print(f"Loaded {name} ({tests} tests)")
            if len(crates) > DEBUG_MAX_CRATES:
                breaking = True
                break

    pruned = 0
    kept = []
    for test in crates:
        if test.status == BUILD_UNTESTED and time.time() - test.creation_timestamp > PRUNE_AFTER_SECONDS:
            test.delete()
            pruned += 1
        else:
            kept += [test]

    crates = kept

    print(f"Loaded {len(crates)} releases and pruned {pruned} old unrun tests")
    return crates