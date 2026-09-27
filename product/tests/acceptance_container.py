"""Real offline container/volume acceptance, synthetic data only.

Host: python acceptance_container.py host IMAGE
The host Docker context must select the intended local engine.
"""
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import time
import uuid


def inside(phase):
    import requests
    client = requests.Session()
    origin = 'http://localhost:8080'
    saved_path = Path('/data/verifier-receipts.json')
    csrf = None
    def call(method, path, body=None, key=None, expected=200):
        headers = {'Origin': origin}
        if csrf:
            headers['X-CSRF-Token'] = csrf
        if key:
            headers['Idempotency-Key'] = key
        response = client.request(method, origin + path, json=body, headers=headers, timeout=10)
        assert response.status_code == expected, f'{method} {path} expected {expected} got {response.status_code}'
        assert 'private' in response.headers.get('Cache-Control', '') and 'no-store' in response.headers.get('Cache-Control', '')
        return response.json()
    for attempt in range(80):
        try:
            if client.get(origin + '/health/ready', timeout=.3).status_code == 200:
                break
        except requests.RequestException:
            pass
        time.sleep(.1)
    else:
        raise AssertionError('container readiness timeout')
    if phase == 'seed':
        csrf = call('GET', '/api/session')['csrf_token']
        venue = {'name': 'Synthetic Container Hearth', 'timezone': 'Etc/UTC', 'slot_minutes': 30,
                 'reservation_duration_minutes': 60, 'cancellation_cutoff_minutes': 0,
                 'opening_hours': [{'weekday': day, 'opens': '00:00', 'closes': '23:59'} for day in 'mon tue wed thu fri sat sun'.split()],
                 'tables': [{'id': f'table_{i}', 'label': f'Synthetic {i}', 'capacity': 4} for i in range(1, 4)],
                 'combinable': [['table_1', 'table_2']]}
        setup = {'setup_secret': os.environ['TABLEKEEPER_SETUP_SECRET'],
                 'owner': {'email': 'container@acceptance.test', 'password': 'synthetic-container-passphrase', 'display_name': 'Synthetic Owner'},
                 'restaurant': venue}
        csrf = call('POST', '/api/setup', setup, expected=201)['csrf_token']
        rid = call('GET', '/restaurants')['restaurants'][0]['id']
        receipts = []
        def remember(path, body, key):
            result = call('POST', path, body, key, 201)
            receipts.append({'path': path, 'body': body, 'key': key, 'result': result})
            return result
        booking = remember('/reservations', {'restaurant_id': rid, 'table_id': 'table_1', 'starts_at_local': '2032-06-17T18:00', 'party_size': 2}, 'container-booking')
        policy = {key: venue[key] for key in ('slot_minutes', 'reservation_duration_minutes', 'cancellation_cutoff_minutes', 'opening_hours')}
        policy.update(effective_from='2032-01-01', capacities={f'table_{i}': 4 for i in range(1,4)})
        remember('/restaurants/' + rid + '/policies', policy, 'container-policy')
        series = remember('/series', {'anchor_reference': booking['reference'], 'count': 3, 'interval_weeks': 1}, 'container-series')
        remember('/series/' + series['series_id'] + '/amend', {'expected_revision': series['revision'], 'from_index': 0, 'local_time': '20:00'}, 'container-amend')
        preview = remember('/restaurants/' + rid + '/replans', {'table_id': 'table_1', 'from': '2032-06-17T18:00:00+00:00', 'to': '2032-06-17T23:00:00+00:00'}, 'container-preview')
        remember('/restaurants/' + rid + '/replans/' + preview['plan_id'] + '/apply', {}, 'container-apply')
        paths = ['/reservations/' + booking['reference'], '/reservations/' + booking['reference'] + '/history',
                 '/series/' + series['series_id'], '/restaurants/' + rid + '/policies']
        snapshots = {path: call('GET', path) for path in paths}
        saved = {'cookie': requests.utils.dict_from_cookiejar(client.cookies), 'csrf': csrf, 'receipts': receipts, 'snapshots': snapshots}
        descriptor = os.open(saved_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, 'w') as stream:
            json.dump(saved, stream)
        print('Seed setup/booking/policy/series adoption+amendment/closure apply: PASS')
    elif phase == 'verify':
        saved = json.loads(saved_path.read_text())
        client.cookies.update(saved['cookie'])
        csrf = saved['csrf']
        for receipt in saved['receipts']:
            assert call('POST', receipt['path'], receipt['body'], receipt['key']) == receipt['result']
        for path, expected in saved['snapshots'].items():
            assert call('GET', path) == expected
        print('Original receipts, identities, current series, policy and history after restart/restore: PASS')
    elif phase == 'proxy':
        response = client.post(origin + '/auth/login', data=b'x' * 65537, timeout=10)
        assert response.status_code == 413
        assert 'private' in response.headers.get('Cache-Control', '') and 'no-store' in response.headers.get('Cache-Control', '')
        assert response.headers.get('X-Content-Type-Options') == 'nosniff'
        response = client.get(origin + '/health', headers={'X-Large': 'x' * 20000}, timeout=10)
        assert response.status_code in (400, 431)
        assert 'private' in response.headers.get('Cache-Control', '') and 'no-store' in response.headers.get('Cache-Control', '')
        assert os.getuid() == 65534
        print('Non-root container and proxy oversized body/header private no-store errors: PASS')
    elif phase == 'slow':
        import socket
        import select
        saved = json.loads(saved_path.read_text())
        client.cookies.update(saved['cookie'])
        csrf = saved['csrf']
        sockets = []
        try:
            for _ in range(4):
                connection = socket.create_connection(('127.0.0.1', 8080), timeout=2)
                connection.sendall(b'POST /auth/login HTTP/1.1\r\nHost: localhost\r\nContent-Length: 10000\r\nContent-Type: application/json\r\n\r\n{')
                sockets.append(connection)
            for _ in range(4):
                connection = socket.create_connection(('127.0.0.1', 8080), timeout=2)
                connection.sendall(b'POST /auth/login HTTP/1.1\r\nHost: localhost\r\nX-Slow: ')
                sockets.append(connection)
            began = time.monotonic()
            body = dict(saved['receipts'][0]['body'], table_id='table_3', starts_at_local='2032-06-18T19:00')
            booking_start = time.monotonic()
            call('POST', '/reservations', body, 'healthy-under-trickle', 201)
            booking_duration = time.monotonic() - booking_start
            alive = list(sockets)
            for _ in range(6):
                time.sleep(4)
                for connection in list(alive):
                    if select.select([connection], [], [], 0)[0]:
                        connection.recv(65536)
                        alive.remove(connection)
                    else:
                        try:
                            connection.sendall(b' ')
                        except OSError:
                            alive.remove(connection)
            elapsed = time.monotonic() - began
            print(json.dumps({'trickling_clients': len(sockets), 'body_clients':4, 'header_clients':4, 'still_open_after_seconds': round(elapsed, 3),
                              'still_open_count': len(alive), 'healthy_booking_seconds': round(booking_duration, 3)}), flush=True)
            assert booking_duration < 5
            assert not alive, 'proxy accepted body trickles beyond documented backend total connection deadline'
        finally:
            for connection in sockets:
                connection.close()
    elif phase == 'proxy-error':
        import signal
        backend = next(int(path.parent.name) for path in Path('/proc').glob('[0-9]*/cmdline')
                       if b'tablekeeper.server' in path.read_bytes().split(b'\0'))
        os.kill(backend,signal.SIGSTOP)
        try:
            response=client.get(origin+'/health/ready',timeout=25)
            assert response.status_code == 504
            assert 'private' in response.headers.get('Cache-Control','') and 'no-store' in response.headers.get('Cache-Control','')
            assert response.headers.get('X-Content-Type-Options') == 'nosniff'
            print('Proxy-generated504 carries private,no-store and nosniff: PASS')
        finally:
            os.kill(backend,signal.SIGCONT)


