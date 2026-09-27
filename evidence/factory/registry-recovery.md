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
