#!/usr/bin/env python3
"""Point a RustDesk checkout at Dave's self-hosted server.

Applied by .github/workflows/windows-custom.yml right after checkout, before building.
Fails loudly if upstream ever moves or renames any of the anchors below.
"""
import pathlib
import sys

HOST = "remote.davepinto.dev"
KEY = "PacuDs55dwuqUWY2NBrT2Jv46yI27dm0oaQKGhCMqBQ="

CFG = pathlib.Path("libs/hbb_common/src/config.rs")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        sys.exit(f"FAIL: expected exactly 1 occurrence of {label}, found {count}")
    return text.replace(old, new)


def main() -> None:
    if not CFG.exists():
        sys.exit(f"FAIL: {CFG} not found — did the submodule checkout run?")

    text = CFG.read_text()

    text = replace_once(
        text,
        'pub const RENDEZVOUS_SERVERS: &[&str] = &["rs-ny.rustdesk.com"];',
        f'pub const RENDEZVOUS_SERVERS: &[&str] = &["{HOST}"];',
        "RENDEZVOUS_SERVERS",
    )
    text = replace_once(
        text,
        'pub const RS_PUB_KEY: &str = "OeVuKk5nlHiXp+APNn0Y3pC1Iwpwn44JGqrQCsWqmBw=";',
        f'pub const RS_PUB_KEY: &str = "{KEY}";',
        "RS_PUB_KEY",
    )
    # Make the self-update check opt-in instead of opt-out. Otherwise the client offers
    # (and, if accepted, installs) the official build, which would revert the baked-in
    # server settings for anyone who never saved them explicitly. Updates ship from the
    # download page instead.
    text = replace_once(
        text,
        'pub fn option2bool(option: &str, value: &str) -> bool {\n    if option.starts_with("enable-") {',
        'pub fn option2bool(option: &str, value: &str) -> bool {\n'
        '    if option == "enable-check-update" {\n'
        '        return value == "Y";\n'
        '    }\n'
        '    if option.starts_with("enable-") {',
        "option2bool update-check default",
    )

    CFG.write_text(text)
    print(f"patched {CFG}: host={HOST}, key={KEY[:12]}…, update-check opt-in")


if __name__ == "__main__":
    main()
