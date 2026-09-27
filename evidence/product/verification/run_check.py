"""Record a check without hiding failed output. Never pass secrets in arguments.

Usage: python run_check.py LABEL -- command args...
Run from immutable candidate root. Output is persisted verbatim, so test drivers
must not print credentials, private snapshots or response cookies.
"""
import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time


def main():
    label, *command = sys.argv[1:]
    if command[:1] == ["--"]:
        command.pop(0)
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", label) or not command:
        raise SystemExit("Need safe label and command")
    directory = Path(os.environ.get("VERIFICATION_OUTPUT", Path(__file__).parent / "runs"))
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    prefix = directory / (stamp + "-" + label)
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    status = subprocess.check_output(["git", "status", "--porcelain"], text=True)
    started = time.monotonic()
    with prefix.with_suffix(".log").open("x") as output:
        process = subprocess.run(command, stdout=output, stderr=subprocess.STDOUT)
    result = {
        "label": label, "started_utc": stamp, "command": command,
        "cwd": os.getcwd(), "source_revision": revision,
        "working_tree_status": status, "exit_status": process.returncode,
        "duration_seconds": round(time.monotonic() - started, 6),
        "log": prefix.with_suffix(".log").name,
    }
    prefix.with_suffix(".json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    raise SystemExit(process.returncode)


if __name__ == "__main__":
    main()
