"""Record exact source context and measured output for an experience check."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/product/experience'


def main():
    command = sys.argv[1:]
    if not command:
        raise SystemExit('Pass the exact check command as arguments')
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    dirty = subprocess.check_output(['git', 'status', '--porcelain=v1'], cwd=ROOT, text=True)
    diff = subprocess.check_output(['git', 'diff', 'HEAD'], cwd=ROOT)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    started = time.monotonic()
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    elapsed = time.monotonic() - started
    log = EVIDENCE / f'{stamp}.log'
    log.write_text(result.stdout + result.stderr)
    record = {'command': command, 'cwd': str(ROOT), 'head_at_start': revision,
              'dirty_status_at_start': dirty.splitlines(),
              'tracked_diff_sha256': hashlib.sha256(diff).hexdigest(),
              'started_at_utc': stamp, 'duration_seconds': elapsed,
              'exit_status': result.returncode, 'output': log.name,
              'immutable_acceptance': not bool(dirty)}
    (EVIDENCE / f'{stamp}.json').write_text(json.dumps(record, indent=2) + '\n')
    print(result.stdout + result.stderr, end='')
    print(json.dumps(record, indent=2))
    raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
