"""Container supervisor: bounded ingress proxy and one Python process."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def main():
    port = int(os.environ.get('PORT', '8080'))
    if not 1 <= port <= 65535 or port == 8081:
        raise ValueError('PORT must be valid and distinct from internal port 8081')
    config = Path('/app/deploy/nginx.conf.template').read_text().replace('__PORT__', str(port))
    Path('/tmp/tablekeeper-nginx.conf').write_text(config)
    backend = subprocess.Popen([sys.executable, '-m', 'tablekeeper.server'], env=dict(os.environ, PORT='8081', TABLEKEEPER_BIND='127.0.0.1'))
    proxy = subprocess.Popen(['nginx', '-c', '/tmp/tablekeeper-nginx.conf', '-g', 'daemon off;'])
    def shutdown(*_):
        for process in (proxy, backend):
            if process.poll() is None:
                process.terminate()
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    try:
        while backend.poll() is None and proxy.poll() is None:
            time.sleep(0.2)
    finally:
        shutdown()
        for process in (proxy, backend):
            try:
                process.wait(timeout=25)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
    return backend.returncode or proxy.returncode or 0


if __name__ == '__main__':
    sys.exit(main())
