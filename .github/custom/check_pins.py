#!/usr/bin/env python3
"""Check that the fork's build pins match what the upstream source expects.

Run from the root of an upstream checkout, with this fork checked out at .ci/:

    python3 .ci/.github/custom/check_pins.py

The fork's windows-custom.yml and bridge-custom.yml are copies of upstream build steps with
hard-coded tool versions. If upstream bumps one of them, building with the old pin fails
somewhere deep in a 40-minute job, so compare them up front and fail fast instead.

On success, appends `version=` (from Cargo.toml) and `vcpkg=` (VCPKG_COMMIT_ID) to
$GITHUB_OUTPUT when it is set.
"""
import os
import pathlib
import re
import sys

FORK = pathlib.Path(".ci/.github/workflows")
SRC = pathlib.Path(".github/workflows")

# (upstream file, fork file, key). Values are the first `KEY: value` line in each file.
PINS = [
    ("flutter-build.yml", "windows-custom.yml", "FLUTTER_VERSION"),
    ("flutter-build.yml", "windows-custom.yml", "LLVM_VERSION"),
    ("flutter-build.yml", "windows-custom.yml", "SCITER_RUST_VERSION"),
    ("bridge.yml", "bridge-custom.yml", "CARGO_EXPAND_VERSION"),
    ("bridge.yml", "bridge-custom.yml", "FLUTTER_RUST_BRIDGE_VERSION"),
    ("bridge.yml", "bridge-custom.yml", "RUST_VERSION"),
    # The bridge for the Flutter 3.24 builds is generated with this Flutter version.
    ("bridge.yml", "bridge-custom.yml", "flutter-version"),
]


def read_pin(path: pathlib.Path, key: str) -> str:
    if not path.exists():
        sys.exit(f"FAIL: {path} not found")
    m = re.search(rf'^\s*{re.escape(key)}:\s*"?([^"\s,#]+)"?', path.read_text(), re.M)
    if not m:
        sys.exit(f"FAIL: no {key} in {path}")
    return m.group(1)


def main() -> None:
    mismatches = []
    for src_file, fork_file, key in PINS:
        want = read_pin(SRC / src_file, key)
        have = read_pin(FORK / fork_file, key)
        status = "ok" if want == have else "MISMATCH"
        print(f"{status:8} {key}: upstream {src_file}={want}, fork {fork_file}={have}")
        if want != have:
            mismatches.append(key)

    vcpkg = read_pin(SRC / "flutter-build.yml", "VCPKG_COMMIT_ID")
    # Cargo.toml uses `version = "x"`, not `version: x`.
    m =re.search(r'^version = "(.*)"', pathlib.Path("Cargo.toml").read_text(), re.M)
    if not m:
        sys.exit("FAIL: no version in Cargo.toml")
    version = m.group(1)
    print(f"vcpkg={vcpkg} version={version}")

    if mismatches:
        sys.exit(
            "FAIL: fork pins are out of date for this ref: "
            + ", ".join(mismatches)
            + ". Update windows-custom.yml / bridge-custom.yml (and re-check their steps"
            " against upstream flutter-build.yml / bridge.yml)."
        )

    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a") as f:
            f.write(f"vcpkg={vcpkg}\nversion={version}\n")


if __name__ == "__main__":
    main()
