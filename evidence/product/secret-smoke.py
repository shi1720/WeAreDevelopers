"""Coordinator release check of the documented private bind-file recipe."""
import json
import os
from pathlib import Path
import secrets
import subprocess
import tempfile
import time

root = Path(__file__).resolve().parents[2]
started = time.monotonic()
env = dict(os.environ, DOCKER_HOST='unix:///Users/shivamgupta/.colima/default/docker.sock', DOCKER_CONFIG='/tmp/proofline-public-docker-config')
docker = '/opt/homebrew/bin/docker'
name = 'tablekeeper-secret-review-' + secrets.token_hex(4)
image = 'sha256:ad581e03b6a305dd34f6f08149f6fc5e7fe6cf768f7d45108bcbd951ee754c79'
commands = []
def run(*args):
    command = [docker, *args]
    commands.append(command)
    return subprocess.run(command, env=env, text=True, capture_output=True, timeout=30)

result = {'source_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(), 'image': image}
with tempfile.TemporaryDirectory(prefix='tablekeeper-secret-review-', dir=Path.home()/'.cache') as directory:
    secret = Path(directory)/'setup-secret'
    descriptor = os.open(secret, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'w') as output:
        output.write(secrets.token_urlsafe(32))
    result['secret_mode'] = oct(secret.stat().st_mode & 0o777)
    result['host_file_uid'] = secret.stat().st_uid
    try:
        created = run('run', '-d', '--name', name, '--network', 'none', '--cpus', '2', '--memory', '2g',
            '-v', name+':/data', '-v', str(secret)+':/run/setup-secret:ro',
            '-e', 'TABLEKEEPER_MODE=development', '-e', 'TABLEKEEPER_PUBLIC_ORIGIN=http://localhost:8080',
            '-e', 'TABLEKEEPER_SETUP_SECRET_FILE=/run/setup-secret', image)
        result['docker_run_exit'] = created.returncode
        time.sleep(2)
        state = run('inspect', '--format', '{{json .State}}', name)
        result['container_state'] = json.loads(state.stdout) if state.returncode == 0 else {'inspect_failed': True}
        if result['container_state'].get('Running'):
            probe = run('exec', name, 'python', '-c', "import urllib.request; print(urllib.request.urlopen('http://localhost:8080/health/ready').status)")
            result['readiness_exit'] = probe.returncode
            result['readiness_status'] = probe.stdout.strip()
            setup_code = """import http.cookiejar,json,pathlib,urllib.request
origin='http://localhost:8080'
client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
session=json.load(client.open(origin+'/api/session'))
body={'setup_secret':pathlib.Path('/run/setup-secret').read_text(),'owner':{'email':'owner@secret-review.test','password':'synthetic private evening','display_name':'Synthetic Owner'},'restaurant':{'name':'Synthetic Secret Review','timezone':'Etc/UTC','slot_minutes':30,'reservation_duration_minutes':60,'cancellation_cutoff_minutes':0,'opening_hours':[{'weekday':'mon','opens':'17:00','closes':'23:00'}],'tables':[{'id':'window','label':'Window','capacity':2}],'combinable':[]}}
request=urllib.request.Request(origin+'/api/setup',data=json.dumps(body).encode(),headers={'Content-Type':'application/json','Origin':origin,'X-CSRF-Token':session['csrf_token']},method='POST')
response=client.open(request)
assert response.status==201 and json.load(response)['authenticated'] is True
print(response.status)
"""
            setup = run('exec', name, 'python', '-c', setup_code)
            result['setup_exit'] = setup.returncode
            result['setup_status'] = setup.stdout.strip()
        else:
            log = run('logs', name)
            result['failure_log'] = log.stdout + log.stderr
    finally:
        run('rm', '-f', name)
        run('volume', 'rm', name)
result['commands'] = commands
result['duration_seconds'] = time.monotonic()-started
result['recipe_passed'] = result.get('readiness_exit') == 0 and result.get('readiness_status') == '200' and result.get('setup_exit') == 0 and result.get('setup_status') == '201'
(root/'evidence/product/secret-smoke-setup.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps({'recipe_passed': result['recipe_passed'], 'host_file_uid': result['host_file_uid'], 'duration_seconds': result['duration_seconds'], 'evidence': 'evidence/product/secret-smoke-setup.json'}))