def host(image, limited=None):
    docker = os.environ.get('ACCEPTANCE_DOCKER', '/opt/homebrew/bin/docker')
    suffix = uuid.uuid4().hex[:10]
    name, target = 'verifier-' + suffix, 'verifier-restore-' + suffix
    volume, restored = name + '-data', target + '-data'
    env = dict(os.environ, TABLEKEEPER_SETUP_SECRET=secrets.token_urlsafe(32))
    def run(*args, check=True):
        result = subprocess.run([docker, *args], env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if result.returncode and check:
            print(result.stdout)
            raise AssertionError(f'Docker command {args[0]} failed with {result.returncode}')
        return result.stdout.strip()
    def launch(container, data):
        run('run', '-d', '--name', container, '--network=none', '--cpus=2', '--memory=2g', '-v', data + ':/data',
            '-e', 'TABLEKEEPER_MODE=development', '-e', 'TABLEKEEPER_PUBLIC_ORIGIN=http://localhost:8080',
            '-e', 'TABLEKEEPER_SETUP_SECRET', image)
        run('cp', str(Path(__file__).resolve()), container + ':/tmp/acceptance_container.py')
    def phase(container, action):
        print(run('exec', container, 'python', '/tmp/acceptance_container.py', action))
    try:
        run('volume', 'create', volume)
        launch(name, volume)
        phase(name, 'seed')
        if limited:
            phase(name, limited)
            return
        phase(name, 'proxy')
        run('restart', name)
        phase(name, 'verify')
        print(run('exec', name, 'python', '-m', 'tablekeeper.operations', 'backup', '/data/verifier-backup.json'))
        run('volume', 'create', restored)
        common = ['run', '--rm', '--network=none', '-v', restored + ':/data', '-v', volume + ':/source:ro', image,
                  'python', '-m', 'tablekeeper.operations']
        result = json.loads(run(*common, 'maintenance', 'on'))
        print(run(*common, 'restore', '/source/verifier-backup.json', '--expected-revision', str(result['revision'])))
        run(*common, 'maintenance', 'off')
        run('run', '--rm', '--network=none', '-v', restored + ':/data', '-v', volume + ':/source:ro', image,
            'python', '-c', 'import shutil; shutil.copyfile("/source/verifier-receipts.json","/data/verifier-receipts.json")')
        launch(target, restored)
        phase(target, 'verify')
        print('Image identity:', run('image', 'inspect', image, '--format', '{{.Id}}'))
        print('Container restrictions:', run('inspect', name, '--format', '{{.HostConfig.NetworkMode}} {{.HostConfig.NanoCpus}} {{.HostConfig.Memory}} {{.Config.User}}'))
    finally:
        run('rm', '-f', name, target, check=False)
        run('volume', 'rm', volume, restored, check=False)


if __name__ == '__main__':
    if sys.argv[1] in ('host', 'host-slow','host-proxy-error'):
        host(sys.argv[2], {'host-slow':'slow','host-proxy-error':'proxy-error'}.get(sys.argv[1]))
    else:
        inside(sys.argv[1])
