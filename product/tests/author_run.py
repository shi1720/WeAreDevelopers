"""Record author checks, distinct from independently executed acceptance."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


def main():
    root = Path(__file__).resolve().parents[2]
    directory = root / 'evidence/product/engineering'
    directory.mkdir(parents=True, exist_ok=True)
    command = sys.argv[1:]
    if not command:
        raise SystemExit('Supply exact command arguments')
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True, cwd=root).strip()
    status = subprocess.check_output(['git', 'status', '--porcelain'], text=True, cwd=root)
    diff = subprocess.check_output(['git', 'diff', 'HEAD'], cwd=root)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    start = time.monotonic()
    result = subprocess.run(command, cwd=root, capture_output=True, text=True)
    elapsed = time.monotonic() - start
    log = directory / (stamp + '.log')
    log.write_text(result.stdout + result.stderr)
    record = {'command': command, 'cwd': str(root), 'revision': revision, 'status_at_start': status.splitlines(),
              'tracked_diff_sha256': hashlib.sha256(diff).hexdigest(), 'started_at': stamp,
              'duration_seconds': elapsed, 'exit_status': result.returncode, 'log': log.name,
              'independent_acceptance': False}
    (directory / (stamp + '.json')).write_text(json.dumps(record, indent=2) + '\n')
    print(result.stdout + result.stderr, end='')
    print(json.dumps(record, indent=2))
    return result.returncode


if __name__ == '__main__':
    sys.exit(main())
