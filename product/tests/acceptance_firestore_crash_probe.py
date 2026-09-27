"""Diagnostic of actual emulator lock release after precommit process death."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import uuid

from tablekeeper.storage import FirestoreStore


def main():
    assert os.environ.get('FIRESTORE_EMULATOR_HOST'), 'Only emulator permitted'
    collection = 'verifier_' + uuid.uuid4().hex
    store = FirestoreStore('demo-proofline-pilot', collection=collection)
    store.transact('main', lambda c: None, create=True)
    with tempfile.TemporaryDirectory() as directory:
        marker = Path(directory) / 'arm'
        marker.touch()
        env = dict(os.environ, TABLEKEEPER_MODE='development', TABLEKEEPER_FAULT='before_commit', TABLEKEEPER_FAULT_ARM_FILE=str(marker))
        code = 'from tablekeeper.storage import FirestoreStore; import sys; s=FirestoreStore("demo-proofline-pilot",collection=sys.argv[1]); s.transact("main",lambda c:c.update(acceptance_counter=1))'
        result = subprocess.run([sys.executable,'-c',code,collection],env=env,timeout=20)
        assert result.returncode == 86
        print('Process terminated before commit; starting one recovery transaction',flush=True)
        began = time.monotonic()
        # Run recovery in a bounded process so a blocked SDK cannot hide duration.
        result = subprocess.run([sys.executable,'-c',code,collection],timeout=120)
        elapsed = time.monotonic()-began
        print('Recovery exit',result.returncode,'elapsed_seconds',round(elapsed,6),flush=True)
        assert result.returncode == 0
        revision,value = store.snapshot('main')
        assert revision == 2 and value['acceptance_counter'] == 1
    store.close()


if __name__ == '__main__':
    main()
