"""Infrastructure readiness only, never a product acceptance claim."""
import os
import subprocess
import time
import uuid


def main():
    os.environ["FIRESTORE_EMULATOR_HOST"] = "127.0.0.1:18980"
    from google.cloud import firestore
    client = firestore.Client(project="demo-proofline-pilot")
    reference = client.collection("verifier-infrastructure").document(uuid.uuid4().hex)
    transaction = client.transaction(max_attempts=3)

    @firestore.transactional
    def update(tx):
        old = reference.get(transaction=tx)
        assert not old.exists
        tx.set(reference, {"synthetic": True, "probe": 1})

    update(transaction)
    assert reference.get().to_dict() == {"synthetic": True, "probe": 1}
    reference.delete()
    print("Emulator SDK transaction/read/delete: PASS")
    env = dict(os.environ, DOCKER_HOST="unix:///Users/shivamgupta/.colima/default/docker.sock",
               DOCKER_CONFIG="/tmp/proofline-public-docker-config")
    command = ["/opt/homebrew/bin/docker", "run", "--rm", "--network=none", "--cpus=2", "--memory=2g",
               "-v", os.getcwd() + ":/candidate:ro", "python:3.12-slim", "python", "-c",
               "import pathlib,sys; assert sys.version_info[:2]==(3,12); "
               "assert pathlib.Path('/candidate/evidence/product/verification/coverage.md').is_file(); "
               "print('Python3.12 offline 2CPU/2GiB container and mount: PASS')"]
    began = time.monotonic()
    result = subprocess.run(command, env=env)
    print("Container exit:", result.returncode, "duration_seconds:", round(time.monotonic()-began, 6))
    assert result.returncode == 0


if __name__ == "__main__":
    main()
