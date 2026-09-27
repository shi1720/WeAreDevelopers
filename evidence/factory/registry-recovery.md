# Registry recovery, 2026-09-27

Engineer reported two failed Docker builds resolving `python:3.12-slim`, with TCP/443 timeouts to distinct Docker Hub addresses. The core candidate remained unaccepted; local unit results were not substituted for container evidence.

Coordinator checks found host HTTPS could reach Docker Hub and AWS Public ECR (the expected HTTP 401 registry authentication challenges). A direct Colima pull of `public.ecr.aws/docker/library/python:3.12-slim` also failed with a TCP timeout. The default Docker client configuration referenced a missing `docker-credential-desktop`; a separate temporary empty Docker configuration was used for public pulls without modifying existing credentials or daemon settings.

Recovery used the host network to fetch the official image, then loaded it into Colima:

```sh
brew install crane
DOCKER_CONFIG=/tmp/proofline-public-docker-config crane pull \
  --platform linux/arm64 python:3.12-slim /tmp/proofline-python-3.12-slim.tar
DOCKER_CONFIG=/tmp/proofline-public-docker-config \
  DOCKER_HOST=unix:///Users/shivamgupta/.colima/default/docker.sock \
  docker load -i /tmp/proofline-python-3.12-slim.tar
```

All three recovery commands exited 0. Docker reported `Loaded image: python:3.12-slim`. Image inspection returned `sha256:cf9ba7e57be0cf2c23fc6f44e9cae07f6cf26b600272de21b7b269bc76217e67`. No service source, Dockerfile or official harness was changed by this recovery. The image archive is outside the repository and contains only the public base image. Exact total duration was not instrumented; tool execution timestamps are retained in the room. Container builds and isolated acceptance remain separate subsequent checks.

## Official runner dependencies

Verifier then observed a timeout reaching PyPI from a fresh Python container while the official isolated runner build installed its dependencies. Coordinator started a temporary local HTTP CONNECT/forward proxy bound to host `127.0.0.1:18791`, reachable from Colima at `192.168.5.2:18791`. Colima curl through this proxy reached PyPI with HTTP 200, exit 0. The official runner was built without editing its Dockerfile or requirements:

```sh
DOCKER_CONFIG=/tmp/proofline-public-docker-config \
DOCKER_HOST=unix:///Users/shivamgupta/.colima/default/docker.sock \
docker build \
  --build-arg HTTP_PROXY=http://192.168.5.2:18791 \
  --build-arg HTTPS_PROXY=http://192.168.5.2:18791 \
  --build-arg http_proxy=http://192.168.5.2:18791 \
  --build-arg https_proxy=http://192.168.5.2:18791 \
  -t df-harness-runner \
  -f /tmp/proofline-official-spec/harness/Dockerfile \
  /tmp/proofline-official-spec/harness
```

Exit 0; image `sha256:eca1c0912c3e4ac738a5b198f4a384bd9d83ffe7bb62f366d63072f7d89dc8bc`. Playwright's first Chromium transfer timed out after 30 seconds; its own retry succeeded. Pip, Debian dependencies, Chromium and headless shell installed normally. Inspection confirmed no proxy variables in the resulting image's runtime environment. Official checkout `git status --short` was empty. The temporary proxy was stopped before independent isolated verification resumed. No runtime networking exception was introduced. The exact total build duration was not instrumented; it is not reported as a measured benchmark.

The normal legacy Docker build then missed the recovered RUN cache because the build-argument invocation has a different cache signature. Attempt 02 was retained by Verifier. Coordinator restarted the temporary host proxy and supplied `/tmp/proofline-docker-build-tools/docker`, a transparent adapter used only through a task-local PATH. It adds the four proxy build arguments above only when the first Docker argument is `build`, then executes `/opt/homebrew/bin/docker`; every non-build invocation is forwarded unchanged. A normal-form runner build through this adapter exited 0, reused the recovered RUN layer and produced the same image ID. Verifier was directed to inspect the adapter and verify proxy-free runtime environment and the internal network. No test expectation, official source or service file was changed. Subsequent reproducibility commands on this affected Colima installation must use this build-only PATH adapter until its direct outbound connectivity is repaired.
